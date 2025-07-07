import re

# Read the TASK_BOARD.md file
with open('TASK_BOARD.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Original regex from supervisor.py
task_regex = re.compile(
    r"###\s*`\[\s*\]\s*To-Do`\s*(TASK-\d+:.*?)" # 捕获任务标题
    r".*?Assigned To`:\s*Claude Code" + # 确保分配给Claude  
    r"(.*?)" # 捕获任务内容
    r"(?=\n###|\Z)", # 匹配到下一个任务标题或文件末尾
    re.DOTALL | re.IGNORECASE
)

# Try to find matches
matches = task_regex.findall(content)
print(f"Found {len(matches)} matches with original regex")

# Let's also check for the actual pattern in the file
print("\nSearching for To-Do tasks...")
todo_pattern = re.compile(r"###\s*`\[\s*\]\s*To-Do`.*?TASK-\d+", re.IGNORECASE)
todo_matches = todo_pattern.findall(content)
print(f"Found {len(todo_matches)} To-Do tasks:")
for match in todo_matches:
    print(f"  - {match}")

# Check for "Assigned To" pattern
assigned_pattern = re.compile(r"Assigned To[`:\s]*Claude Code", re.IGNORECASE)
assigned_matches = assigned_pattern.findall(content)
print(f"\nFound {len(assigned_matches)} 'Assigned To: Claude Code' patterns")