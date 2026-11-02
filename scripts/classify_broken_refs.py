#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""classify_broken_refs.py —— 把 fix_md_links --check --all 的余量按成因分档。

用法：
  python3 scripts/fix_md_links.py skills --root <库根> --check --all > /tmp/scan.txt
  python3 skills/md-link-maintenance/scripts/classify_broken_refs.py /tmp/scan.txt --root <库根>

输出（只对「全库无此文件」段分档，重名另列）：
  C1 示例/占位   工具还不认的写法（`-X.md`、`NN-slug.md`、`某档案库/…`）
  C2 历史存在过   basename 在 git 历史里出现过（改名/删除后引用没跟）——出映射批量改
  C4 别处有同名   目标在库内别的目录（路径写错，多可批量补全成根相对路径）
  C5 真缺         哪儿都没有（补档 or 删引）
  D1 同 skill 重名 / D2 跨 skill 重名

修次序：C4 → C2 → C1（补白名单）→ D1 → C5/D2。前两档机械可批量，啃完真缺才浮出来。
分类结果同时落 JSON（--json-out，默认与输入同目录），供批修脚本直接消费。
"""
import argparse
import collections
import json
import os
import re
import subprocess
import sys

SEC_NONE = '全库无此文件（需人工）'
SEC_DUP = '重名跳过（需人工判断）'
LINE_RE = re.compile(r'^(?P<f>[^:]+):(?P<l>\d+): (?P<ref>.+)$')
# 与 mdcheck.is_placeholder / fix_md_links.is_placeholder 保持同口径
PH_RE = re.compile(r'(<[^>]*>|\{[^}]*\}|[*?]|\.\.\.|-X\.md|YYYY|NN-slug|示例|模板)')
SKIP_DIRS = ('/.git', '/.venv', '/node_modules', '/cache/terminal', '/workspace/tmp', '/temp/')


def _default_root():
    """默认仓库根：从本脚本上溯找含 skills/ 的一层；找不到退回上三级。"""
    here = os.path.dirname(os.path.abspath(__file__))
    d = here
    for _ in range(6):
        d = os.path.dirname(d)
        if os.path.isdir(os.path.join(d, "skills")):
            return d
    return os.path.abspath(os.path.join(here, "..", "..", ".."))


def parse_scan(path):
    """解析 fix_md_links --check --all 的输出：按段收 `文件:行: 引用`。"""
    out = {SEC_NONE: [], SEC_DUP: []}
    cur = None
    for ln in open(path, encoding='utf-8', errors='replace'):
        ln = ln.rstrip('\n')
        hit = next((s for s in out if ln.startswith(s)), None)
        if hit:
            cur = hit
            continue
        if ln.startswith('   ') and cur:
            m = LINE_RE.match(ln.strip())
            if m:
                out[cur].append((m.group('f'), m.group('ref')))
        elif ln and not ln.startswith(' '):
            cur = None
    return out


def build_name_index(root):
    idx = collections.defaultdict(list)
    for dp, dn, fn in os.walk(root):
        if any(s in dp for s in SKIP_DIRS):
            continue
        for f in fn:
            idx[f].append(os.path.join(dp, f))
    return idx


def git_history_names(root):
    try:
        r = subprocess.run(['git', 'log', '--all', '--name-only', '--pretty=format:'],
                           cwd=root, capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired):
        print('⚠ 取 git 历史失败，C2 档会并入 C5', file=sys.stderr)
        return set()
    return {os.path.basename(x) for x in r.stdout.split('\n') if x.strip()}


def main():
    ap = argparse.ArgumentParser(description='断链余量按成因分档')
    ap.add_argument('scan', help='fix_md_links --check --all 的输出文件')
    ap.add_argument('--root', default=None, help='仓库根（默认自动探测：含 skills/ 的上级）')
    ap.add_argument('--skills', default=None, help='技能目录（默认 <root>/skills）')
    ap.add_argument('--json-out', default=None)
    ap.add_argument('--no-history', action='store_true', help='跳过 git 历史（大仓慢时用）')
    args = ap.parse_args()

    root = os.path.abspath(args.root or _default_root())
    skills = os.path.abspath(args.skills or os.path.join(root, 'skills'))
    parsed = parse_scan(args.scan)
    none, dup = parsed[SEC_NONE], parsed[SEC_DUP]
    idx = build_name_index(root)
    hist = set() if args.no_history else git_history_names(root)

    buckets = collections.defaultdict(list)
    for f, ref in none:
        bn = os.path.basename(ref)
        if PH_RE.search(ref):
            k = 'C1 示例/占位'
        elif bn in hist:
            k = 'C2 历史存在过(改名/删除)'
        elif bn in idx:
            k = 'C4 别处有同名(路径写错)'
        else:
            k = 'C5 真缺'
        buckets[k].append((f, ref))

    print('重名 %d ｜ 查无 %d' % (len(dup), len(none)))
    for k in sorted(buckets):
        print('  %-24s %d' % (k, len(buckets[k])))
        top = collections.Counter(x[0].split('/')[0] for x in buckets[k]).most_common(5)
        for s, n in top:
            print('        %4d  %s' % (n, s))

    d_same = sum(1 for f, ref in dup
                 if all(c.startswith(os.path.join(skills, f.split('/')[0]))
                        for c in idx.get(os.path.basename(ref), [])))
    print('  D1 同 skill 重名 %d ｜ D2 跨 skill 重名 %d' % (d_same, len(dup) - d_same))

    out = args.json_out or os.path.join(os.path.dirname(os.path.abspath(args.scan)), 'links-buckets.json')
    json.dump({k: v for k, v in buckets.items()}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('落盘 %s' % out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
