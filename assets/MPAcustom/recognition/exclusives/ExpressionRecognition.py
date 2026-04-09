import ast
from collections.abc import Iterable
import json
import re
from typing import Any

from maa.custom_recognition import CustomRecognition
from maa.define import OCRResult


PLACEHOLDER_PATTERN = re.compile(r"\{([^{}]+)\}")
NUMBER_PATTERN = re.compile(r"[-+]?\d+(?:\.\d+)?")


class NodeResolutionError(ValueError):

    def __init__(self, message: str, payload: dict[str, Any]):
        super().__init__(message)
        self.payload = payload


class ExpressionRecognition(CustomRecognition):

    def analyze(
        self,
        context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult | None:
        params = self._parse_params(argv.custom_recognition_param)
        expression = params.get("expression")
        if not isinstance(expression, str) or not expression.strip():
            return CustomRecognition.AnalyzeResult(box=None, detail={"status": "invalid expression"})

        image = argv.image
        values_cache: dict[str, int | float] = {}
        placeholder_mapping: dict[str, str] = {}
        node_results: dict[str, Any] = {}

        def replace_placeholder(match: re.Match[str]) -> str:
            node_name = match.group(1).strip()
            if not node_name:
                raise ValueError("empty placeholder")

            variable_name = placeholder_mapping.get(node_name)
            if variable_name is None:
                variable_name = f"_value_{len(placeholder_mapping)}"
                placeholder_mapping[node_name] = variable_name
                try:
                    value, node_result = self._resolve_node_value(context, image, node_name)
                except NodeResolutionError as exc:
                    node_results[node_name] = exc.payload
                    raise

                values_cache[variable_name] = value
                node_results[node_name] = node_result
            return variable_name

        try:
            python_expression = PLACEHOLDER_PATTERN.sub(replace_placeholder, expression)
            python_expression = self._normalize_expression(python_expression)
            parsed = ast.parse(python_expression, mode="eval")
            self._validate_ast(parsed, set(values_cache.keys()))
            result = eval(
                compile(parsed, "<ExpressionRecognition>", "eval"),
                {"__builtins__": {}},
                values_cache,
            )
        except (ValueError, SyntaxError, TypeError, ZeroDivisionError) as exc:
            return CustomRecognition.AnalyzeResult(
                box=None,
                detail={
                    "status": "invalid expression",
                    "reason": str(exc),
                    "expression": expression,
                    "resolved_expression": locals().get("python_expression", expression),
                    "resolved_values": values_cache,
                    "node_results": node_results,
                },
            )

        if type(result) is not bool:
            return CustomRecognition.AnalyzeResult(
                box=None,
                detail={
                    "status": "expression did not evaluate to boolean",
                    "expression": expression,
                    "resolved_expression": python_expression,
                    "resolved_values": values_cache,
                    "node_results": node_results,
                },
            )

        if not result:
            return CustomRecognition.AnalyzeResult(
                box=None,
                detail={
                    "status": "expression evaluated to false",
                    "expression": expression,
                    "resolved_expression": python_expression,
                    "resolved_values": values_cache,
                    "node_results": node_results,
                },
            )

        return CustomRecognition.AnalyzeResult(
            box=(0, 0, 100, 100),
            detail={
                "status": "success",
                "expression": expression,
                "resolved_expression": python_expression,
                "resolved_values": values_cache,
                "node_results": node_results,
            },
        )

    def _parse_params(self, raw_params: Any) -> dict[str, Any]:
        if isinstance(raw_params, dict):
            return raw_params
        if isinstance(raw_params, str):
            try:
                parsed = json.loads(raw_params)
            except json.JSONDecodeError:
                return {}
            if isinstance(parsed, dict):
                return parsed
        return {}

    def _resolve_node_value(self, context, image, node_name: str) -> tuple[int | float, dict[str, Any]]:
        node_data = context.get_node_data(node_name) or {}
        box_index = self._get_box_index(node_data)
        recognition = context.run_recognition(node_name, image)
        payload = {
            "node_data": self._to_jsonable(node_data),
            "box_index": box_index,
            "recognition": self._to_jsonable(recognition),
        }
        if not (recognition and recognition.hit):
            raise NodeResolutionError(f"node {node_name} has no OCR result", payload)

        text = self._extract_text(recognition, box_index=box_index)
        payload["extracted_text"] = text
        if text is None:
            raise NodeResolutionError(f"node {node_name} has no OCR text", payload)

        match = NUMBER_PATTERN.search(text)
        if match is None:
            raise NodeResolutionError(f"node {node_name} has no numeric OCR text", payload)

        number_text = match.group(0)
        if "." in number_text:
            value = float(number_text)
        else:
            value = int(number_text)

        payload["value"] = value
        return value, payload

    def _get_box_index(self, node_data: Any) -> int | None:
        if not isinstance(node_data, dict):
            return None

        recognition = node_data.get("recognition")
        if not isinstance(recognition, dict):
            return None

        param = recognition.get("param")
        if not isinstance(param, dict):
            return None

        box_index = param.get("box_index")
        if isinstance(box_index, int) and box_index >= 0:
            return box_index
        return None

    def _extract_text(self, result: Any, box_index: int | None = None) -> str | None:
        if box_index is not None:
            indexed_text = self._extract_text_by_index(result, box_index)
            if indexed_text is not None:
                return indexed_text

        if isinstance(result, dict):
            direct_text = result.get("text")
            if isinstance(direct_text, str):
                return direct_text

            for key in ("best", "best_result", "detail", "filtered", "filtered_results", "all"):
                if key in result:
                    nested_text = self._extract_text(result[key])
                    if nested_text is not None:
                        return nested_text
            return None

        if isinstance(result, Iterable) and not isinstance(result, (str, bytes, bytearray)):
            for item in result:
                item_text = self._extract_text(item)
                if item_text is not None:
                    return item_text
            return None

        if isinstance(result, OCRResult):
            return result.text

        text = getattr(result, "text", None)
        if isinstance(text, str):
            return text

        detail = getattr(result, "detail", None)
        if detail is not None and detail is not result:
            detail_text = self._extract_text(detail)
            if detail_text is not None:
                return detail_text

        best_result = getattr(result, "best_result", None)
        if best_result is not None and best_result is not result:
            best_text = self._extract_text(best_result)
            if best_text is not None:
                return best_text

        filtered_results = getattr(result, "filtered_results", None)
        if filtered_results is not None and filtered_results is not result:
            for item in filtered_results:
                item_text = self._extract_text(item)
                if item_text is not None:
                    return item_text

        return None

    def _extract_text_by_index(self, result: Any, box_index: int) -> str | None:
        children = self._extract_children(result)
        if children is None or not 0 <= box_index < len(children):
            return None

        return self._extract_text(children[box_index])

    def _extract_children(self, result: Any) -> list[Any] | None:
        if isinstance(result, dict):
            for key in ("sub_results", "detail", "all", "filtered", "filtered_results"):
                value = self._coerce_sequence(result.get(key))
                if value is not None:
                    return value

            raw_detail = result.get("raw_detail")
            if raw_detail is not None:
                raw_children = self._extract_children(raw_detail)
                if raw_children is not None:
                    return raw_children
            return None

        sub_results = self._coerce_sequence(getattr(result, "sub_results", None))
        if sub_results is not None:
            return sub_results

        detail = self._coerce_sequence(getattr(result, "detail", None))
        if detail is not None:
            return detail

        raw_detail = getattr(result, "raw_detail", None)
        if raw_detail is not None:
            raw_children = self._extract_children(raw_detail)
            if raw_children is not None:
                return raw_children

        all_results = self._coerce_sequence(getattr(result, "all", None))
        if all_results is not None:
            return all_results

        filtered_results = self._coerce_sequence(getattr(result, "filtered_results", None))
        if filtered_results is not None:
            if len(filtered_results) == 1:
                nested_children = self._extract_children(filtered_results[0])
                if nested_children is not None:
                    return nested_children
            return filtered_results

        best_result = getattr(result, "best_result", None)
        if best_result is not None:
            best_children = self._extract_children(best_result)
            if best_children is not None:
                return best_children

        return None

    def _coerce_sequence(self, value: Any) -> list[Any] | None:
        if value is None or isinstance(value, (str, bytes, bytearray, dict)):
            return None

        if isinstance(value, list):
            return value

        try:
            return list(value)
        except TypeError:
            return None

    def _to_jsonable(self, value: Any, depth: int = 0) -> Any:
        if depth >= 6:
            return repr(value)

        if value is None or isinstance(value, (str, int, float, bool)):
            return value

        if isinstance(value, dict):
            return {
                str(key): self._to_jsonable(item, depth + 1)
                for key, item in value.items()
            }

        if isinstance(value, OCRResult):
            return {
                "type": type(value).__name__,
                "text": value.text,
            }

        if isinstance(value, Iterable) and not isinstance(value, (str, bytes, bytearray)):
            return [self._to_jsonable(item, depth + 1) for item in value]

        result: dict[str, Any] = {"type": type(value).__name__}
        for attr in (
            "hit",
            "text",
            "box",
            "detail",
            "raw_detail",
            "best_result",
            "filtered_results",
            "sub_results",
            "all",
            "algorithm",
            "name",
            "reco_id",
        ):
            if hasattr(value, attr):
                attr_value = getattr(value, attr)
                if attr_value is not None:
                    result[attr] = self._to_jsonable(attr_value, depth + 1)

        if len(result) == 1:
            result["repr"] = repr(value)
        return result

    def _normalize_expression(self, expression: str) -> str:
        normalized = expression.replace("&&", " and ").replace("||", " or ")
        normalized = re.sub(r"!(?!=)", " not ", normalized)
        return normalized

    def _validate_ast(self, node: ast.AST, allowed_names: set[str]) -> None:
        for child in ast.walk(node):
            if isinstance(
                child,
                (
                    ast.Expression,
                    ast.Load,
                    ast.BinOp,
                    ast.BoolOp,
                    ast.UnaryOp,
                    ast.Compare,
                    ast.Name,
                    ast.Constant,
                    ast.Add,
                    ast.Sub,
                    ast.Mult,
                    ast.Div,
                    ast.Mod,
                    ast.And,
                    ast.Or,
                    ast.Not,
                    ast.UAdd,
                    ast.USub,
                    ast.Eq,
                    ast.NotEq,
                    ast.Lt,
                    ast.LtE,
                    ast.Gt,
                    ast.GtE,
                ),
            ):
                if isinstance(child, ast.Name) and child.id not in allowed_names:
                    raise ValueError(f"unexpected name {child.id}")
                if isinstance(child, ast.Constant) and not isinstance(
                    child.value, (int, float, bool)
                ):
                    raise ValueError("unsupported constant")
                continue
            raise ValueError(f"unsupported syntax {type(child).__name__}")