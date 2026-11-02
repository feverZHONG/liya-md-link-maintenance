#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_md_links.py —— md 文档库断链扫描/自动修复

用法：
  fix_md_links.py <dir> [--check|--fix] [--root <库根>]

  --check (默认)  只扫描，列出断链
  --fix           自动修复：反引号 .md 引用目标不存在时，按 basename 全库找
                  唯一真实文件，生成正确相对路径替换（同目录正确的引用不动）
  --root          仓库根（默认自动探测：含 skills/ 的上级），用于识别跨库引用

内置排除（不算断链）：
  - 模板占位符：type-N、<real|role>、<人物>、通配 *
  - 跨库引用：相对仓库根存在的路径（其他 skill 目录/...、workspace/...）
  - 重名 basename（多个 INDEX.md 等）：跳过，需手动修

注意：
  - 只处理反引号里的 .md 引用；目录引用（`types/`）不在此列，需手动改
  - 故意写的反面教材（如「别写 type-1-完美主义者.md」）目标不存在但应保留，
    会被列出来——人工确认后放行
"""
import argparse
import os
import re
import sys


def _data_root():
    """数据根探测（可迁移/可发布）：$HERMES_ROOT ＞ $SKILL_ROOT ＞ 脚本上溯 ＞ ~/.hermes ＞ 家目录。
    命中判据：该层下存在 skills/ 目录。"""
    for _env in ("HERMES_ROOT", "SKILL_ROOT"):
        _v = os.environ.get(_env)
        if _v and os.path.isdir(os.path.join(_v, "skills")):
            return _v
    _here = os.path.dirname(os.path.abspath(__file__))
    _cands = [os.path.abspath(os.path.join(_here, *([".."] * _n))) for _n in range(1, 5)]
    _cands += [os.path.expanduser("~/.hermes"), os.path.expanduser("~")]
    for _c in _cands:
        if os.path.isdir(os.path.join(_c, "skills")):
            return _c
    return os.path.abspath(os.path.join(_here, "..", "..", ".."))


BASE = _data_root()  # 数据根自动探测


REF_RE = re.compile(r'`([^`]+\.md)`')
def is_placeholder(ref):
    # 与 mdcheck.py 对齐（2026-10-18）：花括号是模板骨架的常用占位（`{角色名}.md`、`{{TODAY-1}}`），
    # 不排掉会把模板示例当真断链天天报 —— 实测 212 条噪音来自这里。
    if '<' in ref or '{' in ref or '*' in ref or '?' in ref or '##' in ref:
        return True
    # `references/x.md`、`A/x.md` 这类是文档里的占位示例（2026-10-18：13 条噪音）
    if os.path.basename(ref).lower() == 'x.md':
        return True
    # 模板模式：日期占位、xxx、省略号（2026-10-18：再清 90 条噪音）
    if 'YYYY' in ref or 'yyyy' in ref or 'xxx' in ref.lower() or '…' in ref or '...' in ref:
        return True
    # 编号/名称占位：NN-阶段名、XX章、地域-X、文件名.md（2026-10-18 第三轮）
    if 'NN' in ref or 'XX' in ref or ref.endswith('-X.md') or ref.endswith('文件名.md'):
        return True
    # 命令示例被反引号抓进来（`grep -c 旧BV号 INDEX.md`）——首词是 shell 命令就不是链接
    if ref.split() and ref.split()[0] in ('grep', 'awk', 'sed', 'find', 'cat', 'ls', 'rg', 'python3', 'wc', 'head', 'tail', 'sort', 'uniq', 'git'):
        return True
    return any(m in ref for m in ('type-N', 'demo', '示例', '<id>'))


def collect_md_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        # 跳过 .git / venv / cache
        dirnames[:] = [d for d in dirnames if d not in ('.git', '.venv', 'venv', '__pycache__', 'cache')]
        for f in filenames:
            if f.endswith('.md'):
                yield os.path.join(dirpath, f)


def skill_root_of(path):
    """往上找最近的含 SKILL.md 的目录。2026-10-18 新增：
    大量断链是「按 skill 根写路径」（references/x.md 写在 characters/ 里），
    照 skill 根能唯一解析的，就是路径基准错，不是文件没了。"""
    d = os.path.dirname(os.path.abspath(path))
    while True:
        if os.path.exists(os.path.join(d, 'SKILL.md')):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def build_name_index(root):
    """basename -> [真实路径]。重名路径列表长度 >1 时跳过。"""
    idx = {}
    for path in collect_md_files(root):
        idx.setdefault(os.path.basename(path), []).append(path)
    return idx


def main():
    ap = argparse.ArgumentParser(description='md 断链扫描/修复')
    ap.add_argument('dir', help='要扫描的目录')
    ap.add_argument('--check', action='store_true', help='只扫描（默认）')
    ap.add_argument('--fix', action='store_true', help='自动修复断链')
    ap.add_argument('--root', default=BASE, help='仓库根，识别跨库引用')
    ap.add_argument('--all', action='store_true', help='打印全部条目（默认只抽样 10-15 条）')
    args = ap.parse_args()

    root = os.path.abspath(args.dir)
    LIM = 10**9 if args.all else 15
    name_index = build_name_index(root)
    broken, cross_lib, placeholders, dup, none, guess = [], [], [], [], [], []
    checked = 0

    for path in collect_md_files(root):
        for i, line in enumerate(open(path, encoding='utf-8'), 1):
            for m in REF_RE.finditer(line):
                ref = m.group(1)
                checked += 1
                if is_placeholder(ref):
                    placeholders.append(f'{os.path.relpath(path, root)}:{i}: {ref}')
                    continue
                target = os.path.normpath(os.path.join(os.path.dirname(path), ref))
                if os.path.exists(target):
                    continue
                # 跨库引用：相对仓库根存在 = 素材来源标注，不算断
                # ⚠️ 必须带目录分隔符（2026-10-18 修）：裸名 `README.md` 会被
                # <库根>/README.md 误吞成「合法跨库」，实际是本 skill 缺这文件。
                if '/' in ref and os.path.exists(os.path.join(args.root, ref)):
                    cross_lib.append(f'{os.path.relpath(path, root)}:{i}: {ref}')
                    continue
                basename = os.path.basename(ref)
                # 候选判定（2026-10-18 加 skill 根这一路）：先按 skill 根解析，
                # 再退回「全库唯一 basename」。两条都只接受唯一答案，重名一律不动。
                cand = None
                sr = skill_root_of(path)
                if sr:
                    alt = os.path.normpath(os.path.join(sr, ref))
                    if os.path.exists(alt):
                        cand = alt
                if cand is None:
                    bns = name_index.get(basename, [])
                    if len(bns) == 1:
                        cand = bns[0]
                    elif len(bns) > 1:
                        dup.append(f'{os.path.relpath(path, root)}:{i}: {ref}')
                        continue
                    else:
                        none.append(f'{os.path.relpath(path, root)}:{i}: {ref}')
                        continue
                # 保护：候选跑到了别的 skill 里，而 ref 第一段又不是 skill 名 ——
                # 这是「裸名撞到别家同名文件」，语义可能完全变了，只能人判（2026-10-18）。
                if cand and sr and not cand.startswith(sr + os.sep):
                    head = ref.split('/')[0]
                    if not os.path.isdir(os.path.join(root, head)):
                        guess.append(f'{os.path.relpath(path, root)}:{i}: {ref} -> {os.path.relpath(cand, root)}')
                        continue
                broken.append((path, i, ref, cand))

    print(f'checked {checked} refs | 跨库 {len(cross_lib)} | 占位 {len(placeholders)} | '
          f'可修 {len(broken)} | 跨skill裸名 {len(guess)} | 重名跳过 {len(dup)} | 全库无此文件 {len(none)}')
    if cross_lib:
        print(f'\n跨库引用（相对 {args.root}，不算断）:')
        for x in cross_lib[:LIM]:
            print('  ', x)
    if placeholders:
        print(f'\n模板占位（不算断）:')
        for x in placeholders[:LIM]:
            print('  ', x)
    if dup:
        print(f'\n重名跳过（需人工判断）{len(dup)} 处:')
        for x in dup[:LIM]:
            print('  ', x)
    if guess:
        print(f'\n跨 skill 撞名（裸名撞到别家同名文件，需人判）{len(guess)} 处:')
        for x in guess[:LIM]:
            print('  ', x)
    if none:
        print(f'\n全库无此文件（需人工）{len(none)} 处:')
        for x in none[:LIM]:
            print('  ', x)
    if not broken:
        print('\n无可自动修复的断链。')
        return 0

    print(f'\n可修 {len(broken)} 处:')
    for path, i, ref, cand in broken:
        print(f'  {os.path.relpath(path, root)}:{i}: {ref} -> {os.path.relpath(cand, os.path.dirname(path))}')

    if args.fix:
        n = 0
        for path, i, ref, cand in broken:
            rel = os.path.relpath(cand, os.path.dirname(path))
            text = open(path, encoding='utf-8').read()
            old = f'`{ref}`'
            new = f'`{rel}`'
            if old in text:
                text = text.replace(old, new, 1)
                open(path, 'w', encoding='utf-8').write(text)
                print(f'  修复 {os.path.relpath(path, root)}:{i}: {ref} -> {rel}')
                n += 1
        print(f'修复完成 {n} 处。重跑 --check 验证。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
