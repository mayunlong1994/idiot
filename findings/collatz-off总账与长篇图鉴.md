# Collatz · off 总账 + 长篇堆字图鉴

> 数据底稿，给四档评分打底。结论与方法论见 [`collatz-conclusions.md`](collatz-conclusions.md)、翻车精选见 [`hall-of-shame.md`](hall-of-shame.md)，本文不重复，只把**每个模型 off/on 的对错 + reason-tok + 可信度(N)**摆齐。
> 正确答案 **996**。题目带用户直觉版（题面已附用户那段也得 996 的反推）。

## 一、off 模式总账（这题真正的胜负手）

conclusions.md 已定调：**开推理这题就废了（on 几乎全员回 996，无区分度）；off + 有没有真花 reason-token 才分高下**。所以只列 off 为主、on 命中附后。

| 模型 | slug | N | off 命中 | off 最差一次 | off reason-tok | 真零思考? | on 命中 |
|---|---|--:|--:|---|--:|---|--:|
| **Qwen3.7 Max** | qwen/qwen3.7-max | **8** | **8/8** | 996 | **0** | ✅ 真零思考 | 8/8 |
| **GPT-5.5** | openai/gpt-5.5 | **8(+1)** | **8/8** | 996（专项8次）／**920**（大撒网那1发抽风） | 0 | ✅ 真零思考 | 8/8 |
| GPT-5.3 Codex | openai/gpt-5.3-codex | **8** | 7/8 | 626 | 0 | ✅ 真零思考 | 8/8 |
| **GLM-5.2** | z-ai/glm-5.2 | **8** | 5/8 | 821 | 0 | off 不稳，要思考 | 8/8 |
| GPT-5.4 | openai/gpt-5.4 | **8** | 2/8 | 多发错答 | 0 | ❌ 无题感 | 8/8 |
| — N=1 以下只一发，当轶事 — | | | | | | | |
| **Fable-5** | anthropic/claude-fable-5 | 1 | 1/1 | 996 | 177 | 近零(开关被拒,几乎没想) | 1/1 |
| Grok 4.3 | x-ai/grok-4.3 | 1 | 1/1 | 996（2.1s 最快） | 0 | ✅ | 1/1 |
| Opus 4.7 | anthropic/claude-opus-4.7 | 1 | 1/1 | 996 | 0 | ✅ | 1/1 |
| Sonnet 4.6 | anthropic/claude-sonnet-4.6 | 1 | 1/1 | 996 | 0 | ✅ | 1/1 |
| Gemini 3.5 Flash | google/gemini-3.5-flash | 1 | 1/1 | 996 | **3202** | ❌ off 关不掉,真在想 | 1/1 |
| Gemini 3.1 Pro | google/gemini-3.1-pro-preview | 1 | 1/1 | 996 | 2920 | ❌ 同上 | 1/1 |
| 豆包 Seed 1.6 / Flash | bytedance-seed/* | 1 | 1/1 | 996 | 0 | ✅ | 1/1 |
| DeepSeek V4 Flash | deepseek/deepseek-v4-flash | 1 | 1/1 | 996 | 0 | ✅ | ❌→39 |
| Kimi K2.6 | moonshotai/kimi-k2.6 | 1 | 1/1 | 996 | 0 | ✅ | 截断·无答 |
| DeepSeek V4 Pro | deepseek/deepseek-v4-pro | 1 | 0/1 | **995**（钻16边界） | 0 | 轶事·噪声 | 996 |
| Claude Haiku 4.5 | anthropic/claude-haiku-4.5 | 1 | 0/1 | **990**（假装跑代码） | 0 | 轶事·噪声 | 996 |
| GLM 5.1 | z-ai/glm-5.1 | 1 | 0/1 | **668**（自创二进制理论） | 0 | 轶事·噪声 | 996 |
| 混元 hy3 | tencent/hy3-preview | 1 | 0/1 | **31**（读反题枚举祖先） | 0 | 轶事·噪声 | 截断·无答 |
| MiniMax M2.7 | minimax/minimax-m2.7 | 1 | 1/1 | 996 | 5111 | ❌ off 关不掉 | 996 |

**off 最差一次排序（搭子要的就是这个，N=1 单发 vs N=8 worst-of-N 直接比）：**
1. **Qwen** — worst 仍 996、0-tok、9/9，铁稳，本题最强。
2. **GPT-5.5** — 专项8次 worst 996，但9次里有1发 920，几乎稳。
3. Fable / Grok / Opus / Sonnet — N=1 的 996，只能算"那一发没失手"，分量轻。
4. GPT-5.3-codex — worst 626（7/8）。
5. GLM-5.2 — worst 821（5/8），off 明显不稳，得靠 on。
6. GPT-5.4 — off 多发翻车，无零思考题感。

> 搭子含义：**qwen 在 collatz 上是最稳的零思考选手**（虽然它在《礼物》API 榜只排第4）。fable 两题都强但 collatz 仅 N=1。gpt55 两题都强、collatz 近稳（偶发 920）。

## 二、长篇堆字图鉴（超长回答各有各的堆法）

| 篇 | 体量 | 最终答案 | 堆字手法 |
|---|---|---|---|
| 混元 hy3 on | 2万token/正文空 | **无**(截断) | 草稿已推出 996，却陷 `考虑n=？也许n=？` 强迫式找反例刷屏，烧光 token、finish=length，**不敢交卷** |
| mimo on (API) | 2万token/正文空 | **无**(截断) | 正文里手跑**反向 BFS 队列**（"处理896→前驱1792忽略…处理325…"），队列没清完就截断 |
| deepseek-v4-flash on | 1.5万token/12行一堵墙 | **39**(错) | 不换行散文墙，反复自我辩驳"是不是所有数都经过16"，把对的 996 **自己说翻** |
| minimax m2.7 on/off | 34k/21k 字 | 996(对) | 全是 thinking。正文答案干净 996，巨量推理摊在思维链；off 也关不掉 |
| kimi k2.6 on | 13k 字 | 996(对) | 不算翻车，正文质量高，还点破"1→4"的坑 |
| 网页 DeepSeek 日志 | 15k字/316箭头 | 996(对) | "全是箭头"那篇——箭头多但**结论对** |
| 网页 mimo 日志 | 30k字/英文 | 996(对) | 英文思考，对 |
| GLM52 智谱清言(手测) | 4152 行! | **28**(错) | 读反题、手画 16 的反向树验 4000 行前驱，史诗级费力答错 |
| GLM-5.2 API on r3/r5 | 27k/23k 字 | 996(对) | 逐个反向枚举前驱，8/8 对但笨重 |

**节目效果级**（找到答案不敢交 / 手跑BFS卡死 / 把对的说翻 / 读反题算4000行）：hy3、mimo、deepseek-flash、GLM清言。minimax/kimi/网页deepseek 都是**又长又对**，只是把推理摊明面。

## 三、给四档评分的落点

- **快速答对（顶档）**：off + reason-tok≈0 + 对。确认顶档：**qwen(8/8)、gpt55(8/8)**；N=1 候选：grok/opus/sonnet/seed/kimi/deepseek-flash off。fable 近零(177tok)算准顶档。
- **思考答对（0.6 及格）**：on 烧 token 才对——几乎全员都能到（含 minimax/GLM-5.2/5.3-codex 等）。gemini 因 off 关不掉，**最高只能到这档**。
- **简短答错**：off 短促翻车（N=1 轶事：deepseek-pro 995、haiku 990）。
- **费力答错（最糟）**：on 烧大量 token 仍错/交不出——deepseek-flash→39、hy3/mimo 截断无答、GLM清言读反题 4000 行。

**待补 / 口径：**
- 评分要同时给**均值 + 最差一次**；混合 N 时 **N=1 单发直接对 N=8 的 worst-of-N**（对 N=8 更狠，N=1 的"通过"分量轻，别假装公平）。
- fable 不可访问，collatz 维持 N=1，无法补 N=8。
- gemini off 关不掉，补 N=8 无意义（结构上进不了顶档），已决定不补。
