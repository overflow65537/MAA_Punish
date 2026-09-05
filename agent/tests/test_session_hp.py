"""Tests for combat HP zero exit checks."""

from __future__ import annotations

import time
from dataclasses import dataclass

from action.combat.core.provider import CombatCheck, parse_hp_current
from action.combat.core.session import CombatTask

from test_support.fakes import FakeBestResult, FakeContext, FakeRecognitionResult


@dataclass
class _FakeCombat:
    frame: bytes = b"img"


@dataclass
class _HpCheck(CombatCheck):
    hp: int | None = 100

    def in_combat(self, context, combat) -> bool:
        return True

    def read_current_hp(self, context, combat) -> int | None:
        return self.hp

    def match_exit_overlay(self, context, combat) -> str | None:
        return None

    def in_outer_interface(self, context, combat) -> bool:
        return False


def _combat(check: _HpCheck, **kwargs) -> CombatTask:
    return CombatTask(FakeContext(), check, **kwargs)


class TestParseHpCurrent:
    def test_parses_fraction(self):
        assert parse_hp_current("1234/5678") == 1234

    def test_parses_zero(self):
        assert parse_hp_current("0/10000") == 0

    def test_allows_spaces(self):
        assert parse_hp_current("0 / 100") == 0

    def test_rejects_plain_number(self):
        assert parse_hp_current("1234") is None


class TestReadCurrentHp:
    def test_reads_current_from_ocr(self):
        context = FakeContext(
            recognition_map={
                "检查血量": FakeRecognitionResult(
                    hit=True,
                    best_result=FakeBestResult(box=(19, 15, 141, 29), text="321/999"),
                )
            }
        )
        assert CombatCheck().read_current_hp(context, _FakeCombat()) == 321

    def test_miss_is_none(self):
        assert CombatCheck().read_current_hp(FakeContext(), _FakeCombat()) is None


class TestHpZeroExit:
    def test_zero_for_five_seconds_exits(self):
        combat = _combat(_HpCheck(hp=0), hp_zero_timeout=5.0)
        combat._hp_zero_since = time.monotonic() - 5.1
        assert combat._check_combat_presence() == "hp_zero"

    def test_nonzero_resets_timer(self):
        combat = _combat(_HpCheck(hp=50))
        combat._hp_zero_since = time.monotonic() - 4.0
        assert combat._check_combat_presence() == ""
        assert combat._hp_zero_since is None

    def test_unknown_hp_does_not_start_timer(self):
        combat = _combat(_HpCheck(hp=None))
        assert combat._check_combat_presence() == ""
        assert combat._hp_zero_since is None

    def test_unknown_after_zero_still_times_out(self):
        combat = _combat(_HpCheck(hp=None), hp_zero_timeout=5.0)
        combat._hp_zero_since = time.monotonic() - 5.1
        assert combat._check_combat_presence() == "hp_zero"
