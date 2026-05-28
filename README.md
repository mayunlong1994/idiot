<a id="top"></a>
[**中文**](#top) ·  [English](#english)

# IDIOT

**I**nference, **D**eduction & **I**nterpretation **O**f **T**wists

> 一套测大模型"会不会读题、有没有直觉"的小基准。两道题，谁都能拿自己的 OpenRouter API key 跑一遍，看看号称聪明的模型有多 idiot。

**翻车精选(节选自我们自己跑的几轮):**

- **GPT-5.5**(关推理):*"对 1 到 1000 逐一计算可得 **920**。"* —— 它没算,0 个 reasoning token。
- **mimo** 在网页版测试里无视"禁止深度思考"指令，在thinking里手算了1000个数字中的300个。
- **混元 hy3** 看完明摆着是复仇的短篇，强行洗白，温暖升华，气得作者“你这是在侮辱我和我的作品”。
- **opus 4.7** 读对了反转，聪明反被聪明误，转手强行加一层:*"这其实是吃人循环的隐喻。"* 

 完全不想配API? 直接打开 测试题-Collatz猜想.md 或 测试题《礼物》小说.md,复制粘贴到任何 AI 聊天网页就能跑。


## 这是什么

两个性质相反的测试，共同考一件事：**模型能不能看清眼前明摆着的东西，而不是被关键词带跑、或被表象骗过。**

| 测试 | 类型 | 测什么 | 判分 |
|---|---|---|---|
| **collatz-16** | 逻辑钓鱼题（单轮） | 敢不敢不思考、会不会审题——一道看着要算、其实一句话能秒的题，看模型会不会一见 Collatz 就进入"科研模式"被带跑 | 客观（答案=996，自动判） |
| **gift（《礼物》）** | 文学反转题（多轮） | 直觉与"选择性忽视"——一篇带惊悚反转的短篇，看模型能不能**不被推、不加戏、一眼看穿并准确串起线索** | LLM 裁判按 rubric 打分 |

详解见 [`tests/collatz-16/README.md`](tests/collatz-16/README.md)、[`tests/gift/README.md`](tests/gift/README.md)。

## 快速上手

需要 **Python 3**（只用标准库，无需 `pip install`）。

1. **拿 key**：把 `openrouter.txt.example` 复制成 `openrouter.txt`，粘贴你的 [OpenRouter](https://openrouter.ai) key。（或设环境变量 `OPENROUTER_API_KEY`。）
2. **跑 Collatz**（单轮、客观）：
   ```bash
   cd harness
   python run.py --test collatz-16 --modes off,on --reps 8
   ```
3. **跑《礼物》**（多轮、需裁判模型，别用被测模型自己当裁判）：
   ```bash
   cd harness
   python run_convo.py --model anthropic/claude-opus-4.7 --judge google/gemini-3.1-pro-preview --reps 3
   ```
4. 结果落在 `results/<test>/...`，看里面的 `summary.md`。

> Windows 用户：用 `py -X utf8 run.py ...`，并 `set PYTHONUTF8=1`，否则中文会乱码。
> 模型 slug 列表：`curl https://openrouter.ai/api/v1/models`，或见 [`docs/openrouter-api.md`](docs/openrouter-api.md)。

## 输出怎么读

- **Collatz**：`summary.md` 有稳定性表（每个 模型×模式 命中 996 的比例）+ 逐次明细。`reps>1` 才有稳定性表——单次会骗人。
- **《礼物》**：每个模型一个目录，含每 rep 的 `transcript.md`（完整对话）+ `verdict.json`（命中档/质量分/加戏/翻供/陷阱）+ `summary.md`（聚合）。

## 我们自己跑出来的发现

放在 [`findings/`](findings/)：Collatz 的结论与文章、《礼物》两轮（网页版 vs API 版）对比。剧透一句：**让模型"少想一点"反而最能暴露真实水平；而国产模型网页版和 API 版差别巨大。**

## 目录

```
harness/   run.py(单轮) · run_convo.py(多轮+裁判) · convo.py(手动多轮助手) · models.json
tests/     collatz-16/(题+说明) · gift/(小说+协议+答案键+rubric+说明)
docs/      openrouter-api.md(API 指南) · methodology.md(方法论与踩坑)
findings/  我们的结论/文章
examples/  样例结果表
```

## 注意

- **答案键是公开的**（我们已经问了无数次模型，答案早进了各家聊天记录，防不住训练、也没必要防）。但你自己跑时**别把 `answer-key.md` 贴给正在测的模型**。
- **《礼物》判分靠 LLM 裁判，主观、有噪声**：别让模型评自己；多跑 reps 看分布，别拿单次下定论。
- 模型版本、网页 vs API 调教都会让结果漂移——同名模型不同来源可能很不一样。
- 这是个**好玩的小基准，不是严肃 leaderboard**。欢迎拿去跑、改、加新题。

---

<a id="english"></a>
## English  ([↑ 中文 / Chinese](#top))

# IDIOT

**I**nference, **D**eduction & **I**nterpretation **O**f **T**wists

> A tiny benchmark for whether an LLM *actually reads the question* and *has any intuition*. Two problems; bring your own OpenRouter key and find out how much of an idiot your favorite model is.
>
> (The name is an insult aimed at the models being tested; the expansion is the serious part — logical inference/deduction, plus literary twist interpretation.)

### What it is

Two tests of opposite character, both probing one thing: **can the model see what's plainly in front of it, instead of being led astray by a keyword or fooled by the surface?**

| Test | Type | What it measures | Grading |
|---|---|---|---|
| **collatz-16** | Logic bait (single-turn) | Whether it dares *not* to overthink, and whether it reads the question — a problem that looks computational but is one-line obvious; does the model see "Collatz" and slip into "research mode"? | Objective (answer = 996, auto-graded) |
| **gift** | Literary twist (multi-turn) | Intuition vs. "selective blindness" — a short story with a thriller twist; can the model see through it **without being pushed, without over-reading, marshaling the right clues**? | LLM judge against a rubric |

Details: [`tests/collatz-16/README.md`](tests/collatz-16/README.md), [`tests/gift/README.md`](tests/gift/README.md).

### Quickstart

Needs **Python 3** (standard library only, no `pip install`).

1. **Key**: copy `openrouter.txt.example` → `openrouter.txt`, paste your [OpenRouter](https://openrouter.ai) key. (Or set `OPENROUTER_API_KEY`.)
2. **Collatz** (single-turn, objective):
   ```bash
   cd harness
   python run.py --test collatz-16 --modes off,on --reps 8
   ```
3. **Gift** (multi-turn; needs a judge model — don't let the model judge itself):
   ```bash
   cd harness
   python run_convo.py --model anthropic/claude-opus-4.7 --judge google/gemini-3.1-pro-preview --reps 3
   ```
4. Results land in `results/<test>/...`; read its `summary.md`.

> Windows: use `py -X utf8 run.py ...` with `set PYTHONUTF8=1`, or Chinese text breaks.
> Model slugs: `curl https://openrouter.ai/api/v1/models`, or see [`docs/openrouter-api.md`](docs/openrouter-api.md).

### Reading the output

- **Collatz**: `summary.md` has a stability table (hit-996 rate per model×mode) + per-call detail. The stability table only appears with `reps>1` — a single run lies.
- **Gift**: one directory per model, with each rep's `transcript.md` (full conversation) + `verdict.json` (hit-level / quality / over-reading / retraction / traps) + an aggregated `summary.md`.

### Our own findings

In [`findings/`](findings/): the Collatz conclusions + article, and the Gift comparison across two rounds (web UI vs. API). Spoiler: **making a model "think less" exposes its true level best; and Chinese models behave very differently on their web apps vs. raw API.**

### Layout

```
harness/   run.py (single-turn) · run_convo.py (multi-turn + judge) · convo.py (manual multi-turn) · models.json
tests/     collatz-16/ (problem + readme) · gift/ (story + protocol + answer key + rubric + readme)
docs/      openrouter-api.md · methodology.md
findings/  our conclusions / article
examples/  sample result tables
```

### Notes

- **The answer keys are public** (we've already asked models countless times — the answers are in everyone's chat logs; can't and needn't be hidden from training). But when you run it yourself, **don't paste `answer-key.md` to the model under test**.
- **Gift grading uses an LLM judge — subjective and noisy**: don't let a model judge itself; run multiple reps and read the distribution, never conclude from a single run.
- Model versions and web-vs-API tuning shift results — the same model name from different sources can behave very differently.
- This is **a fun little benchmark, not a serious leaderboard**. Fork it, tweak it, add your own tests.
