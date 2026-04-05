# coding=utf-8
with open("nanobot/knowledge/store.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

print("Analyze method indentation:")
print("=" * 70)

for i, line in enumerate(lines, 1):
    stripped = line.lstrip()
    if stripped.startswith("async def ") or stripped.startswith("def "):
        indent = len(line) - len(line.lstrip())
        method_name = stripped.split("(")[0].replace("async def ", "").replace("def", "")
        status = "OK" if indent == 4 else "ERROR (indent=" + str(indent))
        print("Line %d: %s | indent=%d | %s" % (i, method_name.strip(), indent, status))