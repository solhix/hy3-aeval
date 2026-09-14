# process_samples — 过程评估验证样本集

本目录用于验证「过程评估器」的定位准确率 / 误报率 / 巧合召回 / 判别力。

## 文件

- `samples.json`：18 条验证样本 + gold 答案键。
- `README.md`：本说明。

## 样本分类

| 分类 | 数量 | 说明 |
|------|------|------|
| good | 8 | 过程正确、答案正确 |
| bad | 7 | 过程有缺陷、答案错误 |
| coincidence | 3 | 过程有缺陷但答案正确（巧合通过） |

## 样本字段

- `problem_id`：对应 `problems.json` 中的题目。
- `category`：good / bad / coincidence。
- `judge0_verdict`：判题结论（AC/WA/TLE）。
- `process_text`：结构化解题过程（5 段式）。
- `gold.*`：人工构造的答案键（ground truth）。

## 跑验证

```bash
# 使用已提交的 HY3 真实评估结果
python process_eval/validate_process_eval.py \
    --samples process_samples/samples.json \
    --predictions results/sample_predictions.jsonl
```

## 人工抽检

已完成两轮：
1. 前 6 条样本人工抽检，全部同意 gold；
2. HY3 裁判误判的 5 条 good 样本已逐条复核（见报告 5.9.2）。
