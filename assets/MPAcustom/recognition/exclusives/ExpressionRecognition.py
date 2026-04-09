import ast
import json
import re
from typing import Any

from maa.custom_recognition import CustomRecognition
from maa.define import OCRResult


PLACEHOLDER_PATTERN = re.compile(r"\{([^{}]+)\}")
NUMBER_PATTERN = re.compile(r"[-+]?\d+(?:\.\d+)?")


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

        def replace_placeholder(match: re.Match[str]) -> str:
            node_name = match.group(1).strip()
            if not node_name:
                raise ValueError("empty placeholder")

            variable_name = placeholder_mapping.get(node_name)
            if variable_name is None:
                variable_name = f"_value_{len(placeholder_mapping)}"
                placeholder_mapping[node_name] = variable_name
                values_cache[variable_name] = self._resolve_node_value(
                    context, image, node_name
                )
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
        except (ValueError, SyntaxError, TypeError, ZeroDivisionError):
            return CustomRecognition.AnalyzeResult(box=None, detail={"status": "invalid expression"})

        if type(result) is not bool:
            return CustomRecognition.AnalyzeResult(box=None, detail={"status": "expression did not evaluate to boolean"})

        if not result:
            return CustomRecognition.AnalyzeResult(box=None, detail={"status": "expression evaluated to false"})

        return CustomRecognition.AnalyzeResult(
            box=(0, 0, 100, 100),
            detail={
                "status": "success",
                "expression": expression,
                "resolved_expression": python_expression,
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

    def _resolve_node_value(self, context, image, node_name: str) -> int | float:
        recognition = context.run_recognition(node_name, image)
        if not (
            recognition
            and recognition.hit
            and isinstance(recognition.best_result, OCRResult)
        ):
            raise ValueError(f"node {node_name} has no OCR result")

        match = NUMBER_PATTERN.search(recognition.best_result.text)
        if match is None:
            raise ValueError(f"node {node_name} has no numeric OCR text")

        number_text = match.group(0)
        if "." in number_text:
            return float(number_text)
        return int(number_text)

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