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

## 姊妹仓库

- [liya-subtraction-skill](https://github.com/feverZHONG/liya-subtraction-skill) —— 技能库做减法：冗余检测 / 拆薄 / 合并 / 归档判断
- [liya-persona-authoring](https://github.com/feverZHONG/liya-persona-authoring) —— 给 AI agent 写身份文件（SOUL.md 类）：创作流程 / 砍装饰留行为 / 减法与漂移对照
- [liya-sillytavern-cards](https://github.com/feverZHONG/liya-sillytavern-cards) —— 酒馆角色卡写法：V2 格式 / PList+Ali:Chat / 三个 Python 工具
- [liya-sillytavern-worldbook](https://github.com/feverZHONG/liya-sillytavern-worldbook) —— 酒馆世界书（Lorebook）：触发链源码实证 + 体检 / 模拟 / 生成工具
- [liya-vision-recognition-traps](https://github.com/feverZHONG/liya-vision-recognition-traps) —— 视觉模型识图陷阱：22 条实测与对策（附真 OCR 通道、生图物理体检、两图差分）
- [liya-chat-game-referee](https://github.com/feverZHONG/liya-chat-game-referee) —— 群聊小游戏裁判：扫雷 / 五子棋 / 大话骰 / 骗子牌 / 掷骰决斗，一位裁判带六个引擎
- [liya-spy-game](https://github.com/feverZHONG/liya-spy-game) —— 谁是卧底：黑板规则 / 出题方法论 / 词库验证 / 身份分配器
- [liya-sea-turtle-soup](https://github.com/feverZHONG/liya-sea-turtle-soup) —— 海龟汤：推理方法论 + 档案流水线（turtle CLI）
- [liya-delegation-and-verification](https://github.com/feverZHONG/liya-delegation-and-verification) —— 委派与验收：任务书写法 / 并行隔离 / 把「自报」验成事实
- [liya-tavern-card-refinement](https://github.com/feverZHONG/liya-tavern-card-refinement) —— 酒馆角色卡精修：7 字段清单 / 槽位归位 / 6 类断言 / 可用性验收
- [liya-prose-quality-metrics](https://github.com/feverZHONG/liya-prose-quality-metrics) —— 稿子读起来「平」怎么办：先量再改（对话占比·句长σ·标点谱）＋ 7 个工具
- [liya-ruozhiba-wordbank](https://github.com/feverZHONG/liya-ruozhiba-wordbank) —— 弱智吧题防御手册：160 道逐题拆解 + 三连防御法（拆前提→指谬误→反杀）
- [liya-subtitle-proofreading](https://github.com/feverZHONG/liya-subtitle-proofreading) —— 字幕校对 / 重建 / 外挂 SRT（5 个纯标准库工具）
- [liya-corpus-line-mining](https://github.com/feverZHONG/liya-corpus-line-mining) —— 从语料 / 会话库挖可复用原句：候选池筛选 + 人审落库（零依赖）
- [liya-story-revision-plan](https://github.com/feverZHONG/liya-story-revision-plan) —— 小说全稿修订方案：评估 / 缺口清单 / 逐章大纲 / 信息融合 / 优先级
- [liya-dev-workflow](https://github.com/feverZHONG/liya-dev-workflow) —— 开发全流程方法论：环境侦查 / 计划 / spike / TDD / 调试 / 推送排障 / 同步验收
- [liya-news-verification](https://github.com/feverZHONG/liya-news-verification) —— 验证伞：轻量核查 / 交付前多源验证 / 链接危险识别 / 厂商官宣核实 / 链接考古
- [liya-knowledge-persistence](https://github.com/feverZHONG/liya-knowledge-persistence) —— 知识持久化：信息该放记忆层 / 文件 / 技能库的分层规范
- [liya-incident-review](https://github.com/feverZHONG/liya-incident-review) —— 社群事件复盘：素材收集 → 时间线重构 → 交叉验证 → 矛盾管理（输出理解不输出建议）
- [liya-source-code-investigation](https://github.com/feverZHONG/liya-source-code-investigation) —— 外部项目调查：源码审计 / 拆包分层 / 数据实测 / 身份链（结论导向，非取用）
- [liya-character-voice-simulation](https://github.com/feverZHONG/liya-character-voice-simulation) —— 角色声线推演：锚点表双向用——分队推演（隔离上下文）＋ 反查认说话人
- [liya-dialogue-system-builder](https://github.com/feverZHONG/liya-dialogue-system-builder) —— 台词系统脚手架：触发维度画格子 / 模板+变量兜底 / 覆盖率验证（含 17 子命令工作台与示例角色）

## 许可

- **代码**（`scripts/`）：[MIT](LICENSE)
- **文档**（`SKILL.md`、`references/`、本 README 正文）：[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) —— 自由使用、改编、商用，**但要署名**（莉娅 / [@feverZHONG](https://github.com/feverZHONG)）并注明来源。

---

维护：[莉娅](https://github.com/feverZHONG) · 宇宙美好记录官
