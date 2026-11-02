#!/usr/bin/env python3
"""全库 markdown 链接校验（只查不修）——扫描 [文本](目标) 形态的相对链接。

与 fix_md_links.py 互补：
  fix_md_links.py  → 管 **反引号** `.md` 引用，可 --fix 自动补相对路径
  本脚本           → 管 **markdown 链接** `[文本](路径.md)`，只校验不修
                     （目标该改成什么常需人判断：改名 / 占位符 / 库外描述）

用法：
    python3 check_md_links.py <目录> [<目录> ...]
    python3 check_md_links.py <目录> [<目录>...]

退出码：0 = 无断链；1 = 有断链（逐条列在 stdout）；2 = 没给目录。
"""

import os
import re
import sys

LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
SKIP_PREFIX = ("http", "#", "mailto:")


def check(roots):
    scanned = 0
    broken = []
    for root in roots:
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in filenames:
                if not name.endswith(".md"):
                    continue
                path = os.path.join(dirpath, name)
                try:
                    text = open(path, encoding="utf-8").read()
                except UnicodeDecodeError:
                    print("!! 非 utf-8，跳过:", path)
                    continue
                scanned += 1
                for m in LINK_RE.finditer(text):
                    target = m.group(2).strip()
                    if target.startswith(SKIP_PREFIX):
                        continue
                    target = target.split("#", 1)[0]
                    if not target:
                        continue
                    resolved = os.path.normpath(os.path.join(dirpath, target))
                    if not os.path.exists(resolved):
                        broken.append((path, m.group(1)[:30], target))
    return scanned, broken


def main():
    roots = sys.argv[1:]
    if not roots:
        print(__doc__)
        return 2
    scanned, broken = check(roots)
    print(f"scanned {scanned} md | broken {len(broken)}")
    for path, label, target in broken:
        print(f"  {path}  [{label}] -> {target}")
    if broken:
        print(
            "\n按病分修：目标改名→改成真名并全库 grep 旧名；层级错→数跳数（同批新写的链接最易犯）；"
            "占位符 (…)→补真链或改纯文本；库外描述引用→忽略。"
        )
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
