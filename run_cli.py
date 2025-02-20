import sys
import os
if not os.path.exists("run_cli.py"):
    os.environ["MAAFW_BINARY_PATH"] = os.getcwd()

from maa.toolkit import Toolkit

from assets.custom.action.basics import (
    CenterCamera,
    GeneralFight,
    Identify,
    ResetIdentify,
    ScreenShot,
)
from assets.custom.action.exclusives import (
    CrimsonWeave,
    LostLullaby,
    Oblivion,
    Pyroath,
    Stigmata,
)
from assets.custom.recognition.exclusives import CalculateScore, IDFMembers, IDFscore


def main():
    # 注册自定义动作-角色战斗逻辑
    Toolkit.pi_register_custom_action("CrimsonWeave", CrimsonWeave())  # 深红囚影
    Toolkit.pi_register_custom_action("LostLullaby", LostLullaby())  # 深谣
    Toolkit.pi_register_custom_action("Oblivion", Oblivion())  # 终焉
    Toolkit.pi_register_custom_action("Pyroath", Pyroath())  # 誓焰
    Toolkit.pi_register_custom_action("Stigmata", Stigmata())  # 深痕
    # 注册自定义动作-通用逻辑
    Toolkit.pi_register_custom_action("GeneralFight", GeneralFight())  # 通用战斗逻辑
    Toolkit.pi_register_custom_action("ScreenShot", ScreenShot())  # 错误截图
    Toolkit.pi_register_custom_action("Identify", Identify())  # 识别人物
    Toolkit.pi_register_custom_action("ResetIdentify", ResetIdentify())  # 重置识别
    Toolkit.pi_register_custom_action("CenterCamera", CenterCamera())  # 重置镜头
    # 注册自定义识别
    Toolkit.pi_register_custom_recognition(
        "CalculateScore", CalculateScore()
    )  # 计算分数
    Toolkit.pi_register_custom_recognition("IDFMembers", IDFMembers())  # 识别宿舍成员
    Toolkit.pi_register_custom_recognition("IDFscore", IDFscore())  # 识别分数

    directly = "-d" in sys.argv
    Toolkit.pi_run_cli("./", "./", directly)


if __name__ == "__main__":
    main()
