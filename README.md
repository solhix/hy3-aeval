# hy3-aeval

> 仓库地址：https://github.com/solhix/hy3-aeval.git

**用混元大模型（HY3）单模型对 CSP-J/S 2025 复赛 8 道算法题做「过程评估与错误定位」** 的评测系统（对应实战任务书「任务二：可验证场景——过程评估与错误定位」）。

在「答案是否正确」的判题之外，额外评估模型的**解题过程**：过程正确性判定、错误步骤定位、错误类型归类、以及「答案对但过程不成立」识别，并用「定位准确率 + 误报率（人工抽检）」做有效性验证。

判题后端使用 [Judge0](https://github.com/judge0/judge0) 评测栈（**需另行部署，不在本仓库内**）。本仓库含过程评估代码、8 道题的题面/参考解、验证样本、评测结果与报告。

## 特性

- **四项过程评估能力**：过程正确性判定 / 错误步骤定位 / 错误类型归类 / 答案对但过程不成立识别。
- **真实有效性验证**：18 条带 gold 的验证样本上，HY3 裁判独立评估，给出定位准确率、误报率、巧合召回、判别力。
- **8 道题**：7 道 CSP-J/S 2025 真题 + 1 道自定义环形最大子段和（覆盖巧合通过场景），含 HY3 实际提交结果与过程。
- **demo 视频**：`demo.mp4`（99 秒，带字幕），展示完整解题与过程评估流程。

## 目录结构

```
.
├── README.md                 # 本文件
├── .gitignore
├── .env.example              # 环境变量样例（HY3_API_BASE 等）
├── LICENSE                   # MIT
├── requirements.txt          # Python 依赖（httpx + openai）
├── problems.json             # 8 道题的题库元数据
├── demo.mp4                  # ≤2 分钟演示视频
├── process_eval/             # ★ 过程评估模块（核心代码）
│   ├── process_eval.py        #   混合裁判主程序（4 能力 + 规则/LLM 交叉）
│   ├── process_rules.py       #   确定性规则层（弱信号校验）
│   ├── validate_process_eval.py  # 有效性验证（定位准确率/误报率/巧合召回）
│   ├── run_direct.py         #   直连 Judge0 判题驱动
│   ├── gen_eval_inputs.py     #   生成 manual 判定与样本预测输入
│   ├── gen_circular_data.py  #   circular 题测试数据生成
│   ├── gen_manual_eval_package.py  # WorkBuddy 人工评估工作包生成
│   └── parse_workbuddy_replies.py # WorkBuddy 回复解析
├── results/                  # 评估输出
│   ├── judgments.jsonl       #   8 道生产题判定结果
│   ├── manual_judgments.jsonl#   含理由的判定
│   └── sample_predictions.jsonl # 18 条验证样本的 HY3 预测
├── runs/
│   └── hy3-final.jsonl       # 8 题判题终态
├── process_samples/          # 过程评估验证样本（18 条，带 gold）
│   ├── samples.json
│   └── README.md
├── solutions/                # 8 道题的参考解
├── statement/                # 8 道题题面 Markdown
├── workspace_hy3/             # HY3 解题过程（process.md + sol.py）
├── data/circular/            # circular 题测试数据（20 个测试点）
├── docs/                     # 文档
│   ├── 报告.md               #   完整评测报告
│   ├── 评测结论.md           #   结论摘要
│   └── agent-prompt.md       #   被测模型系统提示词
└── manual_eval_package/      # WorkBuddy 人工评估提示词（8 组）
```

## 前置条件

| 项 | 要求 |
|----|------|
| Python | ≥ 3.10 |
| Judge0 | 可选，仅重跑判题时需要 |
| HY3 端点 | 可选，LLM 裁判模式需要；无端点时用已提交的评估结果 |

## 快速开始（零外部依赖）

```bash
# 安装依赖
pip install -r requirements.txt

# 验证过程评估有效性（使用已提交的 HY3 真实评估结果）
python process_eval/validate_process_eval.py \
    --samples process_samples/samples.json \
    --predictions results/sample_predictions.jsonl
```

输出：
```
定位准确率          : 8/10 = 80.0%
误报率              : 5/8 = 62.5%
巧合通过召回        : 3/3 = 100.0%
判别力              : 13/18 = 72.2%
```

## 过程评估四项能力

`process_eval.py` 输出结构化判定 JSON：

| 字段 | 能力 |
|------|------|
| `process_valid` | 过程正确性判定（推理链是否成立） |
| `first_error_step` | 错误步骤定位（首个不成立步骤编号） |
| `error_type` | 错误类型归类（题意误读/概念错误/计算错误/条件遗漏/跳步推导/格式不符/幻觉/无错误） |
| `coincidence_pass` | 答案对但过程不成立识别 |

## 评测结果速览

- **8 题答案准确率**：5 AC / 2 WA / 1 TLE
- **过程正确率**：4/8 = 50%（4 题过程成立，4 题条件遗漏）
- **巧合通过**：1 题（circular：AC 但过程遗漏环形特性）
- **验证指标**：定位准确率 80%、误报率 62.5%、巧合召回 100%
- 详细分析见 `docs/报告.md`

## 许可证

MIT License，见 [LICENSE](LICENSE)。Judge0 以 Docker 容器独立运行（GPL-3.0，不在本仓库）。
