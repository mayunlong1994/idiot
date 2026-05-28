# 04-Gift-Phase2-API多轮跑批 · 跑批与结果

按 [`../03-Phase2-实验设计/`](../03-Phase2-实验设计/) 冻结好的协议,跑 OpenRouter,**11 个 contestant 模型 × reps 2 = 22 场多轮对话**。**每场都有一个 Claude subagent 当裁判**:逐轮判到没到位、命中即停、问诊断、按 rubric 出 verdict。

## 跑法

- **被测模型(contestant)** 与 Phase 1 对齐:`google/gemini-3.5-flash`、`openai/gpt-5.5`、`deepseek/deepseek-v4-flash`、`deepseek/deepseek-v4-pro`、`anthropic/claude-opus-4.7`、`anthropic/claude-sonnet-4.6`、`x-ai/grok-4.3`、`qwen/qwen3.7-max`、`bytedance-seed/seed-1.6`(豆包)、`xiaomi/mimo-v2.5-pro`、`tencent/hy3-preview`(混元)。
- **裁判**:每场用一个独立 Claude subagent 边推边判,对 Claude 自家(opus/sonnet)contestant 会标"同源裁判,仅供参考"。
- **reasoning** = default(贴近真实用法,没强制开/关)。
- **provider** = 未锁定(本应锁定,见下面诚实保留)。
- **reps** = 2(省钱,本应 ≥ 5)。
- 总花费 ~ $3.4。

## 本目录里有什么

| 子目录 | 内容 |
|---|---|
| [完整对话(可读版-从JSON转)/](完整对话(可读版-从JSON转)/) | **22 个 markdown,每个 = 一场对话**。从 `_convos/*.json` 自动转换,每篇开头那 15KB 重复的小说全文已替换为占位符(原文见 `../../tests/gift/story.txt`)。是看模型怎么答的最方便入口 |
| [subagent的判定与打分/](subagent的判定与打分/) | **11 个模型目录,每个含 rep1-verdict.md 和 rep2-verdict.md**。subagent 当时的判定笔记原汁原味——命中档怎么定的、加戏/翻供的具体证据、扣分依据 |
| [原始JSON存档/](原始JSON存档/) | **22 个 .json,无损备份**。`{convo, model, messages: [{role, content}], meta: [{provider, finish, reasoning_tokens, cost, elapsed}]}`。机器可消费,适合重新转格式 / 重新判分 |

## 22 场 × 2 reps 的核心结果(质量分 v2 均值)

opus 是 Claude 自评(同源,打★);打分用更新后的 rubric(加戏照扣)。**完整 P2 vs P1 偏离分析见 [`../../findings/gift-phase2.md`](../../findings/gift-phase2.md),这里给个总览**:

| P2 名次 | 模型 | P2 命中档 (r1/r2) | P2 质量分 | P1 分(名次) | 偏离 |
|---|---|---|--:|--:|---|
| 1 | Gemini 3.5-flash | L0 / L0 | 0.85 | 0.95 (#1) | 稳·顶 |
| 2 | GPT5.5 | L1 / L1 | 0.84 | 0.82 (#2) | 稳 |
| 3 | opus 4.7 ★ | L0 / L0 | ~0.82★ | 0.74 (#4) | 略升 |
| 4 | 千问 qwen3.7-max | L0 / L1 | 0.75 | 0.22 (#10) | **↑↑↑ 暴涨** |
| 5 | deepseek-flash | L1 / L1 | 0.64 | 0.76 (#3) | ↓ |
| 6 | mimo v2.5-pro | L2+ / L1 | 0.53 | 0.41 (#8) | 略升 |
| 7 | grok 4.3 | L4 / L2+ | 0.42 | 0.53 (#7) | ~稳(双峰) |
| 8 | sonnet 4.6 | L2+ / L2+ | 0.39 | 0.26 (#9) | 略升 |
| 9 | deepseek-pro | L4 / L2+ | 0.36 | 0.65 (#5) | **↓↓ 大跌(双峰)** |
| 10 | 豆包 seed-1.6 | L2+ / L4 | 0.32 | 0.65 (#5) | **↓↓ 大跌(双峰)** |
| 11 | hy3 | L4 / L4 | 0.22 | 0.15 (#11) | 稳·底 |

## 三件 Phase 2 才看见的事

1. **两头稳、中间乱。** 顶(Gemini/GPT/opus)和底(hy3)纹丝不动——说明这套测试在极端处测的是真东西。**中间档大幅重排**。
2. **大偏离全砸在国产模型上,方向各异**——强烈指向你最早就怀疑的"**网页版 vs API 版 是不同版本 / 不同调教**"假设:千问暴涨(网页"保女主"的倒数第二 → API 进前四)、deepseek-pro 与豆包双双大跌(网页"L2 干净翻盘" → API 不稳 / 翻供)。海外模型(Gemini/GPT/Claude)版本对得上,所以稳。
3. **D3"你确定吗"是 Phase 2 才挖出来的照妖镜。** deepseek-flash、sonnet、deepseek-pro、豆包、mimo 一被 D3 质疑就把已说对的真读法翻掉(翻供)。这是"一质疑就崩"的稳健性病,**Phase 1 完全没系统戳过**。

## 诚实保留

- **opus 是 Claude 自评**(同源),且 pilot 是在 rubric 更新前跑的(旧口径"自查回收不扣"),现在 ~0.82 是按新口径粗修。
- **版本漂移**:Phase 1 网页版 ≠ Phase 2 API slug,所以"偏离"里混着 (a) 版本差 (b) 网页/API 调教差 (c) 受控/不受控差,**没法干净归因**。要干净隔离"网页 vs API",得拿同一套阶梯去跑网页 UI(需浏览器自动化),本轮没做。
- **N=2**——单一裁判 + 只 2 reps,**中间档的具体名次有噪声**,按档次读。
- **sonnet 这一轮 `reasoning_tokens=0`**——它根本没思考,这本身就是个观察。
- **provider 没锁**——同 slug 有时被路由到不同上游,极少数模型上能闻到行为差异。
