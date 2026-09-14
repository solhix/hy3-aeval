# hy3-aeval

> 仓库地址：https://github.com/solhix/hy3-aeval.git

**用混元大模型（HY3）单模型对 CSP-J/S 2025 复赛 8 道算法题做「过程评估与错误定位」** 的评测系统（对应实战任务书「任务二：可验证场景——过程评估与错误定位」）。

在「答案是否正确」的判题之外，额外评估模型的**解题过程**：过程正确性判定、错误步骤定位、错误类型归类、以及「答案对但过程不成立」识别，并用「定位准确率 + 误报率（人工抽检）」做有效性验证。

判题后端使用 [Judge0](https://github.com/judge0/judge0) 评测栈（**需另行部署，不在本仓库内**，见下文「环境部署」）。本仓库只含过程评估代码、8 道题的题面/参考解、验证样本与评测报告。

## 特性

- **单模型过程评估**：被测 = 裁判 = HY3（近自评），通过「确定性规则 + LLM 裁判 + 人工抽检」三重交叉缓解偏差。
- **任务书四项能力全覆盖**：过程正确性判定 / 错误步骤定位 / 错误类型归类 / 答案对过程不成立识别。
- **可验证指标**：在 18 条带 gold 的验证样本上给出定位准确率、误报率、巧合通过召回、判别力。
- **8 道真题**：CSP-J/S 2025 复赛真题题面与参考解（含 HY3 实际提交结果与过程）。
- **零引擎耦合**：评测代码通过 HTTP 直连本地 Judge0，仓库本身不含 Judge0 部署包。

## 目录结构

```
.
├── README.md                 # 本文件
├── .gitignore                # 忽略运行产物（runs/ data/ workspace_hy3/ 等）
├── LICENSE                   # MIT
├── requirements.txt          # Python 依赖（httpx + openai）
├── problems.json             # 8 道题的题库元数据（评测材料，纳入版本库）
├── process_eval/             # ★ 过程评估模块（核心代码）
│   ├── process_eval.py       #   混合裁判主程序（4 能力 + 规则/LLM 交叉）
│   ├── process_rules.py      #   确定性规则层（弱信号校验）
│   ├── validate_process_eval.py  # 有效性验证（定位准确率/误报率/巧合召回）
│   ├── run_direct.py         #   直连 Judge0 判题驱动（产出 8 题 one-shot 终态）
│   └── gen_eval_inputs.py    #   生成 manual 判定与样本预测输入
├── results/                  # 评估输出（committed 作为证据）
│   ├── judgments.jsonl       #   process_eval 批量判定结果
│   ├── manual_judgments.jsonl#   HY3 对 8 道生产题的裁判判定
│   └── sample_predictions.jsonl # 18 条验证样本的预测
├── process_samples/          # 过程评估验证样本（18 条，带 gold）
│   ├── samples.json
│   └── README.md
├── solutions/                # 8 道题的参考解（HY3 实际提交代码）
│   ├── number.cpp  seat.cpp  xor.cpp  polygon.cpp
│   ├── club.cpp   replace.cpp  employ.cpp  road.cpp
├── statement/                # 8 道题题面 Markdown（评测材料）
│   ├── number.md  seat.md  xor.md  polygon.md
│   ├── club.md   replace.md  employ.md  road.md
├── docs/                     # 文档
│   ├── 报告.md               #   评测报告（任务二完成情况）
│   ├── 评测结论.md           #   结论摘要
│   └── agent-prompt.md       #   被测模型系统提示词（含解题过程输出规范）
└── （运行时生成，不入版本库）
    ├── runs/hy3-final.jsonl  #   run_direct 产出的 8 题终态
    ├── workspace_hy3/<id>/   #   HY3 结构化解题过程（process.md + sol.py）
    └── data/<id>/            #   隐藏测试数据（需自行准备）
```

> **题面与隐藏数据**：`statement/*.md` 已纳入版本库；隐藏测试数据 `data/` 与样例压缩包 `statement/*.zip` 因版权/体积原因不入库（`.gitignore` 排除），由使用者自行准备。

## 前置条件

| 项 | 要求 |
|----|------|
| Python | ≥ 3.10（验证环境为 CPython 3.13） |
| Judge0 | 一个可访问的 Judge0 CE 1.13.1 实例（默认 `http://localhost:2358`） |
| HY3 端点 | 过程评估的 LLM 裁判需要 HY3 的 OpenAI 兼容端点（`HY3_API_BASE` / `HY3_API_KEY`）；无端点时可用 `--manual` 走预填判定 |

## 环境部署

### 1. 准备 Judge0 后端（独立于本仓库）

本仓库不含 Judge0 部署包。若需自建，参考 [Judge0 官方文档](https://github.com/judge0/judge0) 用 Docker 启动：

```bash
docker run -d --name judge0 -p 2358:2358 --memory 1g \
  -e CLASSDOWNLOAD_TIMEOUT=15 judge0/judge0:1.13.1
```

验证：

```bash
curl -s http://localhost:2358/about      # 版本信息
curl -s http://localhost:2358/languages  # 语言列表
```

### 2. 创建 Python 环境

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. 准备题库与数据（如需重跑）

| 材料 | 放置位置 | 说明 |
|------|----------|------|
| 题库元数据 | `problems.json` | 已在仓库内（8 题定义） |
| 题面 | `statement/<id>.md` | 已在仓库内 |
| 隐藏测试数据 | `data/<id>/` | 需自行准备 `<id>1.in` / `<id>1.ans` …（编号 1..test_point_count） |

## 过程评估模块（任务二）

覆盖任务书四项能力，并以「定位准确率 + 误报率」做有效性验证。

### 相关文件

| 文件 | 作用 |
|------|------|
| `docs/agent-prompt.md` | 被测模型系统提示词；含「解题过程输出规范」，强制模型把结构化解题过程（题意理解 / 算法思路 / 复杂度分析 / 边界处理 / 关键步骤）写入 `workspace_hy3/{pid}/process.md` |
| `process_eval/run_direct.py` | 直连 Judge0 的判题驱动，产出每题 one-shot 终态到 `runs/hy3-final.jsonl`，并把代码落盘到 `workspace_hy3/{pid}/sol.py` 供规则层校验 |
| `process_eval/process_rules.py` | 确定性规则层：复杂度声明 / 边界提及 / 算法–代码一致性 / 硬编码样例 / 占位 等弱信号校验 |
| `process_eval/process_eval.py` | 混合裁判主程序（LLM 裁决 + 规则交叉）：实现 4 项能力，`batch` 产出 `results/judgments.jsonl`；支持 `--manual`（无 LLM 端点时由模型/人工填判定）与 LLM 模式（`HY3_API_BASE` / `HY3_API_KEY`） |
| `process_eval/validate_process_eval.py` | 在 18 条带 gold 的验证样本上计算定位准确率 / 误报率 / 巧合召回 / 判别力 |
| `process_samples/samples.json` | 18 条验证样本（good 8 / bad 8 / coincidence 2），附 gold 答案键，供人工抽检 |

### 与任务书四项能力对应

`process_eval.py` 的判定 JSON 含：`process_valid`（过程正确性判定）、`first_error_step`（错误步骤定位）、
`error_type`（错误类型归类：题意误读 / 概念错误 / 计算错误 / 条件遗漏 / 跳步推导 / 格式不符 / 幻觉 / 无错误）、
`coincidence_pass`（答案对但过程不成立识别）。

### 运行方式（在仓库根目录执行）

> 所有命令均以**仓库根目录**为工作目录运行（脚本用相对路径读取 `problems.json` / `statement/` / `results/` 等）。
> 依赖：`pip install -r requirements.txt`（仅需 `httpx` + `openai`）。

#### A. 离线演示 / 录屏（零外部依赖，必定可跑，推荐）

只依赖仓库内已有文件，无需 Judge0、无需 HY3 端点、无需测试数据：

```bash
# 1) 对 18 条带 gold 的验证样本计算四项指标（已验证复现 定位100%/误报0%/巧合100%/判别100%）
python process_eval/validate_process_eval.py \
    --samples process_samples/samples.json \
    --predictions results/sample_predictions.jsonl

# 2) 单题结构化判定演示（--manual 直接给判定，跳过 LLM）
python process_eval/process_eval.py judge --problem number \
    --process-file <过程md> --verdict AC --code-file <代码文件> \
    --problems problems.json --statement-dir statement \
    --manual <预填判定json>
```

- `process_samples/samples.json`：18 条 `good/bad/medium/coincidence` 样本，每条含 `process_text`、`code`、Judge0 `verdict` 与 `gold`。
- `results/sample_predictions.jsonl`：18 条样本的预测判定（键为样本 `id`，与 `samples.json` 对齐）。

#### B. 端到端重跑（需外部资源，录屏前先备好）

完整链路需要三样**不在本仓库**的资源：①本地 Judge0（http://localhost:2358）；②`data/<题>/` 真实测试数据；③（走 LLM 裁判时）HY3 端点环境变量。

```bash
# 1) 直连 Judge0 跑 8 题，产出 runs/hy3-final.jsonl + workspace_hy3/（需 Judge0 + data/）
python process_eval/run_direct.py --problems problems.json --solutions-dir solutions --workspace workspace_hy3

# 2) 生成人工/裁判判定输入（需 runs/hy3-final.jsonl）
python process_eval/gen_eval_inputs.py

# 3) 过程评估批量：--manual 用预填判定；配置 HY3_API_BASE/HY3_API_KEY 后可去掉 --manual 走 LLM 裁判
python process_eval/process_eval.py batch --runs runs/hy3-final.jsonl --problems problems.json \
    --workspace workspace_hy3 --statement-dir statement --out results/judgments.jsonl \
    --manual results/manual_judgments.jsonl

# 4) 验证（注意：生产判定 judgments.jsonl 按 submit_index 存，样本验证请用 sample_predictions.jsonl）
python process_eval/validate_process_eval.py --samples process_samples/samples.json \
    --predictions results/sample_predictions.jsonl
#    或实时用 LLM 裁判重判样本（需 HY3 端点）：
python process_eval/validate_process_eval.py --samples process_samples/samples.json --self-eval
```

> **注意（键对齐）**：`validate_process_eval.py` 用样本 `id` 做键。`results/judgments.jsonl` 是 8 道生产题的判定（按 `problem_id+submit_index` 存），**不能直接**用于验证 `samples.json`；样本验证必须传 `--predictions results/sample_predictions.jsonl`。

> **人工抽检要求**：任务书要求误报率「经人工抽检确认」。验证样本 gold 由 HY3 起草，需人工抽检 ≥30% 并确认；
> 抽检结论记入评测报告（见 `docs/报告.md` 第五章）。本次 18 条样本已抽检前 6 条，全部同意 gold。

## 评测结论速览

- **8 题答案准确率**：5 AC / 2 WA / 1 TLE（HY3 one-shot）。
- **过程评估指标**：定位准确率 100%、误报率 0%、巧合通过召回 100%、判别力 100%（在 18 条带 gold 验证样本上）。
- **人工抽检**：18 条样本中抽检 6 条（33%），结论全部同意 gold。
- 详细口径与临界点分析见 `docs/报告.md`。

## 许可证

本仓库以 **MIT License** 发布，完整条款见 [LICENSE](LICENSE)。

### 第三方组件

| 组件 | 许可 | 在本仓库中的形态 |
|------|------|------------------|
| [Judge0](https://github.com/judge0/judge0) | GPL-3.0 | 以 Docker 容器方式独立运行（源码/部署包不在本仓库） |
| [HTTPX](https://github.com/encode/httpx) | BSD-3-Clause | Python 依赖（见 `requirements.txt`） |
| [OpenAI Python SDK](https://github.com/openai/openai-python) | Apache-2.0 | Python 依赖（见 `requirements.txt`，用于 HY3 裁判） |
| 题面 / 样例 / 测试数据 | 归原始出题方所有 | 题面 Markdown 已纳入仓库；隐藏测试数据**不包含**在仓库中 |
