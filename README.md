# BrightLoop AI

**A human-approved, local-first AI workflow assistant.**

BrightLoop turns a plain-language request into a structured action plan with Claude. You can inspect the plan before anything happens. When you approve it, BrightLoop can create Markdown notes and append entries to a local daily log.

> **Project status:** early prototype (v0.1.0). This is a new project and does not yet have public adoption metrics. Contributions, feedback, and testing are welcome.

## Why BrightLoop?

Many AI automation tools make it difficult to see exactly what an agent intends to do before it acts. BrightLoop explores a smaller, more transparent approach: AI can help plan repetitive work, but the person stays in control of execution.

The initial release is intentionally limited. It does not run shell commands, execute model-generated code, send emails, make purchases, or access third-party accounts. Those limitations make the first version easier to inspect and test.

## How it works

1. Describe a task in ordinary language.
2. Claude returns a JSON plan using a small allow-list of actions.
3. BrightLoop validates the plan and saves it locally.
4. Review the proposed changes with `brightloop show`.
5. Type `APPLY` to approve the changes.
6. BrightLoop creates the requested Markdown files in your workspace.

## Quick start

### Requirements

- Python 3.10 or newer
- An Anthropic API key for AI plan generation

### Install

```bash
git clone https://github.com/Skunkamola/brightloop-ai.git
cd brightloop-ai
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
python -m pip install -e .
```

### Configure your API key

Set the key in your environment. Do not commit it to GitHub.

macOS/Linux:

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

PowerShell:

```powershell
$env:ANTHROPIC_API_KEY="your-api-key"
```

Optional model setting (the default is `claude-sonnet-5-5`):

```bash
export BRIGHTLOOP_MODEL="claude-sonnet-5-5"
```

### Create and review a plan

```bash
brightloop plan "Help me organise my revision topics for this week"
brightloop show
brightloop apply
```

When prompted, type `APPLY` to approve the local file changes. Any other response cancels the operation.

You can also point to a different saved plan:

```bash
brightloop show path/to/plan.json
brightloop apply path/to/plan.json --workspace ./my-workspace
```

## Supported actions in v0.1.0

| Action | What it does |
|---|---|
| `write_note` | Creates a new Markdown file under `workspace/notes/` |
| `append_log` | Adds an entry to `workspace/daily-log.md` |

BrightLoop refuses to overwrite an existing note. It validates action types and text sizes, and it never interprets model output as executable code.

## Development and tests

```bash
python -m unittest discover -s tests -v
```

The test suite covers plan parsing, unsupported actions, safe filenames, preview-only behavior, note creation, duplicate targets, and symlink protection. The GitHub Actions workflow runs it on Python 3.10, 3.11, and 3.12.

## Design principles

- **Human approval:** generated plans are previews until the user types `APPLY`.
- **Small action surface:** the first release only creates Markdown notes and appends to one local log file.
- **Untrusted model output:** every plan is parsed and checked against an allow-list; model output is never run as code.
- **Local-first:** there are no third-party account integrations or automatic background actions in v0.1.0.
- **Least privilege:** API credentials are read from the environment and should never be committed.

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md). Planned work includes mocked provider tests, a provider interface, narrowly scoped optional integrations, scheduled workflows with run history, and a lightweight interface. These are future ideas, not features in the current release.

## Contributing

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request. Please keep the approval-first design and least-privilege approach intact.

## Security

Do not commit API keys. See [SECURITY.md](SECURITY.md) for the current security scope and limitations.

## License

MIT. See [LICENSE](LICENSE).
