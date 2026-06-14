"""One-off: restore git exclusives into combat/roles/*Role.do_perform."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "assets" / "MPAcustom" / "action" / "combat" / "roles"

MAP = {
    "GeneralFight": ("general_fight.py", "GeneralFightRole"),
    "Shukra": ("shukra.py", "ShukraRole"),
    "CrimsonWeave": ("crimson_weave.py", "CrimsonWeaveRole"),
    "Hyperreal": ("hyperreal.py", "HyperrealRole"),
    "Oblivion": ("oblivion.py", "OblivionRole"),
    "Stigmata": ("stigmata.py", "StigmataRole"),
    "LostLullaby": ("lost_lullaby.py", "LostLullabyRole"),
    "Pyroath": ("pyroath.py", "PyroathRole"),
    "Crepuscule": ("crepuscule.py", "CrepusculeRole"),
    "Pianissimo": ("pianissimo.py", "PianissimoRole"),
    "InverseCrown": ("inverse_crown.py", "InverseCrownRole"),
    "Spectre": ("spectre.py", "SpectreRole"),
    "Limpidity": ("limpidity.py", "LimpidityRole"),
    "Aegis": ("aegis.py", "AegisRole"),
}

HEADER = '''# Copyright (c) 2024-2025 MAA_Punish
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations

import time

from MPAcustom.action.combat.core.role import BaseRole

'''


def convert_body(body: str) -> str:
    body = re.sub(
        r"^(\s*)def run\s*\([\s\S]*?\)\s*->\s*CustomAction\.RunResult\s*:",
        r"\1def do_perform(self) -> None:",
        body,
        flags=re.M,
    )
    body = re.sub(
        r"^\s*self\.action\s*=\s*CombatActions\([^)]*\)\s*\n", "", body, flags=re.M
    )
    body = re.sub(r"^\s*action\s*=\s*CombatActions\([^)]*\)\s*\n", "", body, flags=re.M)
    body = re.sub(r"def (\w+)\(self,\s*context:\s*Context\)", r"def \1(self)", body)
    body = re.sub(
        r"(?<!self\.combat\.)(?<!\.)\bcontext\.", "self.combat.context.", body
    )
    body = re.sub(r"self\.(\w+)\(context\)", r"self.\1()", body)
    body = re.sub(
        r"self\.(\w+)\(self\.combat\.context\)", r"self.\1()", body
    )
    body = re.sub(
        r"return CustomAction\.RunResult\([^)]*\)\s*\n", "return\n", body
    )
    body = re.sub(r"(?<!self\.)action\.", "self.action.", body)
    return body


def main() -> None:
    for cls, (fname, role_cls) in MAP.items():
        src = subprocess.check_output(
            ["git", "show", f"HEAD:assets/MPAcustom/action/exclusives/{cls}.py"],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        match = re.search(r"class\s+\w+\(CustomAction\):\n(.*)", src, re.S)
        if not match:
            raise RuntimeError(f"no class in {cls}")
        body = convert_body(match.group(1))
        content = HEADER + f"class {role_cls}(BaseRole):\n{body}"
        (OUT_DIR / fname).write_text(content, encoding="utf-8")
        print("wrote", fname)


if __name__ == "__main__":
    main()
