"""Tests for action.combat.config.validate_config."""

from __future__ import annotations

from action.combat.config import LoadSetting
from action.combat.config.validate_config import validate_role_actions


class TestValidateRoleActionsHappyPath:
    def test_real_repo_passes(self):
        assert validate_role_actions() is True

    def test_echo_display_name_regression(self):
        assert LoadSetting.ROLE_ACTIONS["亚里莎·回音"]["name"] == "回音"


class TestValidateRoleActionsErrorPath:
    def test_missing_cls_name_fails(self, monkeypatch):
        bad = {
            "坏角色": {
                "name": "坏",
                "attack_template": ["自定义战斗/x.png"],
                "template": ["人物索引/x.png"],
            }
        }
        monkeypatch.setattr(
            "action.combat.config.validate_config.ROLE_ACTIONS", bad
        )
        assert validate_role_actions() is False

    def test_empty_attack_template_fails(self, monkeypatch):
        bad = {
            "坏角色": {
                "name": "坏",
                "cls_name": "GeneralFight",
                "attack_template": [],
                "template": ["人物索引/x.png"],
            }
        }
        monkeypatch.setattr(
            "action.combat.config.validate_config.ROLE_ACTIONS", bad
        )
        assert validate_role_actions() is False

    def test_unknown_cls_name_fails(self, monkeypatch):
        bad = {
            "坏角色": {
                "name": "坏",
                "cls_name": "NotARealRole",
                "attack_template": ["自定义战斗/x.png"],
                "template": ["人物索引/x.png"],
            }
        }
        monkeypatch.setattr(
            "action.combat.config.validate_config.ROLE_ACTIONS", bad
        )
        assert validate_role_actions() is False

    def test_missing_image_fails(self, monkeypatch):
        bad = {
            "坏角色": {
                "name": "坏",
                "cls_name": "GeneralFight",
                "attack_template": ["自定义战斗/不存在.png"],
                "template": ["人物索引/不存在.png"],
            }
        }
        monkeypatch.setattr(
            "action.combat.config.validate_config.ROLE_ACTIONS", bad
        )
        monkeypatch.setattr(
            "action.combat.config.validate_config._image_exists",
            lambda _path: False,
        )
        assert validate_role_actions() is False

    def test_missing_skill_template_image_fails(self, monkeypatch):
        bad = {
            "坏角色": {
                "name": "坏",
                "cls_name": "GeneralFight",
                "attack_template": ["自定义战斗/神威/不落日/不落日.png"],
                "template": ["人物索引/神威/不落日/不落日.png"],
                "skill_template": {
                    "red": {
                        "识别信号球": {"template": ["信号球/不存在_红.png"]}
                    }
                },
            }
        }
        monkeypatch.setattr(
            "action.combat.config.validate_config.ROLE_ACTIONS", bad
        )

        def image_exists(path: str) -> bool:
            return path != "信号球/不存在_红.png"

        monkeypatch.setattr(
            "action.combat.config.validate_config._image_exists",
            image_exists,
        )
        assert validate_role_actions() is False
