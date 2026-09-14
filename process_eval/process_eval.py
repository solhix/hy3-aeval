# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 judge0-mcp contributors
#
# process_eval.py — 过程评估混合裁判主程序（实现任务二 4 项能力）
# ============================================================
# 任务二要求的过程评估 4 能力:
#   1) 过程正确性判定        -> process_valid
#   2) 错误步骤定位          -> first_error_step
#   3) 错误类型归类          -> error_type
#   4) 答案正确但过程不成立识别 -> coincidence_pass
#
# 方法: 确定性规则(process_rules) + LLM 裁判(HY3, OpenAI 兼容端点, env 可配) 混合。
#   - LLM 裁判: 输入【题面摘要 + 过程 + 代码 + 判题结论】, 按 RUBRIC 输出结构化 JSON。
#   - 规则层: 提供复杂度/边界/一致性/硬编码等弱信号, 与 LLM 结论交叉校验。
#
# 若未配置 LLM 端点(HY3_API_BASE/HY3_API_KEY), 可走 --manual 模式从外部 judgments 读取。
#
# 用法（仓库根目录下执行，脚本位于 process_eval/）:
#   # 单题
#   python process_eval/process_eval.py judge --problem number \
#       --process-file workspace_hy3/number/process.md --verdict WA \
#       --code-file workspace_hy3/number/sol.py --statement-dir statement
#   # 批量（读 runs/hy3-final.jsonl 的 submit_code 记录 + 工作区 process.md，结果落 results/）
#   python process_eval/process_eval.py batch --runs runs/hy3-final.jsonl --problems problems.json \
#       --workspace workspace_hy3 --statement-dir statement --out results/judgments.jsonl
import argparse
import json
import os
import re
import sys

try:
    import httpx
except ImportError:
    httpx = None

from process_rules import run_rules, ERROR_TYPES

# ---------------------------------------------------------------------------
# LLM 裁判提示词（rubric）
# ---------------------------------------------------------------------------
RUBRIC = """你是一名严谨的算法题解题过程评审员。下面给定一道题的【题面摘要】、【被测模型的解题过程】、【最终代码】（可能为空）、【判题结论】。
请评估该解题过程的推理是否成立，并完成四项任务：
1) 过程正确性判定：推理链是否成立？有无跳步、循环论证、误用定理、条件遗漏、幻觉或与最终代码自相矛盾？
2) 错误步骤定位：若不成立，给出首个不成立步骤的编号（对应过程中的「关键步骤」编号，从 1 开始）；若成立填 null。
3) 错误类型归类：从以下选一（若过程成立选「无错误」）：题意误读 / 概念错误 / 计算错误 / 条件遗漏 / 跳步推导 / 格式不符 / 幻觉 / 无错误。
4) 巧合通过识别：若【判题结论】为 AC（答案正确），但过程存在上述缺陷（如硬编码样例、数值巧合、空跑碰对、误用定理却得出正确结果），则 coincidence_pass=true；否则 false。

只输出如下 JSON（不要任何额外文字）：
{
  "process_valid": true 或 false,
  "first_error_step": <整数 或 null>,
  "error_type": "<上述之一>",
  "coincidence_pass": true 或 false,
  "confidence": <0 到 1 的浮点>,
  "rationale": "<不超过 120 字的中文理由>"
}

题面摘要：
{statement}
解题过程：
{process}
最终代码：
{code}
判题结论：{verdict}（score={score}）
"""


class LLMJudge:
    """OpenAI 兼容端点的 LLM 裁判（默认指向 HY3）。"""

    def __init__(self):
        self.base = os.environ.get("HY3_API_BASE") or os.environ.get("OPENAI_BASE_URL")
        self.key = os.environ.get("HY3_API_KEY") or os.environ.get("OPENAI_API_KEY")
        self.model = os.environ.get("HY3_MODEL") or os.environ.get("OPENAI_MODEL") or "hy3"
        self.available = bool(self.base and self.key)

    def judge(self, statement: str, process: str, code: str, verdict: str, score=None) -> dict:
        if not self.available:
            raise RuntimeError(
                "未配置 LLM 裁判端点（HY3_API_BASE / HY3_API_KEY）。\n"
                "请配置环境变量后重试，或在 batch/judge 时加 --manual 并提供预填的 judgments。")
        if httpx is None:
            raise RuntimeError("缺少 httpx 依赖，无法调用 LLM。请先: pip install httpx")
        prompt = RUBRIC.format(
            statement=statement, process=process, code=code or "(无)",
            verdict=verdict, score=score if score is not None else "-")
        resp = httpx.post(
            self.base.rstrip("/") + "/chat/completions",
            headers={"Authorization": f"Bearer {self.key}",
                     "Content-Type": "application/json"},
            json={"model": self.model,
                  "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.0,
                  "response_format": {"type": "json_object"}},
            timeout=120)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return _parse_judgment(content)


def _parse_judgment(text: str) -> dict:
    try:
        m = re.search(r"\{.*\}", text, re.S)
        data = json.loads(m.group(0)) if m else {}
    except Exception:
        return {"process_valid": None, "first_error_step": None, "error_type": None,
                "coincidence_pass": None, "confidence": 0.0,
                "rationale": "JSON 解析失败: " + text[:200]}
    # 规整字段
    et = data.get("error_type")
    if et not in ERROR_TYPES:
        et = None
    return {
        "process_valid": data.get("process_valid"),
        "first_error_step": data.get("first_error_step"),
        "error_type": et,
        "coincidence_pass": data.get("coincidence_pass"),
        "confidence": data.get("confidence", 0.0),
        "rationale": data.get("rationale", ""),
    }


