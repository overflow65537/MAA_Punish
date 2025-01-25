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
from maa.toolkit import Toolkit


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

    # 启动 MaaPiCli
    Toolkit.pi_run_cli("./", "./", False)


if __name__ == "__main__":
    main()
