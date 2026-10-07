"""分辨率检查器在 MaaFwApp（PI_CLIENT_NAME）下的跳过行为。"""

from __future__ import annotations

import logging

import pytest

from maa.event_sink import NotificationType

from sink import resolution_check


@pytest.fixture
def records():
    """收集该模块 logger 的输出，用于断言「不输出日志」。"""
    collected: list[logging.LogRecord] = []

    class _Collector(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            collected.append(record)

    handler = _Collector()
    logger = logging.getLogger(resolution_check.logger.name)
    logger.addHandler(handler)
    try:
        yield collected
    finally:
        logger.removeHandler(handler)


class _TaskerStub:
    """任何属性访问都视为失败，用于确认跳过分支不再碰控制器。"""

    def __getattr__(self, name: str):
        raise AssertionError(f"跳过时不应访问 tasker.{name}")


class _DetailStub:
    def __getattr__(self, name: str):
        raise AssertionError(f"跳过时不应访问 detail.{name}")


class TestShouldSkipClient:
    @pytest.mark.parametrize("value", ["MaaFWApp", "MaaFwApp", "maafwapp", " MaaFWApp "])
    def test_matches_maafwapp_ignoring_case(self, monkeypatch, value: str):
        monkeypatch.setenv(resolution_check.PI_CLIENT_NAME_ENV, value)
        assert resolution_check.should_skip_client() is True

    @pytest.mark.parametrize("value", ["MFAA", "MXU", "MaaPiCli", "MaaDebugger", ""])
    def test_other_clients_are_kept(self, monkeypatch, value: str):
        monkeypatch.setenv(resolution_check.PI_CLIENT_NAME_ENV, value)
        assert resolution_check.should_skip_client() is False

    def test_missing_env_is_not_skipped(self, monkeypatch):
        monkeypatch.delenv(resolution_check.PI_CLIENT_NAME_ENV, raising=False)
        assert resolution_check.should_skip_client() is False


class TestOnTaskerTask:
    def test_maafwapp_does_nothing_and_logs_nothing(self, monkeypatch, records):
        monkeypatch.setenv(resolution_check.PI_CLIENT_NAME_ENV, "MaaFWApp")
        sink = resolution_check.AspectRatioChecker()

        sink.on_tasker_task(_TaskerStub(), NotificationType.Starting, _DetailStub())

        assert records == []

    def test_other_client_still_checks(self, monkeypatch, records):
        monkeypatch.setenv(resolution_check.PI_CLIENT_NAME_ENV, "MFAA")

        class _Tasker:
            controller = None

        class _Detail:
            task_id = 1
            entry = "SomeTask"

        sink = resolution_check.AspectRatioChecker()
        sink.on_tasker_task(_Tasker(), NotificationType.Starting, _Detail())

        assert any(record.levelno == logging.ERROR for record in records)
