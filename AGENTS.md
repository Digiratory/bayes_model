# AGENTS.md

## Project

BN Modeller — a PySide6 desktop GUI for feature dependency modeling with Bayesian Networks, built on py-banshee. Single Python package `bn_modeller/`.

- Real entrypoint: `bn_modeller/app.py:main` (console script `bn_modeller`). GUI-only: a `--nogui` flag exists but `main()` raises "Headless mode is not supported".
- `bn_modeller/main.py` is a legacy prototype (top-level sibling imports, expects local `data/` files). It is not the app entrypoint; don't wire it into the package.
- Layout: `windows/` (main window), `widgets/` (UI pages live in `widgets/page/`), `models/` (Qt table models), `bayesian_nets/` (py-banshee calculations), `utils/db_model_handler.py` (CSV/XLSX ingestion).
- `docs/` is the Jekyll source of the user guide site (digiratory.github.io/bayes_model).

## Commands

- Tests: `.venv\Scripts\python.exe -m pytest tests` — pytest is not declared in pyproject; install it into the venv yourself. Suite is pure Python (no Qt tests).
- Run app: `bn_modeller` after `pip install -e .` (editable installs report placeholder version 0.0.0 in code).
- Format/lint: `pre-commit run --all-files` — isort (black profile) + black; black pinned to `language_version: python3.10`.
- Windows exe: `pyinstaller bn_modeller.exe.spec` (bundles `resources/templates/*.xlsx` and `icon.ico`; hiddenimports for matplotlib PDF/PGF/PS/SVG backends).

## Gotchas

- Build uses Poetry 2 + poetry-dynamic-versioning: version is derived from git tags `release/X.Y.Z` at build time; `bn_modeller/__init__.py` keeps a `0.0.0` placeholder.
- Python 3.14 is supported (`requires-python = ">=3.10,<3.15"`); it requires `pygraphviz>=2.0` — 2.0.x ships cp314 wheels, while 1.x only builds from source and fails without Graphviz dev headers.
- Test fixtures `tests/assets/*.csv` are gitignored by the global `*.csv` rule — a fresh clone cannot run the tests until fixtures are recreated. Keep them; `git add -f` any new ones.
- `requirements.txt` is stale (lists PyQt5 and old pins) — pyproject.toml is the only dependency source. `poetry.lock` is gitignored, so CI resolves fresh.
- Graphviz must be installed natively (Windows: graphviz.org installer, `bin` on PATH): pygraphviz needs it to build and the app needs `dot` at runtime for graph rendering.
- Publishing is fully automated: creating a GitHub release (tag `release/X.Y.Z`) triggers `.github/workflows/python-publish.yml` (poetry build + trusted PyPI publish + release assets). No test/lint CI exists — verify locally.
- User settings persist via `QSettings` (Windows registry under Digiratory/bn_modeller).
- Commit messages: present tense, ≤50-char first line (see CONTRIBUTION.md).
