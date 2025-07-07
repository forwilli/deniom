# .github/scripts/run_diagnostics.py
import os
import sys
import subprocess
import json
from dotenv import load_dotenv
import google.generativeai as genai

# 从项目根目录加载 .env 文件
# __file__ is in .github/scripts/run_diagnostics.py
# project_root is two levels up.
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 注意: 在GitHub Actions环境中，我们不使用.env文件，而是使用Secrets
if os.path.exists(os.path.join(project_root, '.env')):
    load_dotenv(os.path.join(project_root, '.env'))

def get_git_diff():
    """获取本次推送与 main 分支的差异文件列表和内容。"""
    try:
        # 首先确保我们有main分支的信息
        subprocess.run(["git", "fetch", "origin", "main"], check=True, capture_output=True, text=True)
        
        # 获取差异文件的路径列表
        result = subprocess.run(
            ["git", "diff", "origin/main...HEAD", "--name-only"],
            capture_output=True, text=True, check=True
        )
        changed_files = result.stdout.strip().split('\n')
        if not any(changed_files):
            return None, None

        diff_content = ""
        for file_path in changed_files:
            if os.path.exists(file_path) and os.path.isfile(file_path):
                diff_content += f"--- {file_path} ---\n"
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        diff_content += f.read()
                except Exception as e:
                    diff_content += f"[Could not read file content for: {file_path} due to {e}]\n"
                diff_content += "\n\n"
        
        return diff_content, changed_files
    except subprocess.CalledProcessError as e:
        print(f"Error getting git diff: {e.stderr}", file=sys.stderr)
        return None, None
    except Exception as e:
        print(f"An unexpected error occurred in get_git_diff: {e}", file=sys.stderr)
        return None, None

def call_gemini_api(api_key, diff_content):
    """调用Gemini API进行诊断。"""
    if not api_key:
        return {"status": "rejected", "reason": "GEMINI_API_KEY secret not found."}

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-pro')

    try:
        with open('DIAGNOSTICS_REPORT.md', 'r', encoding='utf-8') as f:
            diagnostics_rules = f.read()
    except FileNotFoundError:
        diagnostics_rules = "DIAGNOSTICS_REPORT.md not found."

    prompt = f"""
    **Role**: You are an AI code diagnostician in a CI/CD pipeline.

    **Context**: A developer has submitted the following code changes. Your task is to audit these changes against the project's architectural principles and outstanding tasks.

    **Project's Architectural Rules & Current Tasks**:
    ---
    {diagnostics_rules}
    ---

    **Submitted Code Changes**:
    ---
    {diff_content}
    ---

    **Task**: Review the submitted changes. 
    1.  Do they adhere to the project's rules and help resolve any of the pending tasks?
    2.  Do they introduce any new technical debt or architectural violations?

    **Output Format**: Respond with a JSON object ONLY, with NO other text or markdown formatting. The JSON object must have two keys: "status" (either "approved" or "rejected") and "reason" (a brief, one-sentence explanation for your decision).
    """
    
    response = None # Initialize response to None
    try:
        response = model.generate_content(prompt)
        raw_text = response.text
        
        # New: Robustly extract JSON from markdown code blocks
        match = re.search(r'```(json)?\s*({.*?})\s*```', raw_text, re.DOTALL)
        if match:
            json_text = match.group(2)
        else:
            json_text = raw_text # Assume it's already plain JSON

        print(f"--- Cleaned JSON for parsing ---\n{json_text}\n-----------------------------", file=sys.stderr)
        return json.loads(json_text)
    except Exception as e:
        raw_response_text = getattr(response, 'text', 'Response object was not created or has no text.')
        print(f"Error calling Gemini API or parsing JSON: {e}", file=sys.stderr)
        print(f"--- Raw Gemini Response that caused error ---\n{raw_response_text}\n------------------------------------------", file=sys.stderr)
        return None

def main():
    """主执行函数"""
    diff, files = get_git_diff()
    if not diff:
        print("No diff found or error occurred. Approving empty commit.")
        status, reason = "approved", "No file changes detected."
    else:
        print(f"Diagnosing staged files:\n{', '.join(files)}")
        api_key = os.getenv('GEMINI_API_KEY')
        result = call_gemini_api(api_key, diff)
        
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