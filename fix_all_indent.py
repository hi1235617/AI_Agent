# 批量修复store.py中所有方法的缩进问题

with open("nanobot/knowledge/store.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# 找到需要修复的起始行（从第85行开始的所有方法定义）
fix_start = 84  # 第85行是索引84

# 修复：从85行开始的所有行，如果不是空（只包含空格制表符），都在前面加4个空格
fixed_lines = lines[:fix_start]
for line in lines[fix_start:]:
    if line.strip():  # 如果不是空行
        fixed_lines.append("    " + line)  # 加4个空格
    else:
        fixed_lines.append(line)

# 写回文件
with open("nanobot/knowledge/store.py", "w", encoding="utf-8") as f:
    f.writelines(fixed_lines)

print("Fixed all methods indentation from line 85 onwards")
print("Total lines processed:", len(lines) - fix_start)