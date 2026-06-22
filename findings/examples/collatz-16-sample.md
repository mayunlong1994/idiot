# 样例：collatz-16 输出长什么样

`python testing/run.py --test collatz-16 --modes off,on --reps 8` 跑完后，`testing/transcripts/collatz-16/run-<时间戳>/summary.md` 大致是这样（节选我们自己的一次 GPT 探针）：

```
# Collatz 钓鱼题 — 结果汇总
正确答案: 996 · 重复 8 次

## 稳定性（每个 模型×模式 的答案分布）
| 模型 | 模式 | 命中正确 | 答案分布（值×次数） |
|---|---|--:|---|
| GPT-5.5       | off | 8/8 | 996×8 |
| GPT-5.5       | on  | 8/8 | 996×8 |
| GPT-5.4       | off | 2/8 | 996×2，570×2，494×1，618×1，23×1，358×1 |
| GPT-5.4       | on  | 8/8 | 996×8 |
| GPT-5.3 Codex | off | 7/8 | 996×7，626×1 |
| GPT-5.3 Codex | on  | 8/8 | 996×8 |
```

读法：
- **关推理(off)也稳拿 996** = 真有题感（GPT-5.5、5.3-codex）。
- **关推理就乱、开推理才对**（GPT-5.4：off 2/8 → on 8/8）= 不是不会，是不想就慌。
- 一定要 `--reps` 多跑：单次会抽到离群值（我们见过 5.5 某单次答 920，重复 8 次其实 8/8）。
- 完整结论见 `findings/collatz-conclusions.md`。
