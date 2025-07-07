# tools/supervisor_fixed.py
# Fixed version that handles multiple markdown formats

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
    # First, let's check if we have uncommitted changes
    status = run_command(["git", "status", "--porcelain"])
    if status and status.strip():
        print("Warning: You have uncommitted changes. Committing them first...")
        run_command(["git", "add", "."])
        run_command(["git", "commit", "-m", "chore: Auto-commit before supervisor sync"])
    
    run_command(["git", "checkout", "main"])
    run_command(["git", "pull", "origin", "main"])

def find_new_task():
    """解析任务板，寻找分配给Claude的新任务。"""
    print(f"\n--- Checking for new tasks for {CLAUDE_ASSIGNEE} ---")
    try:
        with open(TASK_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # More flexible regex that handles different markdown formats
        task_regex = re.compile(
            r"###\s*`\[\s*\]\s*To-Do`\s*(TASK-\d+:.*?)\n" # 捕获任务标题
            r"(.*?)" # 捕获中间的所有内容
            r"Assigned To[`\*]*:\s*[`\*]*Claude Code", # 更灵活的匹配
            re.DOTALL | re.IGNORECASE
        )
        
        matches = task_regex.findall(content)
        if matches:
            # Get the first match
            task_title = matches[0][0].strip()
            
            # Extract the full task content including instructions
            # Find the task in the original content to get proper boundaries
            task_start = content.find(f"### `[ ] To-Do` {task_title}")
            if task_start == -1:
                print(f"Error: Could not find task start for {task_title}")
                return None
                
            # Find the next task or end of file
            next_task = content.find("\n### ", task_start + 1)
            if next_task == -1:
                task_content = content[task_start:]
            else:
                task_content = content[task_start:next_task]
            
            print(f"✅ New task found: {task_title}")
            return {"title": task_title, "content": task_content}
            
    except FileNotFoundError:
        print(f"Error: {TASK_FILE} not found.")
    except Exception as e:
        print(f"Error parsing task file: {e}")
        import traceback
        traceback.print_exc()
        
    print("No new tasks found.")
    return None

def execute_claude_task(task):
    """
    实际执行Claude的任务
    """
    print(f"\n--- Executing task: {task['title']} ---")
    print("Task content preview:")
    print(task['content'][:500] + "..." if len(task['content']) > 500 else task['content'])
    
    # Extract task number
    task_match = re.search(r'TASK-(\d+)', task['title'])
    if not task_match:
        print("Error: Could not extract task number")
        return False
        
    task_num = task_match.group(1)
    branch_name = f"feature/TASK-{task_num}"
    
    print(f"\n[EXECUTION] Creating branch {branch_name}")
    
    # For now, just simulate the execution
    print("\n[SIMULATION MODE] Would execute the following steps:")
    print(f"1. Update TASK_BOARD.md to mark task as 'In Progress'")
    print(f"2. Create and checkout branch: {branch_name}")
    print(f"3. Execute the task based on instructions")
    print(f"4. Commit and push changes")
    print(f"5. Monitor CI/CD pipeline")
    
    return True

def main():
    """主函数，运行一次循环"""
    print("🤖 AI Supervisor started (single run mode)")
    
    sync_with_remote()
    new_task = find_new_task()
    
    if new_task:
        success = execute_claude_task(new_task)
        if success:
            print("\nTask execution completed (simulation).")
        else:
            print("\nTask execution failed.")
    else:
        print("\nNo new tasks found for Claude Code.")

if __name__ == "__main__":
    main()