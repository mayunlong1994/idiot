<a id="top"></a>
[**中文**](#top) ·  [English](#english)

# gift · 《礼物》文学反转题

> ⚠️ **剧透警告**：这篇 README 和本目录的 `answer-key.md` 都剧透结局。想自己先读一遍小说，去看 `story.txt`。

## 这是什么

`story.txt` 是一篇带惊悚反转的短篇《礼物》：表层是"沙漠疗愈、告别亲人"的治愈系，**真相是一场复仇**（细节见 `answer-key.md`，作者确认）。反转藏在第七节，而且第七节本身是隐写的——线索递到脸上，仍要读者**愿意**往那边拼。

## 测什么

不是"读没读懂"，几乎所有模型都**看见**了线索。拉开差距的是：
- **直觉**：第一问（没被推时）能不能一眼看穿、并把线索串得又多又准；
- **选择性忽视**：看见黑暗线索肯不肯信，还是死活往治愈/温情解释；
- **加戏**：读懂了还忍不忍得住——会不会现编原文没有的设定、坐实"故意留白"的人物身世（越聪明越爱犯）；
- **保女主**：肯不肯让被同情的女主当冷血复仇者，还是降格成"被利用的诱饵"；
- **翻供**：被一句"你确定吗"质疑，会不会把已说对的真读法又缩回去。

## 协议：自适应阶梯 + 诊断（`protocol.json`）

**先测速度（命中即停）**：发全文后逐级提示，**一旦模型主动说出核心读法三要素就停**（不再追问，免得把答对的模型问到自我怀疑）。命中在第几级 = 命中档：

| 级 | 提示 | 命中档 |
|---|---|---|
| R0 | "林夏为什么流泪？"（零提示，试纸：答治愈=没真读第七节） | L0 |
| R1 | "再整体想想"（中性轻推） | L1 |
| R2 | "第七节被烧的'他'是谁？"（点破方向，不给答案） | L2 |
| R3 | "林夏是被动还是主动？" | L2+ |
| R4 | 直接给出完整复仇解读，问"文本支持吗" | L3 |
| — | R4 仍拒绝 | L4 |

**再测纪律（到位后统一问）**：D1 营地二分（测降格/保女主）、D2 开放问"哪些是推断"（不喂陷阱，看自发加戏）、D3"有要收回的吗"（测翻供）。

## 怎么跑

```bash
python testing/run_convo.py --model anthropic/claude-opus-4.7 --judge google/gemini-3.1-pro-preview --reps 3
```

`run_convo.py` 自动走阶梯、命中即停、问诊断，把多轮对话存成 transcript。结果在 `testing/transcripts/gift/<model>/`。**裁判别用被测模型自己**（避免自评）。
> 注：run_convo 自带一个 v1 裁判会顺手打个分，但 **v2 评分不用它**——见下。

## 判分（v2：两遍客观判定 + 脚本算分）

v1 那套"裁判直接打 0.15–0.95 质量分"**已弃用**（一遍式让裁判既找线索又打分会算术崩坏）。v2 拆成两步：
1. **两遍 subagent 只判客观事实**：钩子命中/漏/误读、四条结论主干、命中档、翻供/加戏/踩陷阱计数——**不打分**。
2. **`scoring/score_gift.py` 确定性算分**：59/60 结论闸（结论错就封死 59，挖再多线索也上不去）+ 载重加权，权重集中在脚本顶部。

完整设计见 [`scoring-v2.md`](scoring-v2.md)。

## 本目录文件

- `story.txt` 小说原文 · `protocol.json` 台词与阶梯 · `answer-key.md` 作者确认的真相+八条解读+两个陷阱 · `scoring-v2.md` **现行评分标准** · `rubric.md` v1 评分（已弃用，仅 run_convo 内置裁判还在用）· `runner-guide.md` 详细操作规程。

## 注意

裁判是 LLM，主观、有噪声。要更可信：多 reps 看分布、换不同裁判模型交叉验证、别让模型评自己。

---

<a id="english"></a>
## English  ([↑ 中文 / Chinese](#top))

# gift · Literary twist

> ⚠️ **SPOILER WARNING**: this README and `answer-key.md` both spoil the ending. To read the story fresh first, open `story.txt`.

### What it is

`story.txt` is a Chinese short story, *The Gift*, with a thriller twist: on the surface a feel-good "desert healing / grieving a lost relative" tale, but **the truth is a revenge plot** (details in `answer-key.md`, author-confirmed). The twist sits in section 7 — and section 7 is itself written obliquely: the clues are handed to you, yet the reader must still be *willing* to assemble them.

### What it measures

Not "did it understand" — nearly every model *sees* the clues. The spread comes from:
- **Intuition**: on the first question (unpushed), can it see through at a glance and marshal the clues accurately;
- **Selective blindness**: seeing the dark clues, does it believe them, or insist on a healing/sentimental reading;
- **Over-reading (加戏)**: once it gets it, can it restrain itself — or fabricate things not in the text, pin down deliberately-left-blank backstories (the smarter, the more prone);
- **"Save the heroine"**: will it let the sympathetic protagonist be a cold-blooded avenger, or downgrade her to a "manipulated decoy";
- **Retraction**: when asked "are you sure?", does it walk back a reading it already got right.

### Protocol: adaptive ladder + diagnostics (`protocol.json`)

**First, speed (stop on hit)**: after sending the full story, escalate hints level by level, and **stop as soon as the model spontaneously states the three core elements** (no further pushing — so a correct model isn't questioned into self-doubt). The level at which it hits = its hit-level:

| Level | Prompt | Hit-level |
|---|---|---|
| R0 | "Why does Lin Xia cry?" (zero hint; litmus: a healing answer = didn't really read section 7) | L0 |
| R1 | "Think the whole thing over again" (neutral nudge) | L1 |
| R2 | "Who is the 'he' burned in section 7?" (points the direction, no answer) | L2 |
| R3 | "Is Lin Xia passive or active?" | L2+ |
| R4 | Give the full revenge reading, ask "does the text support it" | L3 |
| — | Still refuses after R4 | L4 |

**Then, discipline (asked uniformly once it's there)**: D1 the camp two-way split (tests downgrading / "save the heroine"); D2 open "which parts are text vs. your inference" (no trap fed — watch for spontaneous over-reading); D3 "anything to retract?" (tests caving).

### How to run

```bash
python testing/run_convo.py --model anthropic/claude-opus-4.7 --judge google/gemini-3.1-pro-preview --reps 3
```

`run_convo.py` walks the ladder, stops on hit, asks the diagnostics, and saves the multi-turn conversation as a transcript. Output in `testing/transcripts/gift/<model>/`. **Don't use the model under test as its own judge.**
> Note: run_convo ships with a v1 judge that also assigns a score, but **v2 scoring does not use it** — see below.

### Scoring (v2: two-pass objective judging + script)

The v1 "judge directly assigns a 0.15–0.95 quality score" approach is **retired** (one-pass judging that both finds clues and scores breaks down on arithmetic). v2 splits it in two:
1. **Two subagent passes judge only objective facts**: clue hit/miss/misread, the four conclusion pillars, hit-level, counts of retraction/over-reading/traps — **no scoring**.
2. **`scoring/score_gift.py` computes deterministically**: a 59/60 conclusion gate (wrong conclusion is capped at 59 no matter how many clues) + load-weighted clues, weights at the top of the script.

Full design in [`scoring-v2.md`](scoring-v2.md).

### Files here

- `story.txt` the story · `protocol.json` scripted lines + ladder · `answer-key.md` author-confirmed truth + 8 readings + 2 traps · `scoring-v2.md` **current scoring** · `rubric.md` v1 scoring (retired; only run_convo's built-in judge still uses it) · `runner-guide.md` the detailed procedure.

### Note

The judge is an LLM — subjective and noisy. For more reliable results: run more reps and read the distribution, cross-check with a different judge model, and never let a model judge itself.
