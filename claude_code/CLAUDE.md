# Global Preferences

## Working style — subagents

Prefer spawning subagents (via the Agent tool) over running tasks inline. Root context is expensive, spend it on requirements, design decisions, and integration. Delegate execution.

**Delegate to a subagent when:**
- A task requires reading ≥ 3 files or running ≥ 3 commands
- Work can be spec'd and reviewed as output (a search, a refactor, an analysis)
- Tasks are parallelisable — send multiple agents in one message for concurrent work
- The work is self-contained and doesn't need interactive back-and-forth

**Root Claude owns:**
- Understanding requirements and surfacing ambiguities early
- Breaking work into independently-delegatable pieces
- Reviewing subagent output and integrating findings
- Keeping the overall plan coherent

When in doubt, delegate. A sharp root context makes better decisions.
