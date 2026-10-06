"""缓存相关全局选项的传输通道约定（选项写 attach、custom 读本节点 attach）。"""

from __future__ import annotations

import datetime
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from action.basics import role_cache_policy as policy
from recognition.exclusives import CacheRole as cache_role_module

OPTIONS_PATH = (
    Path(__file__).resolve().parents[2] / "options" / "global_option.json"
)
CACHE_NODE = "是否需要缓存"
FREQ_OPTION = "角色缓存更新频率"
HOUR_OPTION = "角色缓存刷新时间"


def _load_options() -> dict:
    return json.loads(OPTIONS_PATH.read_text(encoding="utf-8"))


def _iter_overrides(option: dict):
    if "pipeline_override" in option:
        yield option["pipeline_override"]
    for case in option.get("cases", []) or []:
        if "pipeline_override" in case:
            yield case["pipeline_override"]


def _attach_keys(option: dict, node: str) -> set[str]:
    keys: set[str] = set()
    for override in _iter_overrides(option):
        node_override = override.get(node) or {}
        keys |= set((node_override.get("attach") or {}).keys())
    return keys


class TestOptionChannel:
    """两个缓存选项都只走 attach，且写在同一节点上的键互不重叠。"""

    def test_both_options_are_global(self):
        data = _load_options()
        assert FREQ_OPTION in data["global_option"]
        assert HOUR_OPTION in data["global_option"]
        assert FREQ_OPTION in data["option"]
        assert HOUR_OPTION in data["option"]

    def test_options_never_write_custom_recognition_param(self):
        data = _load_options()
        for name in (FREQ_OPTION, HOUR_OPTION):
            for override in _iter_overrides(data["option"][name]):
                dumped = json.dumps(override, ensure_ascii=False)
                assert "custom_recognition_param" not in dumped, (
                    f"{name} 仍在写 custom_recognition_param（会与其它选项互相覆盖）"
                )

    def test_attach_keys_are_disjoint_on_shared_node(self):
        data = _load_options()
        freq_keys = _attach_keys(data["option"][FREQ_OPTION], CACHE_NODE)
        hour_keys = _attach_keys(data["option"][HOUR_OPTION], CACHE_NODE)
        assert freq_keys == {"update_frequency"}
        assert hour_keys == {"refresh_hour"}
        assert not (freq_keys & hour_keys)

    def test_role_selection_nodes_keep_both_values(self):
        data = _load_options()
        for node in (
            "选择角色程序",
            "选择角色程序_onlyNode",
            "选择角色程序_矩阵循生",
        ):
            freq_keys = _attach_keys(data["option"][FREQ_OPTION], node)
            hour_keys = _attach_keys(data["option"][HOUR_OPTION], node)
            assert freq_keys == {"update_frequency"}
            assert hour_keys == {"refresh_hour"}

    def test_at_most_one_option_writes_param_on_cache_node(self):
        data = _load_options()
        writers = [
            name
            for name, option in data["option"].items()
            for override in _iter_overrides(option)
            if "custom_recognition_param"
            in json.dumps(override.get(CACHE_NODE) or {}, ensure_ascii=False)
        ]
        assert len(writers) <= 1, f"{CACHE_NODE} 上多个选项写 param: {writers}"


class _FakeLogger:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def _record(self, msg, *args) -> None:
        self.messages.append(msg % args if args else str(msg))

    def info(self, msg, *args) -> None:
        self._record(msg, *args)

    def warning(self, msg, *args) -> None:
        self._record(msg, *args)

    def debug(self, msg, *args) -> None:
        self._record(msg, *args)

    def error(self, msg, *args) -> None:
        self._record(msg, *args)

    def joined(self) -> str:
        return "\n".join(self.messages)


class _FakeContext:
    def __init__(self, node_data: dict) -> None:
        self._node_data = node_data

    def get_node_data(self, name: str):
        return self._node_data


@pytest.fixture
def cache_file():
    # 不用 pytest 的 tmp_path：本机 %TEMP%\pytest-of-errov 目录 ACL 异常
    with tempfile.TemporaryDirectory(prefix="maa_punish_cache_") as directory:
        yield Path(directory) / "role_cache.json"


def _prepare(cache_file: Path, monkeypatch, cache_data: dict | None) -> _FakeLogger:
    if cache_data is not None:
        policy.write_cache_data(cache_data, cache_file)
    monkeypatch.setattr(policy, "cache_path", lambda prefix=None: cache_file)
    logger = _FakeLogger()
    monkeypatch.setattr(
        cache_role_module,
        "LoggerComponent",
        lambda name: SimpleNamespace(logger=logger),
    )
    return logger


def _stale_cache() -> dict:
    return {
        "main_update_at": (
            datetime.datetime.now() - datetime.timedelta(days=30)
        ).timestamp(),
        "focus": {"角色A": {"cage": 1}},
    }


class TestCacheRoleReadsNodeAttach:
    def test_reads_frequency_and_hour_from_attach(self, cache_file, monkeypatch):
        logger = _prepare(cache_file, monkeypatch, _stale_cache())
        context = _FakeContext(
            {"attach": {"update_frequency": "never", "refresh_hour": 14}}
        )
        argv = SimpleNamespace(node_name=CACHE_NODE, custom_recognition_param="")

        result = cache_role_module.CacheRole().analyze(context, argv)

        assert result is None  # never -> 不触发更新
        assert "update_frequency=never" in logger.joined()
        assert "refresh_hour=14" in logger.joined()

    def test_attach_wins_over_custom_recognition_param(self, cache_file, monkeypatch):
        logger = _prepare(cache_file, monkeypatch, _stale_cache())
        context = _FakeContext({"attach": {"update_frequency": "never"}})
        argv = SimpleNamespace(
            node_name=CACHE_NODE,
            custom_recognition_param=json.dumps({"update_frequency": "weekly"}),
        )

        result = cache_role_module.CacheRole().analyze(context, argv)

        assert result is None  # attach 的 never 生效，param 的 weekly 不应触发更新
        assert "update_frequency=never" in logger.joined()

    def test_falls_back_to_custom_recognition_param(self, cache_file, monkeypatch):
        logger = _prepare(cache_file, monkeypatch, _stale_cache())
        context = _FakeContext({})
        argv = SimpleNamespace(
            node_name=CACHE_NODE,
            custom_recognition_param=json.dumps(
                {"update_frequency": "never", "refresh_hour": 0}
            ),
        )

        result = cache_role_module.CacheRole().analyze(context, argv)

        assert result is None
        assert "refresh_hour=0" in logger.joined()
