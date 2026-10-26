# Local Agent Instructions

## 表达

- 默认中文，仅在用户明确要求时切换；英文提问、术语或粘贴材料不触发切换。代码、命令、标识符和报错保留原文。表达偏好不减少必要的求解、检索和验证。

## Git 与协作

- 保留用户已有修改：与任务重叠时先理解并兼容，无法安全区分再询问；不擅自覆盖、还原、暂存或清理。
- 仅在用户要求或已批准流程包含提交时 commit；一个逻辑变化一个 commit，只暂存本次改动。未经授权不 push、改 remote、创建/修改/合并远端 PR 或发布版本。回退已提交修改优先用 `git revert`。
- 复杂或高风险代码改动优先用独立分支，需要并行或隔离当前工作区时用 worktree，小改动沿用当前检出。互不依赖且文件范围可分离的部分可交给子 Agent，事先约定文件归属，并提供足以独立实施和验证的目标、必要上下文、文件范围、约束与验收条件；共享文件、界面和证据索引由主 Agent 串行维护，成果由主 Agent 统一整合、验证。
- 上述协作流程中的提交、合并和归档清理须在明确授权或已批准流程内。串行更新并验证任务分支，再以 `git merge --ff-only` 合入整合分支，由主 Agent 复核最终提交并综合验证；目标分支推进时先更新任务分支并复验受影响内容，不用强制重置绕过冲突或快进失败。
- 对上述流程中已合并任务的最终提交打带注释的 `archive/YYYY-MM-DD/<完整分支名>` 标签，记录任务和证据入口；同名标签核对提交身份，不覆盖。确认产物已保全且提交可达后，正常移除任务工作树，用 `git branch -d` 删除已合并分支。

## Agent skills

### Issue tracker

Issues and specs live as markdown files under `.scratch/<feature-slug>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the default labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, and `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Use the single-context layout: root `GLOSSARY.md` and `docs/adr/`. See `docs/agents/domain.md`.
