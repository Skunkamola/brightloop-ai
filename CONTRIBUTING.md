# Contributing to BrightLoop

Thanks for considering a contribution.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
python -m pip install -e .
python -m unittest discover -s tests -v
```

## Contribution guidelines

- Keep the approval step explicit. Never apply a model-generated plan automatically.
- Do not add arbitrary shell execution or unrestricted file-system access.
- Validate all model output as untrusted input.
- Add tests for new actions, edge cases, and failure paths.
- Keep credentials out of source code, commits, screenshots, and issue reports.

For substantial changes, open an issue first so the scope can be discussed.
