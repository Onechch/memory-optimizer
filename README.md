# memory-optimizer

WorkBuddy 记忆优化技能。解决两类问题：**记忆写错层级**（用户级 / 项目级混淆）与**记忆腐化**（重复、冲突、过时、超限）。提供三项能力：写入层级自动判定、记忆健康检查、每日日志 30 天留存蒸馏。

## 功能

- **写入层级判定**：用户说"记住 / 保存"或 Agent 需持久化信息时，自动判断写入
  `~/.workbuddy/MEMORY.md`（用户级，跨项目，4000 字符上限）还是
  `<workspace>/.workbuddy/memory/MEMORY.md`（项目级，3000 字符上限）。
  层级不确定时主动提问，不猜测。
- **记忆健康检查**：扫描各层字符上限、超 30 天日志、层内 / 跨层重复、过时标记、
  **报告冗余**（传入 `--reports-dir` 后，标出与本次报告逐字重复的条目）；
  Agent 在此基础上补充判定脚本无法识别的冲突与语义过时。
- **写前冗余检查（报告去重）**：写入任何记忆前，若信息已在本轮对话产出的报告中，
  只记**来源指针**（位置 + 关键词）而非全文复制；仅报告未含且具长期价值者才存独立条目，
  以控制记忆总量、避免冗余负担。
- **每日日志蒸馏**：超 30 天的日志提炼"经验教训"合并进项目 `MEMORY.md`；
  删除原日志前必须向用户确认无遗漏。

## 安装

将本仓库内容放到 WorkBuddy 技能目录（目录名须为 `memory-optimizer`）：

```bash
# 用户级（跨所有项目，推荐）
cp -r memory-optimizer ~/.workbuddy/skills/

# 或项目级（仅当前项目协作共享）
cp -r memory-optimizer <workspace>/.workbuddy/skills/
```

也可在 WorkBuddy 技能管理中直接导入本仓库。

### 对话式安装（推荐）

无需手动敲命令——直接对你的智能体说一句话即可。支持执行命令 / 联网下载的智能体（如 WorkBuddy）会自动完成下载与安装：

- **WorkBuddy / 通用智能体**：
  > 请安装 GitHub 上的 memory-optimizer 记忆优化技能，仓库地址是 https://github.com/Onechch/memory-optimizer.git，安装到你的用户级技能目录。

- **若智能体自带技能市场**（如 WorkBuddy 的技能市场安装）：
  > 安装 memory-optimizer 技能

底层执行的命令（供参考 / 排错）：

```bash
# 方式 A：git clone 直接落入技能目录（目录名自动为 memory-optimizer）
git clone https://github.com/Onechch/memory-optimizer.git \
    ~/.workbuddy/skills/memory-optimizer

# 方式 B：下载仓库 zip 包后解压（无需 git）
curl -L https://github.com/Onechch/memory-optimizer/archive/refs/heads/main.zip -o /tmp/memory-optimizer.zip
unzip /tmp/memory-optimizer.zip -d /tmp/
cp -r /tmp/memory-optimizer-main ~/.workbuddy/skills/memory-optimizer
```

> 说明：仓库所有者为 `Onechch`；若默认分支为 `master` 请把上面两处的 `main` 改为 `master`。
> 安装后 WorkBuddy 会在下次会话自动识别该技能，无需额外启用；其他智能体按其技能目录约定放置即可。

## 使用

- **触发**：用户说"记住…"、要求"检查记忆 / 整理记忆 / 清理日志"、或任务收尾需写记忆且层级不确定时自动加载；也可手动 `@memory-optimizer`。
- **健康检查脚本**（在技能目录内运行，或传入脚本绝对路径）：

```bash
python3 scripts/check_memory_health.py \
    --workspace "<workspace绝对路径>" \
    --home "<用户.workbuddy绝对路径>" \
    --days 30 \
    --reports-dir "<本次对话产出报告所在目录>"
# 加 --json 输出结构化结果；--reports-dir 可省略（省略则不检测报告冗余）
```

`<workspace绝对路径>` 与 `<用户.workbuddy绝对路径>` 须使用**带盘符的 Windows 绝对路径**，
例如 `D:/project/xxx` 与 `C:/Users/你的用户名/.workbuddy`。
`python3` 可用 WorkBuddy 受管 Python 或系统 Python 3 替代。

## 目录结构

```
memory-optimizer/
├── SKILL.md                    # 技能主说明与流程（必读）
├── README.md                   # 本文件
├── .gitignore                  # 仓库 hygiene
├── references/
│   └── memory-architecture.md  # 三层记忆系统结构、路径、上限、留存规则
└── scripts/
    └── check_memory_health.py  # 确定性记忆健康检查脚本
```

## 说明

- 所有破坏性操作（删除日志、改写 `MEMORY.md`）均需用户确认后执行，绝不静默执行。
- **记忆写入原则**：报告可查的信息只记来源指针（`- [来源] <摘要> | 位置：<路径> | 关键词：<词>`），
  不重复存储全文；仅报告未含且具长期价值者才作为独立条目存储。详见 `references/memory-architecture.md`。
- 详细记忆系统说明见 `references/memory-architecture.md`。
- 许可证：本仓库未附带 LICENSE，如需公开发布请自行添加（建议 MIT）。