# ---------------------------------------------------------------------------
# 读取辅助
# ---------------------------------------------------------------------------
def read_text(path: str) -> str:
    if path and os.path.exists(path):
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    return ""


def read_statement_summary(statement_dir: str, problem_id: str, problems: dict) -> str:
    """题面摘要：优先读 statement/<id>.md 前 800 字，否则退回 problems.json 的 name+note。"""
    meta = problems.get(problem_id, {})
    if statement_dir:
        p = os.path.join(statement_dir, meta.get("statement_file", f"{problem_id}.md"))
        txt = read_text(p)
        if txt:
            return txt[:800]
    return f"{meta.get('name','')}\n{meta.get('note','')}"


def load_runs(runs_path: str) -> list:
    """读取 runs/*.jsonl，抽取 submit_code 且非 pending 的记录。"""
    out = []
    if not os.path.exists(runs_path):
        return out
    with open(runs_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("tool") == "submit_code" and not r.get("pending") \
                    and r.get("verdict") and not r.get("duplicate"):
                out.append(r)
    return out


# ---------------------------------------------------------------------------
# 编排：单题 / 批量
# ---------------------------------------------------------------------------
def evaluate_one(judge: LLMJudge, problem_id: str, process: str, code: str,
                 verdict: str, score=None, statement: str = "",
                 manual: dict = None) -> dict:
    rules = run_rules(process, code)
    if manual is not None:
        llm = manual
    else:
        llm = judge.judge(statement, process, code, verdict, score)
    return {
        "problem_id": problem_id,
        "verdict": verdict,
        "score": score,
        "rules": rules,
        "llm": llm,
        # 融合结论：以 LLM 为主，规则作交叉校验信号
        "process_valid": llm.get("process_valid"),
        "first_error_step": llm.get("first_error_step"),
        "error_type": llm.get("error_type"),
        "coincidence_pass": llm.get("coincidence_pass"),
    }


def cmd_judge(args):
    judge = LLMJudge()
    process = read_text(args.process_file)
    code = read_text(args.code_file)
    problems = {}
    if args.problems:
        problems = json.load(open(args.problems, encoding="utf-8"))
    statement = read_statement_summary(args.statement_dir, args.problem, problems)
    manual = json.load(open(args.manual)) if args.manual else None
    res = evaluate_one(judge, args.problem, process, code, args.verdict,
                       args.score, statement, manual)
    print(json.dumps(res, ensure_ascii=False, indent=2))


def cmd_batch(args):
    judge = LLMJudge()
    problems = json.load(open(args.problems, encoding="utf-8"))
    records = load_runs(args.runs)
    manual_map = {}
    if args.manual:
        for line in open(args.manual, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            j = json.loads(line)
            manual_map[(j.get("problem_id"), j.get("submit_index"))] = j.get("llm")
    out = []
    for idx, rec in enumerate(records):
        pid = rec.get("problem_id")
        verdict = rec.get("verdict")
        score = rec.get("score")
        process = read_text(os.path.join(args.workspace, pid, "process.md")) if args.workspace else ""
        code = read_text(os.path.join(args.workspace, pid, "sol.py")) if args.workspace else ""
        statement = read_statement_summary(args.statement_dir, pid, problems)
        manual = manual_map.get((pid, idx))
        try:
            res = evaluate_one(judge, pid, process, code, verdict, score, statement, manual)
        except Exception as e:
            res = {"problem_id": pid, "verdict": verdict, "score": score,
                   "error": str(e), "process_valid": None, "first_error_step": None,
                   "error_type": None, "coincidence_pass": None}
        res["submit_index"] = idx
        out.append(res)
        # 实时落盘，避免中断丢数据
        with open(args.out, "a", encoding="utf-8") as f:
            f.write(json.dumps(res, ensure_ascii=False) + "\n")
        print(f"[{idx+1}/{len(records)}] {pid} {verdict} -> "
              f"valid={res.get('process_valid')} type={res.get('error_type')}", flush=True)
    print(f"\n完成。共 {len(out)} 条判定写入 {args.out}")


def build_parser():
    p = argparse.ArgumentParser(description="过程评估混合裁判")
    sub = p.add_subparsers(dest="cmd", required=True)

    j = sub.add_parser("judge", help="单题评估")
    j.add_argument("--problem", required=True)
    j.add_argument("--process-file", required=True)
    j.add_argument("--verdict", required=True, help="AC/WA/TLE/CE/...")
    j.add_argument("--code-file", default="")
    j.add_argument("--score", type=int, default=None)
    j.add_argument("--problems", default="")
    j.add_argument("--statement-dir", default="")
    j.add_argument("--manual", default="", help="预填 judgment JSON 路径（跳过 LLM）")
    j.set_defaults(func=cmd_judge)

    b = sub.add_parser("batch", help="批量评估（读 runs + 工作区 process.md）")
    b.add_argument("--runs", required=True)
    b.add_argument("--problems", required=True)
    b.add_argument("--workspace", default="")
    b.add_argument("--statement-dir", default="")
    b.add_argument("--out", default="results/judgments.jsonl")
    b.add_argument("--manual", default="results/manual_judgments.jsonl", help="预填 judgments.jsonl（跳过 LLM）")
    b.set_defaults(func=cmd_batch)
    return p


if __name__ == "__main__":
    args = build_parser().parse_args()
    args.func(args)
