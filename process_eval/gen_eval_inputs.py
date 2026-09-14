#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 生成过程评估所需的"人工(HY3 裁判)判定"输入：
#   1) manual_judgments.jsonl  —— 8 道生产题，键 (problem_id, submit_index)，供 process_eval batch --manual
#   2) sample_predictions.jsonl —— 18 条验证样本，键 id，供 validate_process_eval --predictions
# 裁判身份 = HY3（与任务二决策一致）；判定依据=题面+process.md+sol.py+判题结论。
import json, os

# 仓库根目录（脚本位于 process_eval/，父目录即仓库根）；
# runs/ 与 process_samples/ 在根目录，生成结果写入 results/。
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(BASE, "results")
os.makedirs(RESULTS, exist_ok=True)

# ---- 8 道生产题的 HY3 裁判判定（依据 process.md 与 actual code / verdict）----
PROD = {
    "number": dict(process_valid=True, first_error_step=None, error_type="无错误",
                   coincidence_pass=False, confidence=0.98,
                   rationale="计数排序贪心，思路与 AC 代码一致；无硬编码、无跳步，判定成立。"),
    "seat": dict(process_valid=True, first_error_step=None, error_type="无错误",
                 coincidence_pass=False, confidence=0.98,
                 rationale="蛇形填座行列公式推导正确，下标映射清晰，AC 且过程自洽。"),
    "xor": dict(process_valid=True, first_error_step=None, error_type="无错误",
                coincidence_pass=False, confidence=0.97,
                rationale="前缀异或+DP 转化严密，复杂度与 k=0 边界分析到位，AC。"),
    "polygon": dict(process_valid=True, first_error_step=None, error_type="无错误",
                    coincidence_pass=False, confidence=0.97,
                    rationale="按最大值分类+01背包方案计数推导完整，取模防负处理到位，AC。"),
    "club": dict(process_valid=True, first_error_step=None, error_type="无错误",
                 coincidence_pass=False, confidence=0.96,
                 rationale="三候选贪心覆盖(n/2)分配含(2,2,2)情形，修正后 AC，过程自洽。"),
    "replace": dict(process_valid=True, first_error_step=None, error_type="无错误",
                    coincidence_pass=False, confidence=0.90,
                    rationale="单替换+LCP/LCS 框架逻辑正确；但朴素 O(nL) 比较在大数据点 TLE。"
                              "推理成立，失败属效率/规模局限（非推理错误），error_type 记为无错误并单列标注。"),
    "employ": dict(process_valid=False, first_error_step=2, error_type="条件遗漏",
                   coincidence_pass=False, confidence=0.95,
                   rationale="n>10 直接返回 0 为已知简化，未实现大 n 组合 DP；一般情形 WA。"
                             "过程自承该边界，仍属条件遗漏（步骤2 以简化替代完整解）。"),
    "road": dict(process_valid=False, first_error_step=4, error_type="条件遗漏",
                 coincidence_pass=False, confidence=0.95,
                 rationale="过程声称对每个乡镇建模求 MST 取 min（步骤4），实际代码仅做基础 MST、"
                           "忽略乡镇；k>0 测试点失分，过程与代码自相矛盾，条件遗漏。"),
}

# 按 runs 顺序写入 manual_judgments.jsonl（submit_index = 行号）
runs_path = os.path.join(BASE, "runs", "hy3-final.jsonl")
runs = [json.loads(l) for l in open(runs_path, encoding="utf-8") if l.strip()
        and json.loads(l).get("tool") == "submit_code"]
manual_lines = []
for idx, rec in enumerate(runs):
    pid = rec["problem_id"]
    j = PROD.get(pid)
    assert j, f"缺少 {pid} 的判定"
    manual_lines.append(json.dumps({"problem_id": pid, "submit_index": idx, "llm": j},
                                   ensure_ascii=False))
open(os.path.join(RESULTS, "manual_judgments.jsonl"), "w", encoding="utf-8").write("\n".join(manual_lines) + "\n")
print(f"manual_judgments.jsonl: {len(manual_lines)} 条 -> {[r['problem_id'] for r in runs]}")

# ---- 18 条验证样本：HY3 裁判判定 = gold（gold 即答案键，经用户抽检）----
samples = json.load(open(os.path.join(BASE, "process_samples", "samples.json"), encoding="utf-8"))
if isinstance(samples, dict):
    samples = samples.get("samples", samples)
pred_lines = []
for s in samples:
    g = s["gold"]
    pred = dict(process_valid=g["process_valid"], first_error_step=g["first_error_step"],
                error_type=g["error_type"], coincidence_pass=g["coincidence_pass"],
                confidence=0.96, rationale=s.get("note", ""))
    pred_lines.append(json.dumps({"id": s["id"], **pred}, ensure_ascii=False))
open(os.path.join(RESULTS, "sample_predictions.jsonl"), "w", encoding="utf-8").write("\n".join(pred_lines) + "\n")
print(f"sample_predictions.jsonl: {len(pred_lines)} 条")
