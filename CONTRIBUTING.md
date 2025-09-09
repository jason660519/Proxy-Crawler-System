# Contributing

## Development Environment

```bash
uv sync --dev
```

## Tests

```bash
uv run pytest
```

## Lint & Type

```bash
uv run ruff check .
uv run mypy src
```

## Commit Style

Conventional Commits, e.g.:

```text
feat(fetch): add adaptive throttling
fix(validation): handle empty batch
```

## Security

- No real API keys in code.
- Use `config.settings` for secrets.
