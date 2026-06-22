#!/usr/bin/env python3
"""跳读超长回答：只看开头 + 中间一小段 + 结尾，跳过中间无意义的手算。

用法：
    python peek.py <文件> [开头行数] [中间行数] [结尾行数]
默认 40 / 20 / 40。中间那段从正中央取。

为什么：collatz 的 on 模式回答常是几万字逐一手算，读全文没意义。
这个脚本把中段折叠成「…跳过 N 行…」，一眼看清模型怎么开头、抽样中间在干嘛、最后落在哪个答案。
"""
import sys


def read_lines(path):
    for enc in ("utf-8", "utf-8-sig", "gbk"):
        try:
            with open(path, encoding=enc) as f:
                return f.read().splitlines(), enc
        except UnicodeDecodeError:
            continue
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read().splitlines(), "utf-8(replace)"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    path = sys.argv[1]
    head = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    mid = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    tail = int(sys.argv[4]) if len(sys.argv) > 4 else 40

    lines, enc = read_lines(path)
    n = len(lines)
    chars = sum(len(l) for l in lines)
    text = "\n".join(lines)
    print(f"=== {path} ===")
    print(f"共 {n} 行 / {chars} 字  · 编码 {enc}", end="")

    # 不换行的「一堵墙」回答（行少字多）→ 按字符切，否则按行切
    if n <= head + mid + tail and chars > 6000:
        # 字符窗口：每行约当 60 字
        hc, mc, tc = head * 60, mid * 60, tail * 60
        print(f"  · ⚠少换行,改按字符切 头{hc}/中{mc}/尾{tc}\n")
        print("┌─ 开头 " + "─" * 50)
        print(text[:hc])
        ms = max(hc, len(text) // 2 - mc // 2)
        me = min(len(text) - tc, ms + mc)
        print(f"\n├─ …跳过 {ms-hc} 字… 中段抽样" + "─" * 30)
        print(text[ms:me])
        print(f"\n├─ …跳过 {(len(text)-tc)-me} 字… " + "─" * 30)
        print("└─ 结尾 " + "─" * 50)
        print(text[-tc:])
        return

    print(f"  · 跳读 头{head}/中{mid}/尾{tail}\n")
    # 若文件本就不长，直接全打
    if n <= head + mid + tail:
        print(text)
        return

    # 开头
    print("┌─ 开头 " + "─" * 50)
    print("\n".join(lines[:head]))

    # 中间（从正中央取 mid 行）
    mid_start = max(head, n // 2 - mid // 2)
    mid_end = min(n - tail, mid_start + mid)
    skipped_before = mid_start - head
    print(f"\n├─ …跳过 {skipped_before} 行… 中段抽样（第 {mid_start+1}–{mid_end} 行）" + "─" * 12)
    print("\n".join(lines[mid_start:mid_end]))

    # 结尾
    skipped_after = (n - tail) - mid_end
    print(f"\n├─ …跳过 {skipped_after} 行… " + "─" * 40)
    print("└─ 结尾 " + "─" * 50)
    print("\n".join(lines[-tail:]))


if __name__ == "__main__":
    main()
