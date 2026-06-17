from pathlib import Path
import shutil
import sys
import jsonc

working_dir = Path(__file__).parent
install_path = working_dir / Path("install")
version = len(sys.argv) > 1 and sys.argv[1] or "v0.0.1"

# 安装包资源（原 assets/ 下内容，现位于仓库根目录）
RESOURCE_ITEMS = (
    "agent",
    "resource",
    "tasks",
    "i18n",
    "interface.json",
)


def install_resource():
    for name in RESOURCE_ITEMS:
        src = working_dir / name
        dst = install_path / name
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    shutil.copy2(
        working_dir / "logo.png",
        install_path / "logo.png",
    )
    shutil.copy2(
        working_dir / "update_flag.txt",
        install_path / "update_flag.txt",
    )

    with open(install_path / "interface.json", "r", encoding="utf-8") as f:
        interface = jsonc.load(f)

    interface["version"] = version
    with open(install_path / "interface.json", "w", encoding="utf-8") as f:
        jsonc.dump(interface, f, ensure_ascii=False, indent=4)


def install_chores():
    shutil.copy2(
        working_dir / "README.md",
        install_path,
    )
    shutil.copy2(
        working_dir / "LICENSE",
        install_path,
    )
    # 默认简体副本（兼容未解析 i18n 的 Client）；多语言正文在 i18n/<lang>/
    shutil.copy2(
        working_dir / "i18n" / "zh_cn" / "DISCLAIMER.md",
        install_path / "DISCLAIMER.md",
    )
    shutil.copy2(
        working_dir / "i18n" / "zh_cn" / "CONTACT.md",
        install_path / "CONTACT.md",
    )
    for lang in ("zh_cn", "zh_tw"):
        src = working_dir / "i18n" / lang
        dst = install_path / "i18n" / lang
        dst.mkdir(parents=True, exist_ok=True)
        for name in ("CONTACT.md", "DISCLAIMER.md"):
            shutil.copy2(src / name, dst / name)
    shutil.copy2(
        install_path / "logo.png",
        install_path / "dashboard.png",
    )


if __name__ == "__main__":
    install_resource()
    install_chores()
