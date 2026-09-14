# -*- coding: utf-8 -*-
"""解析 WorkBuddy HY3 的回复，生成正式的 sample_predictions.jsonl 和 judgments.jsonl。

用法：
  1. 把 HY3 对 grp1~grp6 的回复保存到 manual_eval_package/replies/grp1.txt ~ grp6.txt
  2. 把 HY3 对 grp7~grp8 的回复保存到 manual_eval_package/replies/grp7.txt ~ grp8.txt
  3. 运行：python parse_workbuddy_replies.py
"""
import json, os, re, glob

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REPLIES_DIR = "manual_eval_package/replies"

def parse_reply(text):
    """从 HY3 回复文本中提取所有 JSON 对象。"""
    results = []
    # 尝试找 {...} 块（可能跨多行）
    # 用正则匹配最外层 JSON
    decoder = json.JSONDecoder()
    idx = 0
    while idx < len(text):
        # 找下一个 {
        brace = text.find("{", idx)
        if brace == -1:
            break
        try:
            obj, end = decoder.raw_decode(text, brace)
            if isinstance(obj, dict) and "id" in obj:
                results.append(obj)
            idx = end
        except json.JSONDecodeError:
            idx = brace + 1
    return results

# ---- 1. 解析验证样本回复（grp1~grp6）----
print("=== 解析验证样本回复 ===")
all_preds = []
for i in range(1, 7):
    fn = os.path.join(REPLIES_DIR, f"grp{i}.txt")
    if not os.path.exists(fn):
        print(f"  [跳过] {fn} 不存在")
        continue
    text = open(fn, encoding="utf-8").read()
    objs = parse_reply(text)
    print(f"  grp{i}.txt: 解析出 {len(objs)} 条判定")
    all_preds.extend(objs)

# 写入 sample_predictions.jsonl
if all_preds:
    with open("results/sample_predictions.jsonl", "w", encoding="utf-8") as f:
        for p in all_preds:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(f"\n写入 results/sample_predictions.jsonl: {len(all_preds)} 条")
else:
    print("\n[警告] 未解析到任何验证样本判定，请检查回复文件格式")

# ---- 2. 解析生产题回复（grp7~grp8）----
print("\n=== 解析生产题回复 ===")
all_prod = []
for i in range(7, 9):
    fn = os.path.join(REPLIES_DIR, f"grp{i}.txt")
    if not os.path.exists(fn):
        print(f"  [跳过] {fn} 不存在")
        continue
    text = open(fn, encoding="utf-8").read()
    objs = parse_reply(text)
    print(f"  grp{i}.txt: 解析出 {len(objs)} 条判定")
    all_prod.extend(objs)

# 写入 judgments.jsonl 和 manual_judgments.jsonl
if all_prod:
    # 读取 runs 以关联 verdict/score
    runs = [json.loads(l) for l in open("runs/hy3-final.jsonl", encoding="utf-8") if l.strip()]
    runs_by_id = {r["problem_id"]: r for r in runs}

    judgments_lines = []
    manual_lines = []
    for idx, p in enumerate(all_prod):
        pid = p.get("id")
        run = runs_by_id.get(pid, {})
        j = {
            "problem_id": pid,
            "verdict": run.get("verdict", "?"),
            "score": run.get("score"),
            "process_valid": p.get("process_valid"),
            "first_error_step": p.get("first_error_step"),
            "error_type": p.get("error_type"),
            "coincidence_pass": p.get("coincidence_pass"),
            "submit_index": idx,
        }
        judgments_lines.append(json.dumps(j, ensure_ascii=False))
        manual_lines.append(json.dumps({
            "problem_id": pid, "submit_index": idx,
            "llm": {k: p.get(k) for k in ["process_valid","first_error_step","error_type","coincidence_pass","confidence","rationale"]}
        }, ensure_ascii=False))

    open("results/judgments.jsonl", "w", encoding="utf-8").write("\n".join(judgments_lines) + "\n")
    open("results/manual_judgments.jsonl", "w", encoding="utf-8").write("\n".join(manual_lines) + "\n")
    print(f"\n写入 results/judgments.jsonl: {len(judgments_lines)} 条")
    print(f"写入 results/manual_judgments.jsonl: {len(manual_lines)} 条")
else:
    print("\n[警告] 未解析到任何生产题判定")

# ---- 3. 运行验证 ----
print("\n=== 运行有效性验证 ===")
os.system('python process_eval/validate_process_eval.py --samples process_samples/samples.json --predictions results/sample_predictions.jsonl')
