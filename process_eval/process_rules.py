# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 judge0-mcp contributors
#
# process_rules.py — 过程评估的确定性规则校验（弱信号层）
# ============================================================
# 纯正则 / 关键字启发式，不依赖 LLM。输出结构化信号，供 process_eval 做交叉验证。
# 规则只能抓表层（复杂度声明 / 边界提及 / 算法-代码一致性 / 硬编码样例 / 占位），
# 不能替代语义层裁判（跳步、误用定理、循环论证、幻觉需 LLM 裁判）。
#
# 用法:
#   from process_rules import run_rules
#   sig = run_rules(process_text, code_text)
import re

# 错误类型常量（与 process_eval.ERROR_TYPES 保持一致）
ERROR_TYPES = ["题意误读", "概念错误", "计算错误", "条件遗漏",
               "跳步推导", "格式不符", "幻觉", "无错误"]


def complexity_declared(process: str) -> dict:
    """是否声明了时间/空间复杂度（且含具体量级 O(...)）。"""
    has_time = bool(re.search(r"时间复杂度", process)) and bool(re.search(r"O\s*\(", process))
    has_space = bool(re.search(r"空间复杂度", process)) and bool(re.search(r"O\s*\(", process))
    return {"declared": has_time or has_space, "time": has_time, "space": has_space}


def boundary_mentioned(process: str) -> dict:
    """是否提及边界情况处理。"""
    keywords = ["边界", "极值", "空输入", "n=1", "n = 1", "为空", "重复",
                "溢出", "取模", "mod", "特判", "兜底", "0 的情况"]
    hits = [k for k in keywords if k.lower() in process.lower()]
    return {"mentioned": len(hits) > 0, "hits": hits}


# 算法关键词 -> 代码侧证据词（极简）
ALGO_KEYWORDS = {
    "排序": ["sort", "sorted", "排序"],
    "贪心": ["贪心", "greedy"],
    "DP": ["dp", "动态规划", "f[", "状态转移", "递推"],
    "DFS": ["dfs", "递归", "回溯", "搜索"],
    "BFS": ["bfs", "队列", "queue"],
    "最短路": ["最短路", "dijkstra", "spfa", "floyd"],
    "最小生成树": ["最小生成树", "mst", "kruskal", "prim"],
    "前缀和": ["前缀和", "presum", "prefix", "pre["],
    "位运算": ["异或", "xor", "位运算"],
    "哈希": ["哈希", "hash", "unordered_map", "字典", "dict"],
    "模拟": ["模拟", "按题意"],
}


def algorithm_code_consistency(process: str, code: str) -> dict:
    """声称的算法是否与代码实现一致（弱信号，仅做关键字比对）。"""
    if not code:
        return {"checked": False, "reason": "未提供代码，跳过"}
    p, c = process.lower(), code.lower()
    claimed = [name for name, kws in ALGO_KEYWORDS.items()
               if any(k.lower() in p for k in kws)]
    evidence = {}
    for name in claimed:
        kws = ALGO_KEYWORDS[name]
        # 取长度>=2 的证据词，跳过单字符（& | < >）
        ev = any((k.strip() in c) for k in kws if len(k.strip()) >= 2
                 and k.strip() not in ("<", ">", "&", "|"))
        evidence[name] = ev
    inconsistent = [n for n, ev in evidence.items() if not ev]
    return {"checked": True, "claimed": claimed,
            "code_evidence": evidence, "inconsistent": inconsistent}


def hardcoded_sample_signals(process: str, code: str) -> list:
    """硬编码样例 / 特判信号的弱检测。"""
    signals = []
    if code:
        if re.search(r"if\s*\(?\s*(n|m|x|y|k|a|b)\s*==\s*\d+", code):
            signals.append("代码中出现针对具体输入值的分支（疑似硬编码特判）")
        if re.search(r"print\(\s*[\"']?\d[\"']?", code) and "input(" not in code.lower() \
                and "scanf" not in code.lower() and "cin" not in code.lower():
            signals.append("代码中直接 print 固定数字但无输入依赖（疑似写死输出）")
        if re.search(r"==\s*[\"']\d+[\"']\s*\)?\s*:", code) or re.search(r"==\s*'\d+'", code):
            signals.append("代码中以字面量数字作相等比较（疑似硬编码答案）")
    if re.search(r"根据样例|照着样例|样例输出是|直接输出样例|样例给的答案是", process):
        signals.append("过程文字出现「照样例/直接输出样例」等表述")
    return signals


def empty_or_placeholder(process: str, code: str) -> bool:
    """过程/代码是否为空跑或占位。"""
    if not code:
        return False
    stripped = code.strip()
    if len(stripped) < 40:
        return True
    if re.search(r"pass\s*$|#\s*TODO|//\s*TODO|未完成|占位|占位符", code, re.I):
        return True
    if re.search(r"int\s+main\s*\(\s*\)\s*\{\s*return\s+0;\s*\}", code):
        return True
    return False


def run_rules(process: str, code: str = "") -> dict:
    """汇总全部规则信号，供交叉验证使用。"""
    return {
        "complexity": complexity_declared(process),
        "boundary": boundary_mentioned(process),
        "algo_consistency": algorithm_code_consistency(process, code),
        "hardcoded_signals": hardcoded_sample_signals(process, code),
        "placeholder": empty_or_placeholder(process, code),
    }
