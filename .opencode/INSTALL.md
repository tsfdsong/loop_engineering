# Installing LoopEngine for OpenCode

## Prerequisites

- [OpenCode.ai](https://opencode.ai) installed

## Installation

Add loopengine to the `plugin` array in your `opencode.json`:

```json
{
  "plugin": ["loopengine@git+https://github.com/tsfdsong/loopengine.git"]
}
```

Restart OpenCode. The plugin installs through OpenCode's plugin manager and registers all 55 skills.

Verify by asking: "Tell me about LoopEngine"

## Usage

Use OpenCode's native `skill` tool:

```
use skill tool to list skills
use skill tool to load loop
use skill tool to load go
```

## Tool Mapping

| Action | OpenCode Tool |
|--------|--------------|
| Create a todo | `todowrite` |
| Dispatch a subagent | `task` tool |
| Invoke a skill | `skill` tool |
| Read a file | `read` |
| Create/edit/delete files | `apply_patch` |
| Run a shell command | `bash` |
| Search file contents | `grep` |
| Find files by pattern | `glob` |
| Fetch a URL | `webfetch` |
