# Plan: loop 纯化 + go DAG 并行前沿 + 文档对齐

> Specs: `docs/2026-07-21-loop-thin-executor-design.md`, `docs/2026-07-21-go-dag-parallel-frontier-design.md`  
> Plus system-review: 术语消歧、职责表、双真源消除  
> Branch: `feat/loop-go-skill-alignment`

## Task 1 — Approve specs + thin loop modes

Mark both design docs **Approved**. Rewrite:
- `skills/loop/SKILL.md` — thin executor positioning; no 需求确认/writing-plans main path
- `skills/loop/references/mode-default.md` — per thin design §4.1
- `skills/loop/references/mode-auto.md` — no plan split; fail if missing acceptance when go-called
- `skills/loop/references/acceptance-inference.md` — only fill acceptance gaps
- `commands/loop.md` — align trigger copy

Do **not** change gate-matrix/self-healing bodies.

## Task 2 — using-loopengine responsibility table

Update `skills/using-loopengine/SKILL.md`:
- loop = 执行环 (not 需求分析→计划)
- Add responsibility table: brainstorming / go / loop / supervisor / writing-plans
- Mention DAG parallel + scripts; no role registry
- go↔writing-plans one-liner boundary

## Task 3 — go SKILL: thin-loop contract + terminology + parallel frontier

Update `skills/go/SKILL.md`:
- Rename/clarify Step ①.5 as **项目上下文分析** (not 产品「需求分析」)
- Require task packets to loop: goal + acceptance; loop must not re-analyze
- Document **并行前沿** algorithm (P0): ready nodes, write-set conflict → serial, L1 no parallel tax
- Point to `dag-assembly.md`

## Task 4 — dag-assembly + dispatch notes

Update `skills/go/references/dag-assembly.md` with parallel-frontier section.
Light touch `cursor-dispatch-protocol.md` if needed for multi-dispatch same frontier.
Optional: note `parallel_safe` / `write_set` in dag-rules comments (minimal).

## Task 5 — Final alignment review (controller)

Grep for contradictory phrases; produce short 一致性核对报告; fix any remaining CRITICAL doc drift in touched files.
