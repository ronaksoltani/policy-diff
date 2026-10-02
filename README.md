# Policy Diff Tracker

Track visible text changes on a terms-of-service or privacy-policy page. The first run saves a baseline. Later runs compare normalized text, save a unified diff when content changes, and emit a standalone HTML side-by-side report.

## Quick start

```bash
python -m venv .venv
python -m pip install -e .
policy-diff https://example.com/terms --state-dir .policy-state
```

Run the same command again later. State stays local in `.policy-state`; generated snapshots and HTML reports are deliberately excluded from Git. Respect each site's terms and robots guidance, use a sensible interval, and do not use this tool to evade access controls.

## Learning notes

This project joins an HTTP client (`requests`), HTML-to-text cleanup (`BeautifulSoup`), SHA-256 fingerprints, and Python's standard `difflib`. The hash avoids rendering a report when normalized text has not changed; the unified diff gives reviewers a compact history.

## Development

```bash
python -m pip install -e ".[dev]"
pytest
```

## License

MIT. See [LICENSE](LICENSE).
