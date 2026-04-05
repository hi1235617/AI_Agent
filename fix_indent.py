# Fix method indentation for lines 85+ in store.py

with open("nanobot/knowledge/store.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

fix_start = 84  # Start from line 85
fixed_lines = lines[:fix_start]

for line in lines[fix_start:]:
    stripped = line.lstrip()
    # If it's a method definition and has 0 indentation, add 4 spaces
    if (stripped.startswith("async def ") or stripped.startswith("def ")) and line == stripped:
        fixed_lines.append("    " + line)
    else:
        fixed_lines.append(line)

with open("nanobot/knowledge/store.py", "w", encoding="utf-8") as f:
    f.writelines(fixed_lines)

print("Fixed all top-level method definitions from line 85 onwards")