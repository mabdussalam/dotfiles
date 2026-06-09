---
name: modify-settings
description: >
  Make a guarded edit to settings.json — validate the schema, refuse managed-only
  keys at user/project scope, and show a diff before applying. Use when the user
  says "change settings.json", "set <key>", "update settings", "add permission rule",
  "allow X", "deny X", "stop allowing X", "move permission to user|project", or
  "set env var". Preferred over the built-in /update-config skill for any change
  where managed-key refusal, scope-silent-ignore detection, or programmatic lint
  matters. Hooks authoring goes to `create-hook`, not here.
agent: meta-claude
disable-model-invocation: false
argument-hint: "<key>=<value> or describe-the-change"
allowed-tools: [Read, Write, Edit, Bash, WebFetch, AskUserQuestion]
---

# modify-settings

Guarded editor for `settings.json`. Resolves a key/value or a free-text change
into a concrete JSON patch, refuses footguns, shows a diff, and only writes
after explicit user confirmation.

## 1. Inputs

One of:

- A concrete `key=value` (e.g. `model=claude-opus-4-7`,
  `permissions.allow+=Bash(ls:*)`).
- A free-text description of the change (e.g. "stop allowing curl in Bash").

Resolve to a single JSON patch operation:

- **set** `<path>` = `<value>` (scalar / object / array replacement).
- **append** `<value>` to array at `<path>` (e.g. `permissions.allow`).
- **delete** `<path>`.

If the input is ambiguous (multiple plausible paths, unclear value type),
ask the user via `AskUserQuestion` before continuing.

## 2. Resolve write path

Ask via `AskUserQuestion` which scope to write to:

- **User** — `~/.claude/settings.json` (applies to all sessions for this user).
- **Project** — `<project>/.claude/settings.json` (committed; team-shared).
- **Local** — `<project>/.claude/settings.local.json` (gitignored; per-clone).
- **Managed** — **refuse**. Managed settings are MDM/policy-only and must not
  be edited by the user-facing harness.

After scope is chosen:

1. `Read` the target file (treat ENOENT as empty `{}`).
2. Display the **current value** of the key being changed (or `<absent>`).
3. Display the **proposed value**.
4. Show a unified diff of the full file (see §4).
5. `AskUserQuestion` for explicit confirmation before any write.

## 3. Knowledge anchor

**Precedence (high → low):**
Managed → CLI flags → `.claude/settings.local.json` → `.claude/settings.json`
→ `~/.claude/settings.json`.

**Merge behavior:** scalars first-match-wins; arrays merge across scopes;
objects deep-merge.

**Common fields (safe to edit at user/project/local scope):**

- `model`, `availableModels`, `modelOverrides`, `effortLevel`
  (`low|medium|high|xhigh`), `alwaysThinkingEnabled`.
- `env` (object of string→string).
- `permissions`: `{allow, deny, ask, defaultMode, additionalDirectories,
  disableBypassPermissionsMode, disableAutoMode}`. Allow/deny rules use
  `Tool` or `Tool(specifier)` syntax with evaluation
  **deny → ask → allow, first match wins**.
- `hooks`, `allowedHttpHookUrls`, `disableAllHooks`.
- `enabledPlugins`, `skillOverrides`
  (`"name": "on|name-only|user-invocable-only|off"`),
  `maxSkillDescriptionChars`, `skillListingBudgetFraction`.
- `outputStyle`, `statusLine`, `theme`, `editorMode` (`normal|vim`),
  `tui` (`fullscreen|default`), `language`, `viewMode`.
- `attribution{commit,pr}`, `includeGitInstructions`, `autoMemoryEnabled`,
  `autoMemoryDirectory` (user/managed only).
- `worktree{baseRef, symlinkDirectories, sparsePaths, bgIsolation}`,
  `cleanupPeriodDays`.

**Managed-only keys — refuse at user/project/local:**
`claudeMd`, `claudeMdExcludes`, `strictKnownMarketplaces`,
`blockedMarketplaces`, `strictPluginOnlyCustomization`,
`allowManagedHooksOnly`, `allowManagedMcpServersOnly`,
`allowManagedPermissionRulesOnly`, `forceLoginMethod`, `forceLoginOrgUUID`,
`forceRemoteSettingsRefresh`, `channelsEnabled`, `policyHelper`,
`companyAnnouncements`, `parentSettingsBehavior`.

**Ignored-at-project/local (write but warn — silently dropped):**

- `permissions.defaultMode: "auto"` — a cloned repo cannot grant itself
  auto mode (security).
- `disableSkillShellExecution`.

**Live-reload behavior:** most settings reload on the `ConfigChange` event;
`model` and `outputStyle` require `/clear` or a restart to take effect.

**If uncertain about a key not listed above:**
`WebFetch https://code.claude.com/docs/en/settings.md` and re-check.

## 4. Author

1. `Read` the target file (`{}` if missing).
2. Apply the patch using `jq` if available, else Python `json` stdlib via
   `Bash`. Preserve key order where possible; pretty-print with 2-space
   indentation; trailing newline.
3. Write to a sibling temp file (`<target>.tmp.<pid>`).
4. Produce the diff:
   ```
   diff -u <target> <target>.tmp.<pid>
   ```
   Display it to the user.
5. Run §5 lint passes against the temp file.
6. `AskUserQuestion`: confirm apply.
7. On confirm: `mv <target>.tmp.<pid> <target>` (atomic rename).
   On decline or lint FAIL: `rm <target>.tmp.<pid>` and abort.

## 5. Lint

After writing, run the bundled validator:

    uv run --quiet --with pyyaml python ~/.claude/skills/modify-settings/scripts/lint.py <settings.json> --scope user|project|local|managed

Read the first stdout line: `PASS` / `PASS-WITH-WARNINGS` / `FAIL`. On `PASS-WITH-WARNINGS` or `FAIL`, surface every following indented detail line verbatim to the parent. On `FAIL` (e.g., managed-only key at non-managed scope), do not claim success.

The script implements Pass A (JSON parse + object top-level) and Pass B (managed-only key refusal at user/project/local scope, enums for `effortLevel`/`editorMode`/`tui`/`theme`, shape checks for `permissions.{allow,deny,ask}`/`env`/`hooks`/`enabledPlugins`, scope-conditional silent-ignore warnings for `defaultMode: auto` and `disableSkillShellExecution`, and the `defaultMode: bypassPermissions` security warning). **Pass C** below stays prose — these heuristics need human judgment.

### Pass C — footgun heuristics (human judgment)

- Permission rules using `Bash(curl ...)` patterns: curl rules are fragile (shell quoting, redirects, variable expansion). Suggest using `WebFetch` + a `deny` rule on `Bash(curl:*)` + a `PreToolUse` hook for enforcement.
- Edits to `model` or `outputStyle`: surface "requires `/clear` or restart to take effect" — these don't live-reload.

## 6. Report

Print:

- **Path written** (or "no change — aborted").
- **Summary** — one line, e.g. `set permissions.allow += "Bash(ls:*)"`.
- **Unified diff** (the same one shown before apply).
- **Lint status** — `PASS` / `PASS-WITH-WARNINGS` (list warnings) / `FAIL`
  (list reasons; original file restored).
- **Reload note** — if `model` or `outputStyle` changed, remind the user to
  `/clear` or restart.

On any FAIL: the temp file is deleted and the original is untouched. Surface
the reason verbatim; do not retry silently.
