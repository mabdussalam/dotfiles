# Global Preferences

## Working style — delegation

This section is for when you are the **primary (root) session**. A subagent
should just do its assigned task directly — it cannot spawn further subagents
(the Agent tool is a no-op inside one), so the rest of this is root-only.

Your root context is expensive — spend it on requirements, design decisions, and
integration, and prefer delegating execution to subagents over working inline.

**Delegate to a subagent when:**
- A task needs reading ≥ 3 files or running ≥ 3 commands — a heuristic floor, not
  a bright line; weigh it against spec-and-review overhead
- The work can be spec'd up front and reviewed as output — a search, a refactor, an analysis
- It's self-contained and needs no interactive back-and-forth

**Keep it inline when:**
- It's a trivial or single-file change, or a quick look
- The task needs tight, iterative back-and-forth to get right
- Spec-and-review would cost more than just doing it

**When you do delegate:**
- Give the subagent enough standalone context to succeed — it cannot see this conversation
- Fan out independent subtasks in one message to run them concurrently
- Review what comes back and integrate it; on a bad or partial result, re-spec or take it inline

**Root Claude owns:** understanding requirements and surfacing ambiguities early,
breaking work into independently-delegatable pieces, and keeping the plan coherent.
