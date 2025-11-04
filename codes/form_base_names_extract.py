
from config.weakness_chart import weakness_chart

FORM_BASE_DEX_OFFSET = 7001
form_base_names = []

# Extract all form Dex numbers >= FORM_BASE_DEX_OFFSET
form_entries = [
    (int(data["dex"]), name)
    for name, data in weakness_chart.items()
    if int(data["dex"]) >= FORM_BASE_DEX_OFFSET
]

# Sort by Dex number
form_entries.sort(key=lambda x: x[0])

# Keep all unique names (ignore exact duplicates)
seen = set()
for _, name in form_entries:
    if name not in seen:
        form_base_names.append(name)
        seen.add(name)

# Write to form_base_names.py
with open("form_base_names.py", "w", encoding="utf-8") as f:
    f.write("FORM_BASE_NAMES = [\n")
    for name in form_base_names:
        f.write(f'    "{name}",\n')
    f.write("]\n")

print(
    f"[INFO] form_base_names.py created with {len(form_base_names)} entries (sorted by Dex)."
)
