"""
MAA_Punish Agent 运行时 i18n。

读取 PI_CLIENT_LANGUAGE（默认 zh_cn），从 assets/locales/interface/{lang}.json 加载文案。
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

_LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales" / "interface"
_DEFAULT_LANG = "zh_cn"


def get_language() -> str:
    raw = os.environ.get("PI_CLIENT_LANGUAGE", _DEFAULT_LANG).strip().lower()
    if raw in {"zh_cn", "zh_tw"}:
        return raw
    return _DEFAULT_LANG


@lru_cache(maxsize=4)
def _load_table(lang: str) -> dict[str, str]:
    path = _LOCALES_DIR / f"{lang}.json"
    if not path.is_file():
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def t(key: str, **kwargs: object) -> str:
    """翻译 key；缺失时回退 zh_cn，仍缺失则返回 key 本身。支持 str.format 占位符。"""
    lang = get_language()
    for candidate in (lang, _DEFAULT_LANG):
        table = _load_table(candidate)
        if key in table:
            text = table[key]
            if kwargs:
                try:
                    return text.format(**kwargs)
                except (KeyError, IndexError, ValueError):
                    return text
            return text
    return key


def clear_cache() -> None:
    _load_table.cache_clear()
