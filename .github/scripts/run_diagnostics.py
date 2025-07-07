# .github/scripts/run_diagnostics.py
import os
import sys
import subprocess
import json
import re
from dotenv import load_dotenv
import google.generativeai as genai
from pathlib import Path

# 从项目根目录加载 .env 文件
# __file__ is in .github/scripts/run_diagnostics.py
# project_root is two levels up.
project_root = Path(__file__).resolve().parent.parent.parent
# 注意: 在GitHub Actions环境中，我们不使用.env文件，而是使用Secrets
if (project_root / '.env').exists():
    load_dotenv(project_root / '.env')

def get_git_diff():
    """获取本次推送与 main 分支的行级差异。"""
    try:
        # 首先确保我们有main分支的信息
        subprocess.run(["git", "fetch", "origin", "main"], check=True, capture_output=True, text=True)
        
        # 获取与 origin/main 的差异
        result = subprocess.run(
            ["git", "diff", "origin/main...HEAD"],
            capture_output=True, text=True, check=True
        )
        diff_content = result.stdout.strip()
        if not diff_content:
            return None
        
        return diff_content
    except subprocess.CalledProcessError as e:
        print(f"Error getting git diff: {e.stderr}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"An unexpected error occurred in get_git_diff: {e}", file=sys.stderr)
        return None

def load_project_rules(root_path: Path):
    """加载项目中的所有架构和协作规则文档。"""
    rules_content = ""
    rule_files = [
        "AI_DIAGNOSTICIAN_ROLE.md",
        "COLLABORATION_MODEL.md",
        "DIAGNOSTICS_REPORT.md" # 当前的任务和问题也是一种动态规则
    ]
    # 添加根目录下的规则文件
    for file_name in rule_files:
        file_path = root_path / file_name
        if file_path.exists():
            rules_content += f"--- START OF {file_name} ---\n"
            rules_content += file_path.read_text(encoding='utf-8', errors='ignore')
            rules_content += f"\n--- END OF {file_name} ---\n\n"

    # 添加所有 .cursor/rules 目录下的规则
    rule_dirs = root_path.glob('**/.cursor/rules')
    for rule_dir in rule_dirs:
        for rule_file in rule_dir.rglob('*.mdc'):
            rules_content += f"--- START OF {rule_file.relative_to(root_path)} ---\n"
            rules_content += rule_file.read_text(encoding='utf-8', errors='ignore')
            rules_content += f"\n--- END OF {rule_file.relative_to(root_path)} ---\n\n"

    return rules_content

def call_gemini_api(api_key, diff_content, project_rules):
    """调用Gemini API进行诊断。"""
    if not api_key:
        return {"status": "rejected", "reason": "GEMINI_API_KEY secret not found."}

    genai.configure(api_key=api_key)
    # 参数化模型名称，提供默认值
    model_name = os.getenv('GEMINI_DIAGNOSTICS_MODEL', 'gemini-2.5-pro')
    model = genai.GenerativeModel(model_name)

    prompt = f"""
    **Role**: You are an AI code diagnostician in a CI/CD pipeline. You are rigorous, detail-oriented, and serve as the guardian of the project's architecture.

    **Context**: A developer has submitted code changes. Your task is to audit these changes against ALL of the project's established architectural principles, collaboration models, and current tasks.

    **Project's Rules, Principles, and Tasks (Comprehensive)**:
    ---
    {project_rules}
    ---

    **Submitted Code Changes (in diff format)**:
    ---
    {diff_content}
    ---

    **Your Task**:
    1.  **Analyze the diff**: Carefully examine the submitted code changes.
    2.  **Cross-reference with rules**: Compare the changes against the comprehensive rules provided. Do the changes adhere to the file structure, naming conventions, architectural patterns (FSD, modular services), and coding standards? Do they align with the collaboration model?
    3.  **Check against tasks**: Do the changes contribute to solving any pending tasks listed in the `DIAGNOSTICS_REPORT.md`?
    4.  **Identify Violations**: Explicitly state any violations or deviations from the rules.
    5.  **Make a Decision**: Based on your analysis, decide whether to approve or reject the changes. Only approve changes that are fully compliant or are trivial fixes. Reject any changes that introduce architectural debt or violate established principles.

    **Output Format**: Respond with a JSON object ONLY, with NO other text or markdown formatting. The JSON object must have two keys:
    - "status": string, must be either "approved" or "rejected".
    - "reason": string, a brief, one-sentence explanation for your decision. If rejected, clearly state the primary violation.
    """
    
    response = None # Initialize response to None
    try:
        response = model.generate_content(prompt)
        raw_text = response.text
        
        match = re.search(r'```(json)?\s*({.*?})\s*```', raw_text, re.DOTALL)
        if match:
            json_text = match.group(2)
        else:
            json_text = raw_text

        print(f"--- Cleaned JSON for parsing ---\n{json_text}\n-----------------------------", file=sys.stderr)
        return json.loads(json_text)
    except Exception as e:
        raw_response_text = getattr(response, 'text', 'Response object was not created or has no text.')
        print(f"Error calling Gemini API or parsing JSON: {e}", file=sys.stderr)
        print(f"--- Raw Gemini Response that caused error ---\n{raw_response_text}\n------------------------------------------", file=sys.stderr)
        return None

def main():
    """主执行函数"""
    diff = get_git_diff()
    if not diff:
        print("No diff found. Approving empty or non-code commit.")
        status, reason = "approved", "No code changes detected."
    else:
        print("Diagnosing code changes...")
        project_rules = load_project_rules(project_root)
        api_key = os.getenv('GEMINI_API_KEY')
        result = call_gemini_api(api_key, diff, project_rules)
        
        if result and result.get('status') == 'approved':
            status = 'approved'
            reason = result.get('reason', 'Approved by AI.')
        else:
            status = "rejected"
            reason = result.get('reason') if result else "Failed to get a valid response from AI."

    github_output = os.getenv('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a') as f:
            print(f"status={status}", file=f)
            print(f"reason={reason}", file=f)
    
    print(f"Diagnostics complete. Status: {status}. Reason: {reason}")
    
    if status == 'rejected':
        print(f"❌ AI Rejected: {reason}")
        sys.exit(1)
    else:
        print(f"✅ AI Approved: {reason}")

if __name__ == "__main__":
    main()