# tools/supervisor_single_run.py
# Modified version of supervisor.py that runs just one cycle for testing

import subprocess
import time
import re
import os

# --- 配置 ---
REPO_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASK_FILE = os.path.join(REPO_PATH, "TASK_BOARD.md")
CLAUDE_ASSIGNEE = "Claude Code"

def run_command(command, working_dir=REPO_PATH):
    """在一个子进程中运行命令并返回其输出。"""
    print(f"Executing: {' '.join(command)}")
    result = subprocess.run(command, cwd=working_dir, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error executing command: {result.stderr}")
        return None
    print(result.stdout)
    return result.stdout

def sync_with_remote():
    """切换到main分支并从远程拉取最新代码。"""
    print("\n--- Syncing with remote repository ---")
    run_command(["git", "checkout", "main"])
    run_command(["git", "pull", "origin", "main"])

def find_new_task():
    """解析任务板，寻找分配给Claude的新任务。"""
    print(f"\n--- Checking for new tasks for {CLAUDE_ASSIGNEE} ---")
    try:
        with open(TASK_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用正则表达式寻找一个完整的 To-Do 任务块
        # 这个正则表达式会寻找一个以 `### [ ] To-Do` 开头，并分配给Claude的部分
        task_regex = re.compile(
            r"###\s*`\[\s*\]\s*To-Do`\s*(TASK-\d+:.*?)" # 捕获任务标题
            r".*?Assigned To`:\s*" + re.escape(CLAUDE_ASSIGNEE) + # 确保分配给Claude
            r"(.*?)" # 捕获任务内容
            r"(?=\n###|\Z)", # 匹配到下一个任务标题或文件末尾
            re.DOTALL | re.IGNORECASE
        )
        
        match = task_regex.search(content)
        if match:
            task_title = match.group(1).strip()
            task_instructions = match.group(2).strip()
            print(f"✅ New task found: {task_title}")
            return {"title": task_title, "instructions": task_instructions}
            
    except FileNotFoundError:
        print(f"Error: {TASK_FILE} not found.")
    except Exception as e:
        print(f"Error parsing task file: {e}")
        
    print("No new tasks found.")
    return None

def execute_claude_task(task):
    """
    【占位符】这里将调用 Claude 的核心逻辑。
    这个函数是我们需要 Claude 实现的部分。
    """
    print(f"\n--- Executing task: {task['title']} ---")
    print("Instructions:\n", task['instructions'][:200] + "..." if len(task['instructions']) > 200 else task['instructions'])
    
    # --- Claude 的工作流程应该在这里被触发 ---
    # 1. 更新 TASK_BOARD.md 状态为 [In Progress]
    # 2. git checkout -b feature/TASK-XXX
    # 3. 根据 instructions 修改代码
    # 4. git commit & git push
    # 5. 【高级】开始轮询GitHub Actions的结果
    # -----------------------------------------

    print("\n[SIMULATION] Claude is processing the task...")
    print("[SIMULATION] This is where Claude would actually execute the task.")
    print("----------------------------------------")
    return True # 返回执行结果

def main():
    """主函数，运行一次循环"""
    print("🤖 AI Supervisor started (single run mode)")
    
    sync_with_remote()
    new_task = find_new_task()
    
    if new_task:
        success = execute_claude_task(new_task)
        if success:
            print("Task execution would be initiated here.")
        else:
            print("Task execution failed.")
    else:
        print("No new tasks found for Claude Code.")

if __name__ == "__main__":
    main()