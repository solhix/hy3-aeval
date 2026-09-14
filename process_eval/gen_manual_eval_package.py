# -*- coding: utf-8 -*-
"""生成 WorkBuddy 人工评估工作包：
   - 把 18 条验证样本分成 6 组（每组 3 条），生成 6 个提示词文件
   - 把 8 道生产题分成 2 组（每组 4 条），生成 2 个提示词文件
   - 每个提示词可直接复制到 WorkBuddy 的 HY3 对话框
   - HY3 返回后，用 parse_workbuddy_replies.py 自动解析成 jsonl
"""
import json, os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RUBRIC_HEADER = """你是一名严谨的算法题解题过程评审员。下面给定若干道题的【题面摘要】、【解题过程】、【判题结论】，请逐题评估并输出 JSON。

要求每题输出一个 JSON 对象（不要用代码块，直接输出 JSON），包含：
- "id": 题目编号（原样复制我给你的编号）
- "process_valid": true/false（推理链是否成立）
- "first_error_step": 首个不成立步骤的编号（1-based，成立则为 null）
- "error_type": 从「题意误读/概念错误/计算错误/条件遗漏/跳步推导/格式不符/幻觉/无错误」中选一个
- "coincidence_pass": true/false（答案AC但过程有缺陷则为true）
- "confidence": 0.0~1.0
- "rationale": 不超过80字的中文理由

每题之间用 --- 分隔。不要输出任何其他解释。

"""

def make_eval_block(pid, pid_label, statement, process, verdict, score, code=""):
    code_part = f"\n【最终代码】\n{code[:2000]}\n" if code else ""
    return f"""=== {pid_label} ===
【题面摘要】
{statement}

【解题过程】
{process}
{code_part}
【判题结论】{verdict}（score={score}）
"""

# ---- 1. 验证样本（18条，分6组每组3条）----
samples = json.load(open("process_samples/samples.json", encoding="utf-8"))
problems = json.load(open("problems.json", encoding="utf-8"))

os.makedirs("manual_eval_package", exist_ok=True)

# 读取题面前800字
def get_statement(pid):
    meta = problems.get(pid, {})
    sf = meta.get("statement_file", f"{pid}.md")
    p = os.path.join("statement", sf)
    if os.path.exists(p):
        return open(p, encoding="utf-8", errors="replace").read()[:800]
    return meta.get("note", "")

groups = [samples[i:i+3] for i in range(0, 18, 3)]
for gi, group in enumerate(groups):
    prompt = RUBRIC_HEADER
    prompt += f"以下是第 {gi+1} 组（共 {len(group)} 条）：\n\n"
    for s in group:
        stmt = get_statement(s["problem_id"])
        prompt += make_eval_block(
            s["problem_id"], s["id"], stmt,
            s["process_text"], s.get("judge0_verdict", "WA"),
            "?"
        )
        prompt += "\n"
    fn = f"manual_eval_package/grp{gi+1}_validation.txt"
    open(fn, "w", encoding="utf-8").write(prompt)
    print(f"生成 {fn} （{len(group)} 条样本）")

# ---- 2. 生产题（8道，分2组每组4道）----
runs = [json.loads(l) for l in open("runs/hy3-final.jsonl", encoding="utf-8") if l.strip()]

def read_workspace_file(pid, fname):
    p = os.path.join("workspace_hy3", pid, fname)
    if os.path.exists(p):
        return open(p, encoding="utf-8", errors="replace").read()
    return ""

prod_groups = [runs[:4], runs[4:]]
for gi, group in enumerate(prod_groups):
    prompt = RUBRIC_HEADER
    prompt += f"以下是第 {gi+1} 组生产题（共 {len(group)} 道）：\n\n"
    for r in group:
        pid = r["problem_id"]
        stmt = get_statement(pid)
        process = read_workspace_file(pid, "process.md")
        code = read_workspace_file(pid, "sol.py")
        prompt += make_eval_block(
            pid, pid, stmt, process,
            r["verdict"], r["score"], code
        )
        prompt += "\n"
    fn = f"manual_eval_package/grp{gi+1+6}_production.txt"
    open(fn, "w", encoding="utf-8").write(prompt)
    print(f"生成 {fn} （{len(group)} 道生产题）")

print("\n完成。共生成 8 个提示词文件。")
print("下一步：打开 manual_eval_package/ 目录，逐个复制到 WorkBuddy HY3 对话框。")
print("把 HY3 的回复保存到 manual_eval_package/replies/ 目录，文件名对应 grp1.txt ~ grp8.txt")
