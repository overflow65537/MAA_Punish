<!-- markdownlint-disable MD033 MD041 -->
<p align="center">
  <img alt="LOGO" src="logo.png" width="256" height="256" />
</p>

<div align="center">

# MAA_Punish

An assistant for Punishing: Gray Raven, built on a new architecture. Image recognition + simulated input, so you don't have to play the dailies by hand!  
Powered by [MaaFramework](https://github.com/MaaXYZ/MaaFramework).

[中文](README.md) | **English**

</div>

<p align="center">
  <img alt="license" src="https://img.shields.io/github/license/overflow65537/MAA_Punish">
  <img alt="Python" src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white">
  <img alt="platform" src="https://img.shields.io/badge/platform-Android%20%7C%20Windows%20%7C%20Linux%20%7C%20macOS-blueviolet">
  <img alt="commit" src="https://img.shields.io/github/commit-activity/m/overflow65537/MAA_Punish">
  <img alt="mirrorchyan_rid" src="https://img.shields.io/badge/mirrorchyan_rid-MAA__Punish-orange">
</p>

## Disclaimer

- This resource is **open source** and **free**.
- It is provided "as is", without warranty of any kind, express or implied. You use it at your own risk.
- The authors are not liable for any direct, indirect or consequential loss caused by using it.
- It is a standalone component. Its MIT license is not viral, and it is not affected by the licenses of other software it is integrated with.
- Any commercial activity based on this resource has nothing to do with the original authors, and users must not imply any official affiliation or endorsement.

## Global / NA client

The English UI and the **English (Global)** resource are for the Global / NA client (`com.kurogame.gplay.punishing.grayraven.en`). This support is new and still being tested, so some tasks may not work yet.

- In the launcher, select **English (Global)** as the resource. With the Chinese resource selected, the tool looks for Chinese text and won't recognise anything.
- Keep your battle buttons in the default layout, or turn on **Cache button layout** in the resource settings if you've moved them.
- The roguelike modes only have their setup options (difficulty, strategy, mode) in English so far; they can't complete a run on Global yet.
- High-Rank Mapping and Guardian Operation aren't currently available on Global.

If something gets stuck on Global, please open an issue with the log attached (see Notes below).

## Features

- Start / close the game
- Command Bureau: Fortune Machine draw
- Dorm commissions
- Dorm tasks
- Command Bureau check-in
- Simulated Siege
- Farm A-rank construct shards
- War Zone: automatic first clear
- Norman: automatic first clear
- Phantom Pain Cage: automatic first clear
- High-Rank Mapping
- Guardian Operation
- Claim mail
- Buy Inver-Shards from the shop automatically
- Claim Serum
- Simulated Battlefield
- Claim Battle Pass and mission rewards
- Auto roguelike: Recitativo di Fantasia
- Auto roguelike: Cursed Waves
- Auto roguelike: Derived from Matrix
- Auto roguelike: Awakening Tundra
- Auto roguelike: The Godfall Revelation

## Notes

- Android: any emulator works. If some tasks can't finish, switch to 1280\*720 (240 DPI).
- Desktop: run it as administrator.
- PlayCover: supported but untested. Please report any problems.
- If it won't start, first try installing the Visual C++ runtime: <https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170>
- For other problems, open an issue or ask in the QQ group **965061066** (Chinese). Please attach the log from the `debug` folder when reporting a problem. Thank you!

## Usage

Download: [https://github.com/overflow65537/MAA_Punish/releases](https://github.com/overflow65537/MAA_Punish/releases)

### Android

- Download `MPA-android-vXXX.apk` and install it.
- Android package name: com.overflow65537.maafw.punish.
- For Shizuku / root authorisation and the steps after that, see the [MaaFwApp instructions](https://github.com/Aliothmoon/MaaFwApp#使用已打包的应用) (Chinese).
- On first launch, follow the app's prompts to grant notifications, battery-optimisation exemption, and Shizuku or root permission.
- Development builds without a release signature have a `-debug` suffix; you may need to uninstall the development build before installing a later release.

### Windows

- Most users should download `MPA-win-x86_64-vXXX.zip`.
- If you're sure your PC is ARM, download `MPA-win-aarch64-vXXX.zip`.
- Unzip it and run `FOS.exe`.

### macOS

- For an Intel Mac, download `MPA-macos-x86_64-vXXX.dmg`.
- For an Apple Silicon (M1, M2, …) Mac, download `MPA-macos-aarch64-vXXX.dmg`.
- Then:
  1. Open the dmg and copy **all** of its contents to a local folder (keep `MFW.app`, `MFWUpdater`, `maafw/`, `resource/` and the rest in the same folder). Your home folder is recommended:

     ```zsh
     mkdir -p ~/MPA
     cp -R /Volumes/MPA/. ~/MPA/
     ```

  2. Open the folder and run the program:

     ```zsh
     open ~/MPA
     ```

     Find `MFW.app` (or `FOS`) and double-click it. Don't copy the `.app` out on its own.

  ⚠️ Gatekeeper warning:
  `MFW.app` isn't signed by Apple, so Gatekeeper may block it with "cannot be opened because the developer cannot be verified" or "is damaged" (the latter is usually a false alarm; the file isn't really damaged). Hold **Control**, right-click `MFW.app`, choose "Open", and confirm in the dialog. After allowing it once, you can double-click it normally.

  If you downloaded the dmg in a browser, macOS may also mark the files as quarantined (`com.apple.quarantine`). If it still won't open, look for an "Open Anyway" button in System Settings → Privacy & Security, or remove the quarantine flag (change the path to where you installed it):

  ```zsh
  xattr -rd com.apple.quarantine ~/MPA
  ```

  You can also try launching it once from the terminal: `open ~/MPA/MFW.app`.

### Linux

- x86_64: download `MPA-linux-x86_64-vXXX.tar.gz`
- aarch64: download `MPA-linux-aarch64-vXXX.tar.gz`
- Extract it and run `./MFW` or `./run-mfw.sh` from the same folder (the `tar.gz` keeps the executable permissions).

  ```bash
  mkdir -p ~/MPA
  tar -xzf MPA-linux-*-vXXX.tar.gz -C ~/MPA
  chmod +x ~/MPA/MFW ~/MPA/MFWUpdater ~/MPA/run-mfw.sh
  ~/MPA/run-mfw.sh
  ```

## Development

### Auto-combat (character-specific logic)

The combat framework lives in `agent/action/combat/`. The pipeline dispatches everything through `CombatRunner`. To add a character, register it in `LoadSetting.py` and implement a `BaseRole` subclass under `roles/` (class name = `cls_name`); you **don't** need to register each one in `agent_file.py`.

See the [combat framework development guide](docs/自动战斗框架开发指南.md) (Chinese) for details. It includes **LLM prompt templates** you can paste into Cursor or similar tools to change how a character fights.

Characters with their own combat logic so far:

| Frame (CN) | cls_name | Source file |
|------|----------|--------|
| 深红囚影 | CrimsonWeave | `agent/action/combat/roles/crimson_weave.py` |
| 深谣 | LostLullaby | `agent/action/combat/roles/lost_lullaby.py` |
| 终焉 | Oblivion | `agent/action/combat/roles/oblivion.py` |
| 誓焰 | Pyroath | `agent/action/combat/roles/pyroath.py` |
| 启明 | Shukra | `agent/action/combat/roles/shukra.py` |
| 深痕 | Stigmata | `agent/action/combat/roles/stigmata.py` |
| 超刻 | Hyperreal | `agent/action/combat/roles/hyperreal.py` |
| 晖暮 | Crepuscule | `agent/action/combat/roles/crepuscule.py` |
| 希声 | Pianissimo | `agent/action/combat/roles/pianissimo.py` |
| 铮骨 | Aegis | `agent/action/combat/roles/aegis.py` |
| 骇影 | Spectre | `agent/action/combat/roles/spectre.py` |
| 逆冕 | InverseCrown | `agent/action/combat/roles/inverse_crown.py` |
| 霁梦 | Limpidity | `agent/action/combat/roles/limpidity.py` |
| 谬影 | Daemonissa | `agent/action/combat/roles/daemonissa.py` |
| 芒星之迹 | Startrail | `agent/action/combat/roles/startrail.py` |
| 灼惘 | Geiravor | `agent/action/combat/roles/geiravor.py` |
| 幻日 | Parhelion | `agent/action/combat/roles/parhelion.py` |
| 极锋 | Arete | `agent/action/combat/roles/arete.py` |
| 亡歌 | Dirge | `agent/action/combat/roles/dirge.py` |
| 不落日 | Aeternion | `agent/action/combat/roles/aeternion.py` |
| 安魂 | Lacrimosa | `agent/action/combat/roles/lacrimosa.py` |
| 烬航 | Effulgence | `agent/action/combat/roles/effulgence.py` |
| General | GeneralFight | `agent/action/combat/roles/general_fight.py` |

Characters without their own logic use the **GeneralFight** logic once the battle starts. PRs adding more are welcome; for development questions, ask in the QQ group **965061066**.

### Developer docs

- [MaaFramework quick start](https://github.com/MaaXYZ/MaaFramework/blob/main/docs/en_us/1.1-QuickStarted.md)
- [Combat framework development guide (with LLM prompts for changing combat)](docs/自动战斗框架开发指南.md) (Chinese)

### How to build

**Only read this if you want to build from source. Otherwise just [download a release](https://github.com/overflow65537/MAA_Punish/releases).**

#### Desktop

0. Clone the project with its submodules:

   ```bash
   git clone --recursive https://github.com/overflow65537/MAA_Punish.git
   ```

1. Download a MaaFramework [release package](https://github.com/MaaXYZ/MaaFramework/releases) and extract it into the `deps` folder.
2. Install:

   ```python
   python ./tools/ci/install.py
   ```

The binaries and resources are generated in the `install` folder.

#### Android

The Android APK is built with [MaaFwApp](https://github.com/Aliothmoon/MaaFwApp). The repository's `install` workflow assembles the MaaFramework Android libraries, the dual-ABI Python agent and this project's resources, and uploads the APK as an artifact; tagged builds also add the APK to the GitHub Release.

Building locally needs JDK 17, the Android SDK and Python 3. For the exact commands, packaging recipe and release-signing setup, see [`.github/android/README.md`](.github/android/README.md).

## Acknowledgements

### Open-source libraries

- [MaaFramework](https://github.com/MaaXYZ/MaaFramework)

  An automation black-box testing framework based on image recognition

- [MaaFwApp](https://github.com/Aliothmoon/MaaFwApp)

  A general-purpose Android GUI for MaaFramework

- [MFW-ChainFlow Assistant](https://github.com/overflow65537/MFW-PyQt6)

  A frontend based on PySide6 for MaaFramework

### Developers

Thanks to everyone who has contributed to MAA_Punish:

<a href="https://github.com/overflow65537/MAA_Punish/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=overflow65537/MAA_Punish&max=1000" alt="Contributors to MAA_Punish"/>
</a>

### Contributor list

See [AUTHORS.md](AUTHORS.md).
