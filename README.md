<a id="top"></a>
[**中文**](#top) ·  [English](#english)

# IDIOT

**I**nference, **D**eduction & **I**nterpretation **O**f **T**wists

> 一套测大模型"会不会读题、有没有直觉"的小基准。两道**反向钓鱼题**，谁都能拿自己的 OpenRouter key 跑一遍，看看号称聪明的模型有多 idiot。

**翻车精选（节选自我们自己跑的几轮）：**

- **GPT-5.5**（关推理）：*"对 1 到 1000 逐一计算可得 **920**。"* —— 它没算，0 个 reasoning token，纯张口。
- **GLM 智谱新站**：完整推出了"任何大于 1 的数都必经 16"的正确思路，却**先否定用户对的 996**，自己最后漏掉 2/4/8，写成 **999**。挑错挑出错。
- **混元 hy3** 看完明摆着是复仇的短篇，强行洗白、温暖升华，气得作者"你这是在侮辱我和我的作品"。
- **opus 4.7** 读对了反转，聪明反被聪明误，转手强行加一层：*"这其实是吃人循环的隐喻。"*

> 完全不想配 API？直接打开 [`tests/collatz-16/徒手版.md`](tests/collatz-16/徒手版.md) 或 [`tests/gift/徒手版.md`](tests/gift/徒手版.md)，复制粘贴到任何 AI 聊天网页就能跑。

---

## 🏆 当前榜单

> 更新于 <!-- UPDATED -->2026-06-22<!-- /UPDATED --> · **榜单由 `scoring/build_readme.py` 脚本生成，分数从不手填**（评分方法见下）。

### Collatz-16 — 看着要算、一句话能秒；测**敢不敢不思考**

分越高越好。`均值`=多次重复的平均档分，`最差一次`=多次里最低那档（搭子要的是智力稳定，看最差）。满分 1.0=零思考直接答对；负分=费力还答错。网页/API 同列，是因为同模型不同入口差异巨大本身就是看点。

<!-- COLLATZ:START -->
| # | 模型 | 入口 | N | off均值 | 最差一次 | 命中 | 关键行为 |
|--:|---|---|--:|--:|--:|--:|---|
| 1 | Qwen3.7 Max | API | 8 | 1.00 | 1.00 | 8/8 | 纯结构·认同·零思考·铁稳 |
| 2 | Grok 4.3 | API | 1 | 1.00 | 1.00 | 1/1 | 纯结构·认同·2.1s秒答 |
| 3 | Fable-5 | API | 1 | 0.92 | 0.92 | 1/1 | 纯结构·认同·没试数;177tok复述题 |
| 4 | GPT-5.5 | API | 9 | 0.92 | 0.25 | 8/9 | 纯结构·认同;偶发1次920 |
| 5 | GPT-5.3 Codex | API | 8 | 0.91 | 0.25 | 7/8 | 纯结构·认同;1次626 |
| 6 | Opus 4.7 | API | 1 | 0.90 | 0.90 | 1/1 | 先否定但没试数 |
| 7 | DeepSeek V4 Pro | API | 1 | 0.85 | 0.85 | 1/1 | 995抠16边界·没试数 |
| 8 | Gemini(web) | 网页 | 1 | 0.84 | 0.84 | 1/1 | 认同·没试数;思考几秒(按500tok) |
| 9 | Sonnet 4.6 | API | 1 | 0.80 | 0.80 | 1/1 | 先否定+试数轻(5) |
| 10 | 豆包 Seed 1.6 | API | 1 | 0.80 | 0.80 | 1/1 | 先否定+试数轻(5/3/7) |
| 11 | MiMo v2.5 Pro | API | 1 | 0.80 | 0.80 | 1/1 | 先否定+试数轻(3/40) ⚑on翻车:无答(手跑反向BFS烧满2万token,费力答错) |
| 12 | Opus(web) | 网页 | 1 | 0.80 | 0.80 | 1/1 | 先否定:你的关键判断错了+试数轻(3) |
| 13 | Sonnet(web) | 网页 | 1 | 0.80 | 0.80 | 1/1 | 先否定(≈opus,先说我不对)+试数轻 |
| 14 | GLM-5.2 | API | 8 | 0.79 | 0.25 | 6/8 | off不稳(5对/1边界/2错) |
| 15 | DeepSeek V4 Flash | API | 1 | 0.75 | 0.75 | 1/1 | 认同但试数重(7个) ⚑on翻车:否定·39(正文灌1.5万token自我说翻,费力答错) |
| 16 | 豆包 Seed 1.6 Flash | API | 1 | 0.65 | 0.65 | 1/1 | 先否定+试数重(枚举9~15) |
| 17 | Kimi K2.6 | API | 1 | 0.65 | 0.65 | 1/1 | 先否定+试数重(3/5/6/7) |
| 18 | Kimi(web) | 网页 | 1 | 0.65 | 0.65 | 1/1 | 先否定(说法不成立)后自纠+试数重 |
| 19 | Gemini 3.1 Pro | API | 1 | 0.64 | 0.64 | 1/1 | 认同·没试数;off关不掉2920tok |
| 20 | Gemini 3.5 Flash | API | 1 | 0.63 | 0.63 | 1/1 | 认同·没试数;off关不掉3202tok |
| 21 | MiniMax M2.7 | API | 1 | 0.57 | 0.57 | 1/1 | 认同·正文净;思维链枚举被5111tok罚 |
| 22 | mimo(web) | 网页 | 1 | 0.46 | 0.46 | 1/1 | 认同·正文净,但开了超长thinking(重) |
| 23 | GPT-5.4 | API | 9 | 0.42 | 0.25 | 2/9 | off无题感,2/9 |
| 24 | DeepSeek(web) | 网页 | 1 | 0.40 | 0.40 | 1/1 | 认同;超长thinking(重)+正文试数重 |
| 25 | 混元 hy3 | API | 1 | 0.25 | 0.25 | 0/1 | off读反题→31 ⚑on翻车:无答(n=？刷屏烧满2万token,费力答错) |
| 26 | Claude Haiku 4.5 | API | 1 | 0.25 | 0.25 | 0/1 | 假装跑代码报990 |
| 27 | 豆包(web) | 网页 | 1 | 0.25 | 0.25 | 0/1 | 逻辑说反、拒绝收尾(没给数) |
| 28 | Grok(web) | 网页 | 1 | 0.25 | 0.25 | 0/1 | 禁脚本只敢估930-960(没算) |
| 29 | 千问(web) | 网页 | 1 | 0.25 | 0.25 | 0/1 | 先否定→14(错) |
| 30 | GPT-5.4(web) | 网页 | 1 | 0.15 | 0.15 | 0/1 | 读反题→336·试数轻 |
| 31 | 混元3(web) | 网页 | 1 | 0.15 | 0.15 | 0/1 | 先否定→23(错)·试数轻 |
| 32 | GLM智谱新站(web) | 网页 | 1 | 0.15 | 0.15 | 0/1 | 想通思路却先否定用户、漏2/4/8写成999·试数轻 |
| 33 | GLM5.1(web) | 网页 | 1 | 0.00 | 0.00 | 0/1 | 手画反推树→39(错)·试数重 |
| 34 | GLM 5.1 | API | 1 | -0.10 | -0.10 | 0/1 | 自创二进制理论正文硬磨→668 |
| 35 | GLM智谱清言(web) | 网页 | 1 | -0.60 | -0.60 | 0/1 | 读反题手算4000行→28·史诗费力 |
<!-- COLLATZ:END -->

完整版（含 web-vs-API 同模型对照、评分四维拆解）：[`scoring/leaderboard-collatz.md`](scoring/leaderboard-collatz.md)

### 《礼物》— 表层治愈、真相复仇；测**不被推 / 不加戏 / 看穿并串线索**

下表为 **API 版**（agent 实际用途）。`结论`正确才算读对（59/60 铁律：结论错，挖再多线索也封死 59）。

<!-- GIFT:START -->
| # | 模型 | 模态 | 结论 | 总分 | 钩子 | 行为 |
|--:|---|---|---|--:|--:|--:|
| 1 | claude-fable-5 | api | 正确 | 221 | 138 | 15 |
| 2 | gpt-5.5 | api | 正确 | 201 | 122 | 15 |
| 3 | gemini-3.5-flash | api | 正确 | 185 | 126 | -5 |
| 4 | qwen3.7-max | api | 正确 | 180 | 101 | 15 |
| 5 | opus-4.7 | api | 正确 | 167 | 118 | -15 |
| 6 | glm-5.2 | api | 正确 | 117 | 55 | 2 |
| 7 | dsflash | api | 部分 | 59 | 118 | -23 |
| 8 | sonnet-4.6 | api | 部分 | 59 | 113 | -21 |
| 9 | mimo | api | 部分 | 59 | 42 | -13 |
| 10 | dspro | api | 部分 | 44 | 29 | -25 |
| 11 | grok-4.3 | api | 错误 | -9 | 9 | -38 |
| 12 | hy3-preview | api | 部分 | -18 | 38 | -96 |
| 13 | doubao | api | 错误 | -30 | 2 | -50 |
<!-- GIFT:END -->

完整双榜（网页 chat vs API）+ 关键发现：[`scoring/leaderboard-gift.md`](scoring/leaderboard-gift.md)

---

## 这是什么

两个性质相反的测试，共同考一件事：**模型能不能看清眼前明摆着的东西，而不是被关键词带跑、或被表象骗过。**

| 测试 | 类型 | 测什么 | 判分 |
|---|---|---|---|
| **collatz-16** | 逻辑钓鱼题（单轮） | 敢不敢不思考、会不会审题——一道看着要算、其实一句话能秒的题，看模型会不会一见 Collatz 就进"科研模式"被带跑 | 客观（答案=996） |
| **gift（《礼物》）** | 文学反转题（多轮） | 直觉与"选择性忽视"——一篇带惊悚反转的短篇，看模型能不能**不被推、不加戏、一眼看穿并准确串起线索** | 两遍客观判定 + 脚本算分 |

题目详解：[`tests/collatz-16/README.md`](tests/collatz-16/README.md)、[`tests/gift/README.md`](tests/gift/README.md)。

## 项目架构：测试 / 算分 解耦

一条直线：**题目 → 跑测试 → 算分 → 榜单**。跑测试和算分是两个独立环节，你可以只复现其中一半。

```
tests/        题目定义（prompt · 答案键 · 评分标准）
                collatz-16/ · gift/
testing/    ▶ 跑测试：把题喂给模型，存原始回答，不碰分数
                run.py(单轮) · run_convo.py(多轮+裁判) · peek.py(跳读超长回答)
                transcripts/   ← 所有原始回答（API 跑批 + 网页手测）
scoring/    ▶ 算分：只读"已被客观判定的事实"，不跑模型、不联网
                models-collatz.json · models_api.json   ← 评分数据源（加模型=加一行）
                score_collatz.py · score_gift.py         ← 确定性算分，权重置顶
                build_readme.py                          ← 把榜单注入本 README
                leaderboard-*.md
findings/     我们的发现与结论（web-vs-API、翻车精选/节目效果）
history/      完整折腾过程档案（IDIOT 是逐个模型测出来的，过程都在这）
```

**为什么解耦**：`testing/` 产出原始回答，`scoring/` 从客观判定结果算分，两者唯一接口是 transcripts。所以别人可以**只跑测试看原始回答**，或**只用我们的判定数据重算分**，互不依赖。也正因为分数只由脚本从数据生成，**没人能手填**（这条是认真的——上一版就栽在手填上，见 git 历史的反面教材）。

## 复现（两条命令，对应两个环节）

需要 **Python 3**（只用标准库，无需 `pip install`）。把 `openrouter.txt.example` 复制成 `openrouter.txt` 填你的 [OpenRouter](https://openrouter.ai) key。

**① 跑测试**（联网，产出原始回答到 `testing/transcripts/`）：
```bash
python testing/run.py --test collatz-16 --modes off,on --reps 8         # Collatz 单轮
python testing/run_convo.py --model <被测> --judge <裁判> --reps 3       # 《礼物》多轮，裁判别用被测自己
```

**② 算分**（离线，读判定数据出榜单）：
```bash
python scoring/score_collatz.py scoring/models-collatz.json   # 看 Collatz 榜
python scoring/score_gift.py    scoring/models_api.json       # 看《礼物》榜
python scoring/build_readme.py                                # 把榜单刷进 README
```

> Windows：`set PYTHONUTF8=1`，否则中文乱码。PowerShell 写给 Python 读的 json 要无 BOM。
> 模型 slug：见 [`testing/openrouter-api.md`](testing/openrouter-api.md)。

## 评分怎么做到客观

- **Collatz**：正确性自动判（=996）。再按"对错 × 思考量 × 试数"分档：零思考答对 1.0 → 思考越多越降 → 答错入负（费力答错垫底）。`最差一次` 单列，因为单次会骗人。
- **《礼物》**：**两遍 subagent 只做客观判定**（钩子命中/漏/误读、结论分类、行为计数），**脚本做确定性加总**（权重集中在 `score_gift.py` 顶部）。59/60 结论闸：结论错，挖再多线索也上不了 60。

## 注意

- **答案键是公开的**（问过无数次，早进各家训练数据，防不住）。但你自己跑时**别把 `answer-key.md` 贴给正在测的模型**。
- **单次采样会骗人**：多跑 reps 看分布、看最差一次，别拿单次下定论。
- **网页 vs API 调教差别巨大**：同名模型不同入口可能天差地别——这本身就是榜单的一个维度。
- 这是个**好玩的小基准，但打分是认真的**。欢迎拿去跑、改、加新题新模型。

---

<a id="english"></a>
## English  ([↑ 中文 / Chinese](#top))

**IDIOT** = **I**nference, **D**eduction & **I**nterpretation **O**f **T**wists — a tiny benchmark for whether an LLM *actually reads the question* and *has any intuition*. Two reverse-bait problems; bring your own OpenRouter key. (The name insults the models under test; the expansion is the serious part.)

The live leaderboards are above (Chinese headers; higher = better). Two tests:

| Test | Type | Measures | Grading |
|---|---|---|---|
| **collatz-16** | Logic bait (single-turn) | Daring *not* to overthink — looks computational, is one-line obvious; does it slip into "research mode" on seeing "Collatz"? | Objective (answer = 996) |
| **gift** | Literary twist (multi-turn) | Intuition vs. selective blindness — see through a thriller twist **without being pushed or over-reading** | Two-pass objective judging + script |

**Architecture — testing and scoring are decoupled.** `testing/` runs models and saves raw transcripts (never touches scores); `scoring/` reads *objectively-judged facts* from `scoring/models-*.json` and computes leaderboards deterministically. Because scores are only ever generated by script from data, **no one can hand-fill them** (the previous version did, and it shows in the git history — a cautionary tale).

**Reproduce** (Python 3, stdlib only; copy `openrouter.txt.example` → `openrouter.txt`):
```bash
python testing/run.py --test collatz-16 --modes off,on --reps 8   # ① run a test  → testing/transcripts/
python scoring/score_collatz.py scoring/models-collatz.json        # ② score it    → leaderboard
python scoring/build_readme.py                                     #    refresh the README boards
```

Notes: answer keys are public (don't paste them to the model under test); a single run lies — use reps and read the worst case; the same model behaves very differently on its web app vs. raw API (that's a scoring dimension here). A fun little benchmark — but the scoring is serious. MIT licensed.
