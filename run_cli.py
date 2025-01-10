from assets.custom.action.CrimsonWeave.main import CrimsonWeave
from assets.custom.action.LostLullaby.main import LostLullaby
from assets.custom.action.GeneralFight.main import GeneralFight
from assets.custom.action.Oblivion.main import Oblivion
from assets.custom.action.Pyroath.main import Pyroath
from assets.custom.action.Stigmata.main import Stigmata

from maa.toolkit import Toolkit

def main():
    # 注册自定义动作
    Toolkit.pi_register_custom_action("CrimsonWeave", CrimsonWeave())
    Toolkit.pi_register_custom_action("GeneralFight", GeneralFight())
    Toolkit.pi_register_custom_action("LostLullaby", LostLullaby())
    Toolkit.pi_register_custom_action("Oblivion", Oblivion())
    Toolkit.pi_register_custom_action("Pyroath", Pyroath())
    Toolkit.pi_register_custom_action("Stigmata", Stigmata())

    # 启动 MaaPiCli
    Toolkit.pi_run_cli("./", "./", False)

if __name__ == "__main__":
    main()