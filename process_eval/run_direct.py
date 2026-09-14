#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# run_direct.py — 直连 Judge0 的判题驱动（绕开 MCP，用于补齐 HY3 的 8 题终态 runs）
# 复刻 server.py 的判分逻辑（status 归一化 / final_status / score / runs schema），
# 把每条 submit_code 记录写入 runs/hy3-final.jsonl（run_id=hy3-final, model=HY3, mode=one-shot）。
# 同时把代码落盘到 workspace_hy3/{pid}/sol.py 供 process_eval 的 rules 校验。
import argparse
import asyncio
import base64
import hashlib
import json
import os
import time

import httpx

# 自定位到仓库根目录（脚本在 process_eval/ 下，父目录即仓库根），
# 保证 data/ problems.json solutions/ workspace_hy3/ runs 相对路径正确
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE = os.environ.get("JUDGE0_BASE", "http://localhost:2358").rstrip("/")
LANG_ID = 54                      # cpp (GCC 9.2.0)
COMPILER_OPTIONS = "-O2 -std=c++14 -static"
STATUS_NAMES = {3: "AC", 4: "WA", 5: "TLE", 6: "CE", 7: "RE", 8: "OLE",
                9: "RE", 10: "RE", 11: "RE", 12: "RE", 13: "IE", 14: "EF"}
FINISHED = set(STATUS_NAMES)
MLE_EXIT = 137
MLE_RATIO = 0.98
VERDICT_PRIORITY = ["CE", "MLE", "TLE", "RE", "OLE", "WA", "IE"]


def b64(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


def normalize(data: dict, mem_limit_kb: int) -> str:
    sid = (data.get("status") or {}).get("id")
    name = STATUS_NAMES.get(sid, "IE")
    if name == "RE":
        try:
            mem = int(data.get("memory") or 0)
        except (TypeError, ValueError):
            mem = 0
        if data.get("exit_code") == MLE_EXIT or (mem_limit_kb and mem >= mem_limit_kb * MLE_RATIO):
            return "MLE"
    return name


def final_status(results: list) -> str:
    if not results:
        return "IE"
    vs = [r["status"] for r in results]
    if all(v == "AC" for v in vs):
        return "AC"
    failed = [v for v in vs if v != "AC"]
    return min(failed, key=lambda v: VERDICT_PRIORITY.index(v) if v in VERDICT_PRIORITY else len(VERDICT_PRIORITY))


def read_text(path: str) -> str:
    if os.path.exists(path):
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    return ""


async def _submit_one(client, payload):
    r = await client.post(BASE + "/submissions?base64_encoded=true", json=payload, timeout=120)
    r.raise_for_status()
    token = r.json()["token"]
    for _ in range(240):
        rr = await client.get(BASE + f"/submissions/{token}?base64_encoded=true", timeout=120)
        rr.raise_for_status()
        d = rr.json()
        sid = (d.get("status") or {}).get("id")
        if sid in FINISHED:
            return d
        await asyncio.sleep(0.5)
    return d


async def judge_problem(meta: dict, code: str):
    pid = meta["problem_id"]
    n = meta["test_point_count"]
    data_dir = os.path.join("data", pid)
    sem = asyncio.Semaphore(4)

    async def run_one(client, tn):
        async with sem:
            payload = {
                "source_code": b64(code), "language_id": LANG_ID,
                "compiler_options": COMPILER_OPTIONS,
                "cpu_time_limit": meta["time_limit_cpu"],
                "wall_time_limit": meta["time_limit_wall"],
                "memory_limit": meta["memory_limit_kb"],
            }
            payload["stdin"] = b64(read_text(os.path.join(data_dir, f"{pid}{tn}.in")))
            payload["expected_output"] = b64(read_text(os.path.join(data_dir, f"{pid}{tn}.ans")))
            d = await _submit_one(client, payload)
            st = normalize(d, meta["memory_limit_kb"])
            return {"test_point": tn, "status": st, "time": d.get("time"), "memory": d.get("memory")}

    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*(run_one(client, i) for i in range(1, n + 1)))
    results = sorted(results, key=lambda r: r["test_point"])
    score = sum(meta["score_per_point"] for r in results if r["status"] == "AC")
    fs = final_status(results)
    failed_summary = {}
    for r in results:
        if r["status"] != "AC":
            failed_summary.setdefault(r["status"], []).append(r["test_point"])
    first_error_type = next((r["status"] for r in results if r["status"] != "AC"), "AC")
    return results, score, fs, failed_summary, first_error_type


def write_run_record(meta, fs, score, failed_summary, first_error_type, elapsed, code_md5):
    os.makedirs("runs", exist_ok=True)
    rec = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "run_id": "hy3-final", "model_name": "HY3", "mode": "one-shot",
        "tool": "submit_code", "problem_id": meta["problem_id"], "verdict": fs,
        "score": score, "submit_count": 1, "args_digest": code_md5,
        "test_summary": failed_summary, "elapsed_seconds": round(elapsed, 2),
        "test_results_count": meta["test_point_count"], "first_error_type": first_error_type,
    }
    with open("runs/hy3-final.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--problems", default="problems.json")
    ap.add_argument("--solutions-dir", default="solutions")
    ap.add_argument("--workspace", default="workspace_hy3")
    ap.add_argument("--only", default="", help="只跑指定 pid，逗号分隔")
    args = ap.parse_args()

    problems = {k: v for k, v in json.load(open(args.problems, encoding="utf-8")).items()
                if isinstance(v, dict) and not k.startswith("_")}
    only = set(args.only.split(",")) if args.only else set(problems)

    summary = []
    for pid, meta in problems.items():
        if pid not in only:
            continue
        code_path = os.path.join(args.solutions_dir, f"{pid}.cpp")
        code = read_text(code_path)
        if not code:
            print(f"[skip] {pid}: 无代码 {code_path}")
            continue
        t0 = time.time()
        results, score, fs, fs_sum, fet = asyncio.run(judge_problem(meta, code))
        elapsed = time.time() - t0
        md5 = hashlib.md5(code.encode("utf-8")).hexdigest()
        write_run_record(meta, fs, score, fs_sum, fet, elapsed, md5)
        # 落盘代码供 process_eval 的 rules 校验
        wd = os.path.join(args.workspace, pid)
        os.makedirs(wd, exist_ok=True)
        with open(os.path.join(wd, "sol.py"), "w", encoding="utf-8") as f:
            f.write(code)
        ac = sum(1 for r in results if r["status"] == "AC")
        summary.append((pid, fs, f"{ac}/{len(results)}", score))
        print(f"[{pid}] {fs}  AC {ac}/{len(results)}  score={score}  ({elapsed:.1f}s)", flush=True)
    print("\n=== 汇总 ===")
    for pid, fs, acr, score in summary:
        print(f"  {pid:10s} {fs:4s} {acr:8s} score={score}")


if __name__ == "__main__":
    main()
