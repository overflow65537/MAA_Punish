import sys
import os

if not os.path.exists("run_cli.py"):
    os.environ["MAAFW_BINARY_PATH"] = os.getcwd()

from maa.toolkit import Toolkit

from assets.custom.action.basics.CenterCamera import CenterCamera
from assets.custom.action.basics.CombatActions import CombatActions
from assets.custom.action.basics.Identify import Identify
from assets.custom.action.basics.IdentifyRoles import IdentifyRoles
from assets.custom.action.basics.MultiplayerAutoBattle import MultiplayerAutoBattle
from assets.custom.action.basics.ResetIdentify import ResetIdentify
from assets.custom.action.basics.ScreenShot import ScreenShot
from assets.custom.action.basics.SelectCharacter import SelectCharacter
from assets.custom.action.basics.SetTower import SetTower
from assets.custom.action.basics.Count import Count

from assets.custom.action.exclusives.CrimsonWeave import CrimsonWeave
from assets.custom.action.exclusives.LostLullaby import LostLullaby
from assets.custom.action.exclusives.Oblivion import Oblivion
from assets.custom.action.exclusives.Pyroath import Pyroath
from assets.custom.action.exclusives.Stigmata import Stigmata

from assets.custom.recognition.exclusives.CalculateScore import CalculateScore
from assets.custom.recognition.exclusives.IDFMembers import IDFMembers
from assets.custom.recognition.exclusives.IDFscore import IDFscore
from assets.custom.recognition.exclusives.IDFMasteryLevel import IDFMasteryLevel

print("如无必要,请使用MFW.exe运行")
print("if not necessary, please use MFW.exe to run")


def main():
    print("开始注册自定义内容")
    # 注册自定义动作-角色战斗逻辑
    Toolkit.pi_register_custom_action("CrimsonWeave", CrimsonWeave())  # 深红囚影
    Toolkit.pi_register_custom_action("LostLullaby", LostLullaby())  # 深谣
    Toolkit.pi_register_custom_action("Oblivion", Oblivion())  # 终焉
    Toolkit.pi_register_custom_action("Pyroath", Pyroath())  # 誓焰
    Toolkit.pi_register_custom_action("Stigmata", Stigmata())  # 深痕
    # 注册自定义动作-通用逻辑
    Toolkit.pi_register_custom_action("ScreenShot", ScreenShot())  # 错误截图
    Toolkit.pi_register_custom_action("Identify", Identify())  # 识别人物
    Toolkit.pi_register_custom_action("ResetIdentify", ResetIdentify())  # 重置识别
    Toolkit.pi_register_custom_action("CenterCamera", CenterCamera())  # 重置镜头
    Toolkit.pi_register_custom_action("IdentifyRoles", IdentifyRoles())  # 角色识别
    Toolkit.pi_register_custom_action(
        "MultiplayerAutoBattle", MultiplayerAutoBattle()
    )  # 多人战斗
    Toolkit.pi_register_custom_action("CombatActions", CombatActions())  # 通用角色战斗
    Toolkit.pi_register_custom_action("SetTower", SetTower())  # 设置塔
    Toolkit.pi_register_custom_action("Count", Count())  # 计数
    Toolkit.pi_register_custom_action("SelectCharacter", SelectCharacter())  # 选择角色
    # 注册自定义识别
    Toolkit.pi_register_custom_recognition(
        "CalculateScore", CalculateScore()
    )  # 计算分数
    Toolkit.pi_register_custom_recognition("IDFMembers", IDFMembers())  # 识别宿舍成员
    Toolkit.pi_register_custom_recognition("IDFscore", IDFscore())  # 识别分数
    Toolkit.pi_register_custom_recognition("IDFMasteryLevel", IDFMasteryLevel())  # 识别大师度

    directly = "-d" in sys.argv
    Toolkit.pi_run_cli("./", "./", directly)


if __name__ == "__main__":
    main()
