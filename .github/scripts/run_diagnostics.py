# .github/scripts/run_diagnostics.py

import os
import sys
import subprocess
import google.generativeai as genai

def get_git_diff():
    """获取本次推送与 main 分支的差异文件列表和内容。"""
    try:
        # 首先确保我们有main分支的信息
        subprocess.run(["git", "fetch", "origin", "main"], check=True)
        
        # 获取差异文件的路径列表
        result = subprocess.run(
            ["git", "diff", "origin/main...HEAD", "--name-only"],
            capture_output=True, text=True, check=True
        )
        changed_files = result.stdout.strip().split('\n')

        # 读取每个差异文件的内容
        diff_content = ""
        for file_path in changed_files:
            if os.path.exists(file_path):
                diff_content += f"--- {file_path} ---\n"
                with open(file_path, 'r', encoding='utf-8') as f:
                    diff_content += f.read()
                diff_content += "\n\n"
        
        return diff_content, changed_files
    except subprocess.CalledProcessError as e:
        print(f"Error getting git diff: {e}", file=sys.stderr)
        return None, None
    except Exception as e:
        print(f"An unexpected error occurred in get_git_diff: {e}", file=sys.stderr)
        return None, None


def call_gemini_api(api_key, diff_content):
    """调用Gemini API进行诊断。"""
    if not api_key:
        print("Error: GEMINI_API_KEY secret not found.", file=sys.stderr)
        return None

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-pro')

    # 从项目根目录读取架构规则文件
    # 注意：在GitHub Actions环境中，路径是相对于根目录的
    try:
        with open('DIAGNOSTICS_REPORT.md', 'r', encoding='utf-8') as f:
            diagnostics_rules = f.read()
    except FileNotFoundError:
        diagnostics_rules = "DIAGNOSTICS_REPORT.md not found. Please review based on general best practices."

    prompt = f"""
    **Role**: You are an AI code diagnostician, acting as an automated code reviewer in a CI/CD pipeline.

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

    Example of a valid response:
    {{
      "status": "approved",
      "reason": "This change correctly refactors the component according to the plan."
    }}

    Example of another valid response:
    {{
      "status": "rejected",
      "reason": "This introduces a business logic component into the shared UI layer, violating FSD principles."
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        # 尝试解析JSON
        import json
        return json.loads(response.text)
    except Exception as e:
        print(f"Error calling Gemini API or parsing response: {e}", file=sys.stderr)
        print(f"Raw response was: {getattr(response, 'text', 'N/A')}", file=sys.stderr)
        return None


def main():
    """主执行函数"""
    diff, files = get_git_diff()
    if not diff:
        print("No diff found or error occurred. Approving empty commit.")
        status, reason = "approved", "No file changes detected."
    else:
        print(f"Found changed files:\n{files}")
        api_key = os.getenv('GEMINI_API_KEY')
        result = call_gemini_api(api_key, diff)
        
        if result and 'status' in result and 'reason' in result:
            status = result['status']
            reason = result['reason']
        else:
            status = "rejected"
            reason = "Failed to get a valid diagnostic result from the AI."

    # 使用 GitHub Actions 的方式输出结果
    # 这会将变量设置到后续步骤的环境中
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        print(f"status={status}", file=f)
        print(f"reason={reason}", file=f)
    
    print(f"Diagnostics complete. Status: {status}. Reason: {reason}")
    
    if status == 'rejected':
        sys.exit(1) # 使工作流步骤失败

if __name__ == "__main__":
    main()