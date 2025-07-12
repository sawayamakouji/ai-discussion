import json
import datetime
import os
import re
from dotenv import load_dotenv
import google.generativeai as genai

# .envからAPIキー読み込み
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError(".envにGEMINI_API_KEYが設定されていません")
genai.configure(api_key=api_key)

# ファイル名定義
SUMMARY_FILE = "summary.md"
RULES_FILE = "rules.md"
NEXT_INSTR_FILE = "next_instructions.md"
FULL_LOG_FILE = "full_logs.md"

# エージェント設定
agents = {
    "Planner": "戦略を論理式・短文英語で提案する",
    "Debugger": "リスクを論理式・短文英語で分析する",
    "Manager": "議論をまとめ次のアクションを決定する",
    "Synthesizer": "全出力を統合・要約・指針更新・次回指令を生成する"
}

# ファイル読み込み
def read_file(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

# ファイル保存
def save_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# Gemini応答
def gemini_chat(prompt, history=[]):
    model = genai.GenerativeModel("models/gemini-2.5-flash-lite-preview-06-17")
    response = model.generate_content(prompt + "\n" + "\n".join(history))
    return response.text.strip()

# Main

def main():
    summary = read_file(SUMMARY_FILE)
    rules = read_file(RULES_FILE)
    next_instructions = read_file(NEXT_INSTR_FILE)
    history = []
    logs = []

    print("=== AI壁打ち 1ターン開始 ===")
    user_input = input("ユーザーの問いかけを入力してください（空で次の行動を使用、exitで終了）: ").strip()
    if user_input.lower() == "exit":
        print("終了します。")
        return
    if not user_input:
        user_input = next_instructions or "次のステップを続行してください。"

    history.append(f"User Input: {user_input}")
    logs.append({"agent": "User", "message": user_input})

    for agent, role in agents.items():
        if agent == "Synthesizer":
            continue  # Synthesizerは後でまとめ実行
        prompt = f"[{agent}] {role}. Summary so far: {summary}. Rules: {rules}. User Input: {user_input}"
        message = gemini_chat(prompt, history[-3:])
        print(f"[{agent}] {message}")
        logs.append({"agent": agent, "message": message})
        history.append(f"{agent}: {message}")

    # Synthesizer 統合処理
    synth_prompt = (
        "You are Synthesizer. Integrate Planner, Debugger, and Manager outputs into updated summary, important rules, and next instructions. "
        f"Summary so far: {summary}\nRules so far: {rules}\nLogs: {json.dumps(logs, ensure_ascii=False)}"
    )
    synth_response = gemini_chat(synth_prompt)
    print(f"[Synthesizer] {synth_response}")

    # summary/rules/next instructionsを抽出
    summary_match = re.search(r"SUMMARY:(.*?)RULES:", synth_response, re.DOTALL)
    rules_match = re.search(r"RULES:(.*?)NEXT_INSTRUCTIONS:", synth_response, re.DOTALL)
    next_instr_match = re.search(r"NEXT_INSTRUCTIONS:(.*)$", synth_response, re.DOTALL)

    summary_new = summary_match.group(1).strip() if summary_match else synth_response
    rules_new = rules_match.group(1).strip() if rules_match else rules
    next_instructions_new = next_instr_match.group(1).strip() if next_instr_match else "次のステップを続行してください。"

    save_file(SUMMARY_FILE, summary_new)
    save_file(RULES_FILE, rules_new)
    save_file(NEXT_INSTR_FILE, next_instructions_new)

    # ログ保存
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(FULL_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n# --- SESSION {now} ---\n")
        for entry in logs:
            f.write(f"## {entry['agent']}\n{entry['message']}\n\n")
        f.write(f"## Synthesizer\n{synth_response}\n")
        f.write("# --- SESSION END ---\n")

    print(f"=== Summary保存完了: {SUMMARY_FILE} ===")
    print(f"=== Rules保存完了: {RULES_FILE} ===")
    print(f"=== Next Instructions保存完了: {NEXT_INSTR_FILE} ===")
    print(f"=== Full Log保存完了: {FULL_LOG_FILE} ===")

if __name__ == "__main__":
    main()
