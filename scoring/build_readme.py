#!/usr/bin/env python3
"""重建 README 里的实时榜单段。

跑两个评分脚本（--md），把生成的 markdown 表注入 README 的标记区
（<!-- COLLATZ:START/END -->、<!-- GIFT:START/END -->），并盖上更新日期。

**榜单永远由脚本生成、人手不碰分数**——这从结构上杜绝了手填分。
加完新模型（往 scoring/models-*.json 加一行）后，跑一次本脚本即可。

用法：python scoring/build_readme.py
"""
import subprocess, sys, os, re
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PY = sys.executable
README = os.path.join(REPO, "README.md")


def run_md(script, data):
    r = subprocess.run([PY, os.path.join(HERE, script), os.path.join(HERE, data), "--md"],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        sys.exit(f"{script} 失败：\n{r.stderr}")
    return r.stdout.strip()


def inject(text, tag, content):
    pat = re.compile(rf"(<!-- {tag}:START -->).*?(<!-- {tag}:END -->)", re.S)
    if not pat.search(text):
        sys.exit(f"README 里找不到 {tag} 标记区")
    return pat.sub(lambda m: f"{m.group(1)}\n{content}\n{m.group(2)}", text)


def main():
    collatz = run_md("score_collatz.py", "models-collatz.json")
    gift = run_md("score_gift.py", "models_api.json")
    today = datetime.now().strftime("%Y-%m-%d")
    with open(README, encoding="utf-8") as f:
        text = f.read()
    text = inject(text, "COLLATZ", collatz)
    text = inject(text, "GIFT", gift)
    text = re.sub(r"(<!-- UPDATED -->).*?(<!-- /UPDATED -->)",
                  lambda m: f"{m.group(1)}{today}{m.group(2)}", text)
    with open(README, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"README 榜单已更新 · {today}")


if __name__ == "__main__":
    main()
