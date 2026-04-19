---
name: git-commit-message
description: Generate precise git commit messages for this repository from staged or working tree diffs. Use when the user asks for commit messages, 提交信息, 提交说明, commit 文案, git commit, staged changes, or wants to summarize code changes in this project's existing style.
disable-model-invocation: true
---

# Git Commit Message

## Purpose

Generate commit messages that match this repository's existing style.

## Invocation

- Invoke manually in Cursor Chat with `/git-commit-message`.
- Prefer staged changes. If nothing is staged, analyze the current working tree diff.
- Return only the final commit message unless the user explicitly asks for explanation or alternatives.

## Repository style

- Use a Conventional Commit type prefix such as `feat:`, `fix:`, `perf:`, `refactor:`, `docs:`, `test:`, or `chore:`.
- The summary is usually written in simplified Chinese.
- Prefer a single-line subject only. Do not add a body unless the user explicitly asks for one or the change is too complex to summarize in one line.
- Keep the subject specific to the actual behavior change. Avoid vague summaries like `更新代码` or `修改逻辑`.
- Do not invent scope unless the user explicitly requests `type(scope): subject`.

## How to analyze changes

1. Inspect staged changes first. If nothing is staged, inspect the working tree diff.
2. Identify the main user-visible or behavior-changing effect, not every small edit.
3. Choose the most accurate type:
   - `feat:` new behavior, new logic, or new supported scenario
   - `fix:` bug fix, wrong behavior correction, recovery handling, edge case handling
   - `perf:` performance optimization or faster / lighter logic
   - `refactor:` structural rewrite without intended behavior change
   - `docs:` documentation only
   - `test:` tests only
   - `chore:` maintenance, config, tooling, cleanup
4. Write one concise Chinese summary that explains the primary change.
5. Match the tone already used in this repository: direct, concrete, and action-oriented.

## Output rules

- Default to outputting only the final commit subject.
- Do not wrap the result in backticks unless the user asks for raw code formatting.
- Do not output multiple alternatives unless the user asks for options.
- If the change mixes multiple categories, choose the dominant one.
- If the diff is too broad to summarize honestly, say so and provide the best high-level summary.

## Preferred wording patterns

- `feat: 添加...`
- `feat: 更新...，优化...`
- `fix: 修复...`
- `fix: 修复...，确保...`
- `perf: 优化...`

## Good examples

Input: add special handling when signal orb elimination target equals 2 in phase 2
Output: `feat: 在希声2阶段增加信号球消除目标为2的处理逻辑`

Input: fix restart flow after battle failure in 寒境曙光
Output: `fix: 修复寒境曙光战斗失败后重启游戏`

Input: optimize 深谣 combat logic
Output: `perf: 优化深谣战斗逻辑`

Input: fix attack count handling when core skill is not ready
Output: `fix: 修复晖暮攻击逻辑，确保在核心技能未就绪时正确处理攻击次数`

## When the user asks for more than one line

If the user explicitly wants a title and body, use:

```text
<type>: <中文摘要>

<1-2 句中文正文，解释为什么改，而不是逐条罗列代码改动>
```

## Suggested prompts

- `/git-commit-message`
- `根据当前 staged diff，用 git-commit-message skill 生成提交信息`
- `按这个仓库的风格写一条 commit message`
- `根据改动生成中文 Conventional Commit`
