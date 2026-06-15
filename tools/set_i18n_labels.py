"""Change task JSON labels from hardcoded text to $key i18n format."""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

TASKS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "tasks")

updated = []
skipped = []

for filename in sorted(os.listdir(TASKS_DIR)):
    if not filename.endswith(".json"):
        continue
    path = os.path.join(TASKS_DIR, filename)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    task_list = data.get("task", [])
    if not task_list:
        skipped.append(f"{filename} (no task array)")
        continue

    task = task_list[0]
    name = task.get("name", "")
    if not name:
        skipped.append(f"{filename} (no name field)")
        continue

    expected_label = f"${name}"
    current_label = task.get("label", "")

    if current_label == expected_label:
        skipped.append(f"{filename} (already {expected_label})")
        continue

    task["label"] = expected_label
    data["task"][0] = task

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    updated.append(f"{filename}: '{current_label}' -> '{expected_label}'")


print(f"Updated {len(updated)} files:")
for u in updated:
    print(f"  {u}")
if skipped:
    print(f"\nSkipped {len(skipped)}:")
    for s in skipped:
        print(f"  {s}")
