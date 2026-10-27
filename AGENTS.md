# Local Agent Instructions

## 表达

- 默认中文，仅在用户明确要求时切换；英文提问、术语或粘贴材料不触发切换。代码、命令、标识符和报错保留原文。表达偏好不减少必要的求解、检索和验证。

## Git 与协作

- 保留用户已有修改：与任务重叠时先理解并兼容，无法安全区分再询问；不擅自覆盖、还原、暂存或清理。
- 仅在用户要求或已批准流程包含提交时 commit；一个逻辑变化一个 commit，只暂存本次改动。未经授权不 push、改 remote、创建/修改/合并远端 PR 或发布版本。回退已提交修改优先用 `git revert`。
- 复杂或高风险代码改动优先用独立分支，需要并行或隔离当前工作区时用 worktree，小改动沿用当前检出。互不依赖且文件范围可分离的部分可交给子 Agent，事先约定文件归属，并提供足以独立实施和验证的目标、必要上下文、文件范围、约束与验收条件；共享文件、界面和证据索引由主 Agent 串行维护，成果由主 Agent 统一整合、验证。
- 上述协作流程中的提交、合并和归档清理须在明确授权或已批准流程内。串行更新并验证任务分支，再以 `git merge --ff-only` 合入整合分支，由主 Agent 复核最终提交并综合验证；目标分支推进时先更新任务分支并复验受影响内容，不用强制重置绕过冲突或快进失败。
- 对上述流程中已合并任务的最终提交打带注释的 `archive/YYYY-MM-DD/<完整分支名>` 标签，记录任务和证据入口；同名标签核对提交身份，不覆盖。确认产物已保全且提交可达后，正常移除任务工作树，用 `git branch -d` 删除已合并分支。

## 书籍处理

- 默认流程：非 OCR 提取（pypdf 文本层 + 图片/页面抽取）→ 直译或重排为 `.qmd` → agy 忠实润色 → 主 Agent 编排与排版核验 → 用户批准具体版本 → 合并 `main`、推送并部署 Pages。原书代码一律不执行，页面只做静态展示。
- 模型分工固定：直译用本地 pi 的 `openai-codex/gpt-6.1-terra`（thinkingLevel `low`）经 pi-subagents worker 按互不重叠章节委派；润色用 `agy.exe` 的 `gemini-3.8-flash-low` 叠加 `humanizer-zh` skill。不得用其他模型顶替；不可用时停下说明并询问。
- 润色只给译文与术语表，不提供原文；只调措辞与可读性，不改术语译名、公式、代码、数值、单位、引用编号与图注含义。译后由主 Agent 与原书缓存逐项比对，保留润色前后 diff 与调用证据。
- 完整度：图片与图表、代码、公式、表格、脚注、参考文献、交叉引用、链接与各类跳转编号都不得遗漏；不以摘要代译，分页处不断章。
- 资产：原始 PDF 与提取缓存（`**/raw/**`、`.local/`）不提交；站点只提交译文、必要图片（`metadata.yaml` 的 `assets` 声明，允许 png/jpg/jpeg/gif/webp）与元数据。
- 可见性：书籍翻译属衍生作品。公开发布须用户对该版本明确批准；未获版权方授权时页面如实标注「非官方直译、仅个人学习用途、未获授权」，不对外宣传、不加推广性元数据。风险由用户承担，代理不得声称已获授权或已合规。
- 发布门禁：`catalog/books.yaml` 登记、`review.status: approved`（含 `approved_by`、`approved_at`、`evidence_path`）、`provenance.json` 全部 `verified` 三者同时满足才可上 Pages；本地预览只走 `catalog/preview.yaml`，永不进入 `dist/`。

## Agent skills

### Issue tracker

Issues and specs live as markdown files under `.scratch/<feature-slug>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the default labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, and `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Use the single-context layout: root `GLOSSARY.md` and `docs/adr/`. See `docs/agents/domain.md`.
