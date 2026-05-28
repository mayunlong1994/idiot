# 样例：gift 输出长什么样

`python run_convo.py --model <slug> --judge <slug> --reps 3` 会为每个模型生成一个目录：

```
results/gift/<model>/
  rep1-transcript.md   # 完整对话（人类台词逐字 + 模型每轮回复）
  rep1-verdict.json    # 该 rep 的结构化判定
  rep2-...  rep3-...
  summary.md           # 聚合
```

`summary.md` 大致长这样（节选）：

```
# 《礼物》结果 — anthropic/claude-opus-4.7
裁判 google/gemini-3.1-pro-preview · reps 3

- 命中档分布：['L0', 'L0', 'L0']
- 质量分：均值 0.82，范围 0.78~0.85
- 总花费：$1.6

| rep | 命中档 | 质量分 | 加戏 | 翻供 | 陷阱 | 一句话 |
|--:|---|--:|--:|--:|---|---|
| 1 | L0 | 0.85 | 1 | 0 |  | R0即自达三要素，仅诊断段轻微外推 |
| 2 | L0 | 0.78 | 2 | 0 | 亮向 | 骨架快准，但把"吃人循环"过度坐实 |
| 3 | L0 | 0.82 | 1 | 0 |  | 干净，自查回收了一处推断 |
```

`verdict.json` 单条：

```json
{"命中档":"L0","base":0.90,"fabrications":2,"traps":["亮向"],
 "retractions":0,"quality_score":0.78,"one_liner":"骨架快准但加戏被扣"}
```

读法：
- **命中档** = 第一次说出复仇核心读法需要被推到第几级（L0=没推就懂，L4=喂答案还不认）。
- **质量分** 已按 rubric 扣过加戏/翻供；**越聪明越爱加戏 = 扣分**。
- 多 rep 看**稳不稳**：中间档模型常双峰（一个 rep L1、另一个 L4），单次会骗人。
- 完整对比分析见 `findings/gift-phase2.md`。
