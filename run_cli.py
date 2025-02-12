import sys

from maa.toolkit import Toolkit

from assets.custom.action.basics import CenterCamera, GeneralFight, Identify, ResetIdentify, ScreenShot, Stigmata
from assets.custom.action.exclusives import CrimsonWeave, LostLullaby, Oblivion, Pyroath
from assets.custom.recognition.exclusives import CalculateScore, IDFMembers, IDFscore


def main():
    # 注册自定义动作
    Toolkit.pi_register_custom_action("CrimsonWeave", CrimsonWeave())
    Toolkit.pi_register_custom_action("GeneralFight", GeneralFight())
    Toolkit.pi_register_custom_action("LostLullaby", LostLullaby())
    Toolkit.pi_register_custom_action("Oblivion", Oblivion())
    Toolkit.pi_register_custom_action("Pyroath", Pyroath())
    Toolkit.pi_register_custom_action("Stigmata", Stigmata())
    Toolkit.pi_register_custom_action("ScreenShot", ScreenShot())
    Toolkit.pi_register_custom_action("Identify", Identify())
    Toolkit.pi_register_custom_action("ResetIdentify", ResetIdentify())
    Toolkit.pi_register_custom_action("CenterCamera", CenterCamera())
    # 注册自定义识别
    Toolkit.pi_register_custom_recognition("CalculateScore", CalculateScore())
    Toolkit.pi_register_custom_recognition("IDFMembers", IDFMembers())
    Toolkit.pi_register_custom_recognition("IDFscore", IDFscore())

    directly = "-d" in sys.argv
    Toolkit.pi_run_cli("./", "./", directly)


if __name__ == "__main__":
    main()
