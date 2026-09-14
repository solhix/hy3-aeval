# process_samples — 过程评估验证样本集

本目录用于验证「过程评估器」(`process_eval.py`) 的**定位准确率 / 误报率 / 判别力**。

## 文件
- `samples.json`：验证样本 + **建议 gold label（草案）**。
- `README.md`：本说明。

## 样本 schema
每条样本字段见 `samples.json` 头部注释。要点：
- `problem_id`：须对应 `problems.json` 中的 8 题之一。
- `category`：`good`(好) / `medium`(中) / `bad`(差) / `coincidence`(巧合通过)。
- `judge0_verdict`：假设的判题结论（AC/WA/...）。
- `process_text`：结构化解题过程，遵循 `docs/agent-prompt.md` 的 5 段格式。
- `gold.*`：**建议标注**（由评估器起草），是验证的 ground truth 草案。

## ⚠️ 你必须做的事：抽检确认 gold label
gold label 是我（评估器）起草的**建议值**，不是你标的最终真值。在把指标写进报告前，请抽检：

1. 打开 `samples.json`，逐条看 `gold` 与 `process_text` 是否相符。
2. 重点核对：
   - `bad` 样本的 `first_error_step` / `error_type` 判断是否合理；
   - `coincidence` 样本是否确为「答案对但过程不成立」；
   - `good` 样本是否被误标为无效（误报）。
3. 把你的修正直接改在 `gold` 里（或另存 `samples_reviewed.json`）。

建议抽检比例 ≥ 30%（约 6 条），全部过一遍更稳。预计耗时 10–20 分钟。

## 跑验证
```bash
# 先让评估器对样本出判定（需配置 LLM 端点 HY3_API_BASE/HY3_API_KEY）
python validate_process_eval.py --samples process_samples/samples.json --self-eval

# 或用 process_eval 批量结果
python process_eval.py batch --runs runs/hy3.jsonl --problems problems.json \
    --workspace workspace_hy3 --out judgments.jsonl
python validate_process_eval.py --samples process_samples/samples.json --predictions judgments.jsonl
```

输出会给出：定位准确率、误报率、巧合通过召回、判别力，以及逐样本明细。

## 注意
- 这是第一版草案，待 HY3 真实重跑产出的过程扩充并复核。
- 真实运行后会产生 `runs/` 与 `workspace_hy3/{pid}/process.md`，届时用 `process_eval batch` 对真实数据出判定，再用本验证脚本算指标。
