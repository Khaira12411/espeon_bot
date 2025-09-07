#!/usr/bin/env python3
# -------------------- Populate Shiny/Golden Forms --------------------
import ast
import pprint
import os

# -------------------- Config --------------------
WEAKNESS_CHART_FILE = os.path.join("config", "weakness_chart.py")

# -------------------- Load weakness_chart --------------------
with open(WEAKNESS_CHART_FILE, "r", encoding="utf-8") as f:
    content = f.read()

parsed = ast.parse(content)
weakness_chart = None
for node in parsed.body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
        if node.targets[0].id == "weakness_chart":
            weakness_chart = ast.literal_eval(node.value)

if weakness_chart is None:
    raise ValueError("Could not find weakness_chart dict in the file.")

print(f"💙 [INFO] Loaded {len(weakness_chart)} entries from weakness_chart.py")

# -------------------- Populate Shiny/Golden Variants (No Duplicates) --------------------
new_entries = {}
for name, data in weakness_chart.items():
    dex = data.get("dex")
    if not dex:
        continue

    # Skip mons with dex starting with 7
    if str(dex).startswith("7"):
        print(f"💛 [SKIP] {name} (dex {dex} starts with 7)")
        continue

    base_dex_int = int(dex)

    # Shiny variant
    shiny_name = f"shiny {name}"
    if shiny_name not in weakness_chart:
        shiny_data = data.copy()
        shiny_data["dex"] = str(1000 + base_dex_int)
        new_entries[shiny_name] = shiny_data
        print(f"💙 [ADD] {shiny_name} → dex {shiny_data['dex']}")
    else:
        print(f"💛 [SKIP] {shiny_name} already exists")

    # Golden variant
    golden_name = f"golden {name}"
    if golden_name not in weakness_chart:
        golden_data = data.copy()
        golden_data["dex"] = str(9000 + base_dex_int)
        new_entries[golden_name] = golden_data
        print(f"💙 [ADD] {golden_name} → dex {golden_data['dex']}")
    else:
        print(f"💛 [SKIP] {golden_name} already exists")

# -------------------- Merge and Write Back --------------------
weakness_chart.update(new_entries)

with open(WEAKNESS_CHART_FILE, "w", encoding="utf-8") as f:
    f.write("weakness_chart = ")
    pprint.pprint(weakness_chart, stream=f, indent=4)

print("💙 [SUCCESS] weakness_chart.py updated successfully!")
