# 文档库引用链维护 · md-link-maintenance

> md 文件被移动、改名、分目录之后，反引号里的相对引用会**静默断掉**——没有报错，只有下次按图索骥时撞墙。
> 这套东西管三件事：**断链扫描与自动修复、markdown 链接校验、整个文档库重构时的安全流程**。

## 这是什么

任何靠「文件 + 引用」组织起来的 md 库都会遇到这个问题：拆薄一个 skill、把 references 按主题分目录、把一篇长文拆成几章——文件一动，引用就断。手工找断链靠不住（一次能漏几十条），所以这里给了三个脚本和一套流程。

| 脚本 | 管什么 |
|:--|:--|
| `scripts/fix_md_links.py` | 扫描并修复**反引号**形式的 `.md` 相对引用（`references/a.md`、裸名 `a.md`、`../b.md` 都查）；`--check` 只报不动，`--fix` 就地改 |
| `scripts/check_md_links.py` | 校验标准 markdown 链接 `[文本](路径.md)`，只查不修 |
| `scripts/classify_broken_refs.py` | 修不动的那些**按成因分档**（示例/占位残留、历史上存在过、真缺失），才知道先修哪档、哪些不用修 |

## 怎么用

把本仓放进你的 skills 目录（目录名用 `md-link-maintenance`）：

```bash
git clone https://github.com/feverZHONG/liya-md-link-maintenance.git <你的数据根>/skills/md-link-maintenance
```

先扫一遍看看有多少：

```bash
python3 scripts/fix_md_links.py skills --root <你的数据根> --check --all
```

确认后修复：

```bash
python3 scripts/fix_md_links.py skills --root <你的数据根> --fix --all
```

## 三条最容易踩的

1. **位置参数是目录路径，不是 skill 名**——写 `fix_md_links.py 某个skill名` 会扫到 0 个文件、打印「checked 0 refs、可修 0」，看着像全对，其实是没扫到。
2. **`--root` 决定「什么算跨库引用」**：库内统一用「库根相对」写法时，不带 `--root` 会把所有跨库引用当断链报——同一次扫描可能差出几百条假阳性，反之指错根也会漏。
3. **「0 入链的孤儿档」不等于废料**：先查有没有脚本按路径模式读它、是不是内容型资料，再决定删不删。

## 目录

- `SKILL.md` —— 完整流程（摸依赖面 → git mv → 修引用 → 验证 → 同步）与判据
- `references/` —— 分场景细节：引用形态、改名操作、编号重排、重写与踩坑
- `scripts/` —— 上面那三个脚本
