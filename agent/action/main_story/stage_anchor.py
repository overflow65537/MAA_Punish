# Copyright (c) 2024-2025 MAA_Punish
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
MAA_Punish
MAA_Punish 主线章节内的关卡锚点推进
作者:overflow65537

pipeline 侧约定（见 tools/gen_main_story_stages.py 生成的节点）：

    进入章节 → 滑动 → 初始化关卡_XX（本文件 MainStoryInitStage）
        ├─ 用一次 OCR 找出当前可见的最大关号
        ├─ 锚点 当前关卡     = XX_NN   （这次要打的那一关）
        └─ 锚点 当前章节推进 = 推进关卡_XX
    → [Anchor]当前关卡 → XX_NN 点击 → 主线_选关后战斗
    → 回到章节界面 → [Anchor]当前章节推进 → 推进关卡_XX（本文件 MainStoryAdvance）
        ├─ 锚点 当前关卡 +1
        └─ 已经是本章最后一关时，锚点指向 退出本章_XX
    → 主线_打当前关 → [Anchor]当前关卡 → ...
"""

from __future__ import annotations

import json
import re

from maa.custom_action import CustomAction
from maa.custom_recognition import CustomRecognition

from logger_component import LoggerComponent

logger = LoggerComponent(__name__).logger

ANCHOR_STAGE = "当前关卡"
ANCHOR_ADVANCE = "当前章节推进"

# 全屏 OCR 节点，识别结果由本文件自己过滤（关号前缀随章节变化，不能写死在节点里）
STAGE_LIST_NODE = "主线_关卡列表"

# 同一章里允许连续回退几次（成功推进一次就清零）。回退是真会重打上一关的，
# 所以不能一路退到底，否则会在"打过-退回来"之间来回弹。
ROLLBACK_BUDGET = 2
_rollbacks: dict[str, int] = {}


def _load_param(raw: str | None) -> dict:
    try:
        return json.loads(raw or "{}")
    except ValueError:
        logger.error(f"main_story: 参数不是合法 JSON: {raw!r}")
        return {}


class MainStoryInitStage(CustomRecognition):
    """进入章节后把锚点设到"当前这一关"。

    判定依据：关卡列表里可见的最大关号。进入章节前的滑动已经把列表推到最新，
    所以可见最大关号就是当前要打的那一关。
    取不到任何标签时退化成第 1 关——欠估只会白打一关，过估会一路空推进，
    所以这里宁可往小取。
    """

    def analyze(
        self,
        context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult | None:
        param = _load_param(argv.custom_recognition_param)
        chapter = str(param.get("chapter", ""))
        prefix = str(param.get("label_prefix", ""))
        try:
            stages = int(param.get("stages", 0))
        except (TypeError, ValueError):
            stages = 0
        if not chapter or not prefix:
            logger.error(f"main_story: 初始化参数不完整: {param!r}")
            return None

        picked, box = self._detect_stage(context, argv, prefix, stages)
        _rollbacks.pop(chapter, None)
        ok_stage = context.set_anchor(ANCHOR_STAGE, f"{chapter}_{picked:02d}")
        ok_advance = context.set_anchor(ANCHOR_ADVANCE, f"推进关卡_{chapter}")
        logger.info(
            f"[MainStoryInitStage] chapter={chapter} prefix={prefix} stages={stages} "
            f"→ {chapter}_{picked:02d} (set_anchor stage={ok_stage} advance={ok_advance})"
        )
        return CustomRecognition.AnalyzeResult(
            box=box,
            detail={
                "chapter": chapter,
                "stage": picked,
                "anchor_stage": f"{chapter}_{picked:02d}",
                "anchor_advance": f"推进关卡_{chapter}",
            },
        )

    def _detect_stage(
        self,
        context,
        argv: CustomRecognition.AnalyzeArg,
        prefix: str,
        stages: int,
    ) -> tuple[int, list[int]]:
        detail = context.run_recognition(STAGE_LIST_NODE, argv.image)
        if detail is None or not detail.all_results:
            logger.warning("[MainStoryInitStage] 关卡列表 OCR 无结果，退化为第 1 关")
            return 1, [0, 0, 1, 1]

        pattern = re.compile(rf"^\s*{re.escape(prefix)}\s*-\s*(\d+)\s*$")
        found: list[tuple[int, list[int]]] = []
        for result in detail.all_results:
            text = getattr(result, "text", "") or ""
            match = pattern.match(text)
            if match:
                found.append((int(match.group(1)), list(result.box)))

        if not found:
            logger.warning(
                f"[MainStoryInitStage] 未匹配到 {prefix}-N 标签，退化为第 1 关"
            )
            return 1, [0, 0, 1, 1]

        picked, box = max(found, key=lambda item: item[0])
        if stages and picked > stages:
            logger.warning(
                f"[MainStoryInitStage] 识别到 {picked} 超过表内关卡数 {stages}，按表截断"
            )
            picked = stages
        return picked, box


class MainStoryAdvance(CustomAction):
    """把锚点往前推一格：打完第 N 关，下一关就是 N+1。"""

    def run(
        self,
        context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:
        param = _load_param(argv.custom_action_param)
        chapter = str(param.get("chapter", ""))
        try:
            stages = int(param.get("stages", 0))
        except (TypeError, ValueError):
            stages = 0

        current = context.get_anchor(ANCHOR_STAGE)
        if not current:
            # 旧流程（未接入锚点）走不到这里，真走到了也别动锚点
            logger.warning("[MainStoryAdvance] 当前关卡锚点未设置，跳过推进")
            return CustomAction.RunResult(success=True)

        match = re.fullmatch(rf"{re.escape(chapter)}_(\d+)", current)
        if not match:
            logger.warning(
                f"[MainStoryAdvance] 锚点 {current!r} 不属于第 {chapter} 章，跳过推进"
            )
            return CustomAction.RunResult(success=True)

        stage = int(match.group(1))
        if stages and stage >= stages:
            target = f"退出本章_{chapter}"
        else:
            target = f"{chapter}_{stage + 1:02d}"

        ok = context.set_anchor(ANCHOR_STAGE, target)
        _rollbacks.pop(chapter, None)
        logger.info(f"[MainStoryAdvance] chapter={chapter} {current} → {target} (ok={ok})")
        return CustomAction.RunResult(success=True)


class MainStoryRollback(CustomAction):
    """on_error 兜底：锚点指向的关卡在屏幕上找不到时，退回上一关再试。

    触发条件：`主线_打当前关` 的 next 列表（锚点关卡 + 滑动重试）轮询超时——
    也就是这一关的标签怎么滚都找不到，通常是初始化把锚点设高了
    （例如把还没解锁的关卡当成了当前关），或者关卡列表停在了错误的位置。

    注意：这里只覆盖"找不到"，不覆盖"点了但没进战斗"——后者的界面依然停在
    关卡列表，全程没有任何识别失败，走不到 on_error。
    """

    def run(
        self,
        context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:
        current = context.get_anchor(ANCHOR_STAGE)
        if not current:
            logger.warning("[MainStoryRollback] 当前关卡锚点未设置，结束回退")
            return CustomAction.RunResult(success=False)

        match = re.fullmatch(r"(.+)_(\d+)", current)
        if not match:
            # 已经是 退出本章_XX 之类的收尾节点，别在这里打转
            logger.warning(f"[MainStoryRollback] 锚点 {current!r} 不是关卡节点，跳过回退")
            return CustomAction.RunResult(success=False)

        chapter, stage = match.group(1), int(match.group(2))
        used = _rollbacks.get(chapter, 0)
        if stage <= 1 or used >= ROLLBACK_BUDGET:
            logger.error(
                f"[MainStoryRollback] 第 {chapter} 章回退到头"
                f"(stage={stage}, used={used}/{ROLLBACK_BUDGET})，放弃本章"
            )
            context.set_anchor(ANCHOR_STAGE, f"退出本章_{chapter}")
            _rollbacks.pop(chapter, None)
            return CustomAction.RunResult(success=True)

        _rollbacks[chapter] = used + 1
        target = f"{chapter}_{stage - 1:02d}"
        ok = context.set_anchor(ANCHOR_STAGE, target)
        logger.warning(
            f"[MainStoryRollback] chapter={chapter} {current} → {target} "
            f"(第 {used + 1}/{ROLLBACK_BUDGET} 次回退, ok={ok})"
        )
        return CustomAction.RunResult(success=True)
