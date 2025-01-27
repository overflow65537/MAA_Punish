from assets.custom.action.CrimsonWeave.main import CrimsonWeave
from assets.custom.action.LostLullaby.main import LostLullaby
from assets.custom.action.GeneralFight.main import GeneralFight
from assets.custom.action.Oblivion.main import Oblivion
from assets.custom.action.Pyroath.main import Pyroath
from assets.custom.action.Stigmata.main import Stigmata
from assets.custom.action.ScreenShot.main import ScreenShot
from assets.custom.action.Identify.main import Identify
from assets.custom.action.ResetIdentify.main import ResetIdentify
from assets.custom.action.CenterCamera.main import CenterCamera
from assets.custom.recognition.CalculateScore.main import CalculateScore
from assets.custom.recognition.IDFMembers.main import IDFMembers
from assets.custom.recognition.IDFscore.main import IDFscore
from maa.toolkit import Toolkit

import sys

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
