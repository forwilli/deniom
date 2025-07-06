# .github/scripts/run_diagnostics.py

import os
import sys
import subprocess
import json
from dotenv import load_dotenv
import google.generativeai as genai

# 从项目根目录加载 .env 文件
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 注意: 在GitHub Actions环境中，我们不使用.env文件，而是使用Secrets
if os.path.exists(os.path.join(project_root, '.env')):
    load_dotenv(os.path.join(project_root, '.env'))

def get_git_diff():
    """获取本次推送与 main 分支的差异文件列表和内容。"""
    try:
        subprocess.run(["git", "fetch", "origin", "main"], check=True)
        result = subprocess.run(
            ["git", "diff", "origin/main...HEAD", "--name-only"],
            capture_output=True, text=True, check=True
        )
        changed_files = result.stdout.strip().split('\n')
        diff_content = ""
        for file_path in changed_files:
            if os.path.exists(file_path):
                diff_content += f"--- {file_path} ---\n"
                with open(file_path, 'r', encoding='utf-8') as f:
                    diff_content += f.read()
                diff_content += "\n\n"
        return diff_content, changed_files
    except Exception as e:
        print(f"Error getting git diff: {e}", file=sys.stderr)
        return None, None

def call_gemini_api(api_key, diff_content):
    """调用Gemini API进行诊断。"""
    if not api_key:
        print("Error: GEMINI_API_KEY secret not found.", file=sys.stderr)
        return None

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-pro')

    try:
        with open('DIAGNOSTICS_REPORT.md', 'r', encoding='utf-8') as f:
            diagnostics_rules = f.read()
    except FileNotFoundError:
        diagnostics_rules = "DIAGNOSTICS_REPORT.md not found."

    prompt = f"""
    **Role**: You are an AI code diagnostician in a CI/CD pipeline.
    **Context**: A developer has submitted the following code changes.
    **Architectural Rules & Tasks**:
    ---
    {diagnostics_rules}
    ---
    **Submitted Changes**:
    ---
    {diff_content}
    ---
    **Task**: Review the changes. Do they adhere to the rules and resolve pending tasks?
    **Output Format**: Respond with a JSON object ONLY, with "status" ("approved" or "rejected") and "reason".
    """
    
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        print(f"Error calling Gemini API: {e}", file=sys.stderr)
        return None

def main():
    """主执行函数"""
    diff, files = get_git_diff()
    if not diff:
        print("No diff found. Approving.")
        status, reason = "approved", "No file changes."
    else:
        api_key = os.getenv('GEMINI_API_KEY')
        result = call_gemini_api(api_key, diff)
        if result and result.get('status') == 'approved':
            status = 'approved'
            reason = result.get('reason', 'Approved by AI.')
        else:
            status = "rejected"
            reason = result.get('reason') if result else "AI diagnostics failed."

    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        print(f"status={status}", file=f)
        print(f"reason={reason}", file=f)
    
    if status == 'rejected':
        print(f"❌ AI Rejected: {reason}")
        sys.exit(1)
    else:
        print(f"✅ AI Approved: {reason}")

if __name__ == "__main__":
    main()