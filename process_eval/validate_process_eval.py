# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 judge0-mcp contributors
#
# validate_process_eval.py — 过程评估有效性验证（任务二硬性两条）
# ==========================================================================
# 计算并报告:
#   1) 定位准确率   : 在「确有错误」的样本上，首个错误步骤判对的比例
#   2) 误报率       : 在「过程本正确」的样本上，被错判为错误的比例
#   3) 巧合通过召回 : 在「答案对但过程不成立」样本上，被识别出的比例
#   4) 判别力       : 好/中(应判有效) vs 差/巧合(应判无效) 的整体区分准确率
#
# 用法（仓库根目录下执行，脚本位于 process_eval/）:
#   # 方式 A：直接对 18 条验证样本做离线验证（用按样本 id 存的预测文件，无需 LLM/Judge0）
#   python process_eval/validate_process_eval.py --samples process_samples/samples.json \
#       --predictions results/sample_predictions.jsonl
#   注：results/judgments.jsonl 是 8 道生产题判定（按 problem_id+submit_index 存），
#       键与 samples.json 的 id 不对齐，不能用于样本验证；样本验证务必用 sample_predictions.jsonl。
#
#   # 方式 B：直接对样本集跑评估器（需配置 LLM 端点）
#   python process_eval/validate_process_eval.py --samples process_samples/samples.json --self-eval
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from process_eval import evaluate_one, LLMJudge, ERROR_TYPES  # noqa: E402


def load_jsonl(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def locate_pred(pred):
    """从判定结果取预测的首错步骤（优先 llm，否则 None）。"""
    if isinstance(pred, dict):
        v = pred.get("first_error_step")
        if v is None and "llm" in pred:
            v = pred["llm"].get("first_error_step")
        return v
    return None


def valid_pred(pred):
    if isinstance(pred, dict):
        v = pred.get("process_valid")
        if v is None and "llm" in pred:
            v = pred["llm"].get("process_valid")
        return v
    return None


def coinc_pred(pred):
    if isinstance(pred, dict):
        v = pred.get("coincidence_pass")
        if v is None and "llm" in pred:
            v = pred["llm"].get("coincidence_pass")
        return v
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", required=True)
    ap.add_argument("--predictions", default="results/judgments.jsonl", help="process_eval 产出的 judgments.jsonl")
    ap.add_argument("--self-eval", action="store_true", help="直接对样本跑评估器（需 LLM）")
    ap.add_argument("--statement-dir", default="")
    ap.add_argument("--problems", default="problems.json")
    args = ap.parse_args()

    samples = json.load(open(args.samples, encoding="utf-8"))
    if isinstance(samples, dict):
        samples = samples.get("samples", samples)

    # 取得预测
    preds = {}
    if args.self_eval:
        judge = LLMJudge()
        problems = json.load(open(args.problems, encoding="utf-8"))
        for s in samples:
            res = evaluate_one(judge, s["problem_id"], s["process_text"], "",
                               s.get("judge0_verdict", "WA"), None,
                               read_stmt(args.statement_dir, s["problem_id"], problems))
            preds[s["id"]] = res
    elif args.predictions:
        for j in load_jsonl(args.predictions):
            preds[j.get("id") or (j.get("problem_id"), j.get("submit_index"))] = j
    else:
        print("需提供 --predictions 或 --self-eval")
        sys.exit(1)

    # ---- 统计 ----
    loc_total = loc_hit = 0          # 定位准确率
    fp_total = fp_hit = 0            # 误报率（本正确却判错）
    coin_total = coin_hit = 0        # 巧合通过召回
    coin_false_alarm = 0             # 非巧合却被标巧合
    disc_total = disc_hit = 0        # 判别力

    rows = []
    for s in samples:
        gold = s["gold"]
        pred = preds.get(s["id"]) or {}
        pv = valid_pred(pred)
        pl = locate_pred(pred)
        pc = coinc_pred(pred)
        gv = gold["process_valid"]
        gl = gold["first_error_step"]
        gc = gold["coincidence_pass"]

        # 定位准确率：gold 确有错
        if gl is not None:
            loc_total += 1
            if pl == gl:
                loc_hit += 1
        # 误报率：gold 本正确
        if gv is True:
            fp_total += 1
            if pv is False:
                fp_hit += 1
        # 巧合通过召回 / 误报
        if gc is True:
            coin_total += 1
            if pc is True:
                coin_hit += 1
        else:
            if pc is True:
                coin_false_alarm += 1
        # 判别力：good/medium -> 应 valid；bad/coincidence -> 应 invalid
        expect_valid = (s["category"] in ("good", "medium"))
        disc_total += 1
        if (pv is True) == expect_valid:
            disc_hit += 1

        rows.append({
            "id": s["id"], "cat": s["category"], "gold_valid": gv, "pred_valid": pv,
            "gold_step": gl, "pred_step": pl, "gold_coin": gc, "pred_coin": pc,
            "match_valid": (pv == gv),
        })

    def pct(a, b):
        return f"{a}/{b} = {100.0*a/b:.1f}%" if b else "n/a"

    print("=" * 64)
    print("过程评估有效性验证报告")
    print("=" * 64)
    print(f"样本总数            : {len(samples)}")
    print(f"定位准确率          : {pct(loc_hit, loc_total)}   (确有错样本中首错步骤判对)")
    print(f"误报率              : {pct(fp_hit, fp_total)}   (本正确却判错)")
    print(f"巧合通过召回        : {pct(coin_hit, coin_total)}   (巧合样本被识别)")
    print(f"巧合误报(非巧合标奇): {coin_false_alarm}")
    print(f"判别力(好/中 vs 差) : {pct(disc_hit, disc_total)}")
    print("-" * 64)
    print("逐样本明细:")
    for r in rows:
        flag = "OK" if r["match_valid"] else "XX"
        print(f"  [{flag}] {r['id']:<24} cat={r['cat']:<12} "
              f"valid g={r['gold_valid']}/{r['pred_valid']} "
              f"step g={r['gold_step']}/{r['pred_step']} coin g={r['gold_coin']}/{r['pred_coin']}")
    print("=" * 64)


def read_stmt(statement_dir, pid, problems):
    if not statement_dir:
        return ""
    meta = problems.get(pid, {})
    p = os.path.join(statement_dir, meta.get("statement_file", f"{pid}.md"))
    if os.path.exists(p):
        with open(p, encoding="utf-8", errors="replace") as f:
            return f.read()[:800]
    return ""


if __name__ == "__main__":
    main()
