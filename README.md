# memory-optimizer

WorkBuddy 记忆优化技能。解决两类问题：**记忆写错层级**（用户级 / 项目级混淆）与**记忆腐化**（重复、冲突、过时、超限）。提供三项能力：写入层级自动判定、记忆健康检查、每日日志 30 天留存蒸馏。

## 功能

- **写入层级判定**：用户说"记住 / 保存"或 Agent 需持久化信息时，自动判断写入
  `~/.workbuddy/MEMORY.md`（用户级，跨项目，4000 字符上限）还是
  `<workspace>/.workbuddy/memory/MEMORY.md`（项目级，3000 字符上限）。
  层级不确定时主动提问，不猜测。
- **记忆健康检查**：扫描各层字符上限、超 30 天日志、层内 / 跨层重复、过时标记；
  Agent 在此基础上补充判定脚本无法识别的冲突与语义过时。
- **每日日志蒸馏**：超 30 天的日志提炼"经验教训"合并进项目 `MEMORY.md`；
  删除原日志前必须向用户确认无遗漏。

## 安装

将本仓库内容复制到 WorkBuddy 技能目录（目录名须为 `memory-optimizer`）：

```bash
# 用户级（跨所有项目，推荐）
cp -r memory-optimizer ~/.workbuddy/skills/

# 或项目级（仅当前项目协作共享）
cp -r memory-optimizer <workspace>/.workbuddy/skills/
```

也可在 WorkBuddy 技能管理中直接导入本仓库。

## 使用

- **触发**：用户说"记住…"、要求"检查记忆 / 整理记忆 / 清理日志"、或任务收尾需写记忆且层级不确定时自动加载；也可手动 `@memory-optimizer`。
- **健康检查脚本**（在技能目录内运行，或传入脚本绝对路径）：

```bash
python3 scripts/check_memory_health.py \
    --workspace "<workspace绝对路径>" \
    --home "<用户.workbuddy绝对路径>" \
    --days 30
# 加 --json 输出结构化结果
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
- 详细记忆系统说明见 `references/memory-architecture.md`。
- 许可证：本仓库未附带 LICENSE，如需公开发布请自行添加（建议 MIT）。
