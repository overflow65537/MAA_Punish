from assets.src.action_CrimsonWeave.main import CrimsonWeave
from assets.src.action_GeneralFight.main import GeneralFight

from maa.toolkit import Toolkit

def main():
    # 注册自定义动作
    Toolkit.pi_register_custom_action("CrimsonWeave", CrimsonWeave())
    Toolkit.pi_register_custom_action("GeneralFight", GeneralFight())

    # 启动 MaaPiCli
    Toolkit.pi_run_cli("./", "./", False)

if __name__ == "__main__":
    main()