# AGENTS.md

Guidance for agents working in this repository.

## Repository layout

- **`main`**: placeholder README only.
- **`cursor/hermes-desktop-ebbd`** (and **`cursor/deploy-hermes-deepseek-ebbd`**): Hermes Agent + DeepSeek install scripts, `.env.example`, optional Linux desktop shortcuts.

For development and demos, use a branch that contains `scripts/` (checkout `cursor/hermes-desktop-ebbd` if you are on `main`).

## What this project is

Deployment helpers for [Hermes Agent](https://github.com/NousResearch/hermes-agent) on Linux with **DeepSeek** as the default LLM provider. The app itself is installed under `~/.hermes/hermes-agent` via upstream `install.sh`, not as Python/Node sources in this repo.

## Cursor Cloud specific instructions

### Prerequisites (system)

- Git, curl, network egress
- Hermes installer pulls **uv**, **Python 3.11**, and Node tooling automatically on first install

### First-time setup (human or agent)

```bash
git checkout cursor/hermes-desktop-ebbd   # if scripts/ are missing
export DEEPSEEK_API_KEY='sk-...'          # required for chat
export PATH="$HOME/.local/bin:$PATH"
bash scripts/install-hermes-deepseek.sh
source ~/.bashrc
hermes doctor
```

Optional full stack (lazy Python deps, Playwright, Docker, Codex CLI):

```bash
bash scripts/install-hermes-full.sh
```

Optional desktop launchers (XFCE/GNOME):

```bash
bash scripts/desktop/install-desktop-shortcuts.sh
```

### PATH

Ensure `~/.local/bin` is on `PATH` (installer adds it to `~/.bashrc`). The `hermes` CLI is `~/.local/bin/hermes` → venv entrypoint.

### Lint / test / build (this repo)

There is no in-repo linter, test suite, or build. Validate changes by re-running the install scripts and `hermes doctor`.

### Run / verify

| Command | Purpose |
|---------|---------|
| `hermes doctor` | Environment and dependency check |
| `hermes status` | Provider, keys, component status |
| `hermes skills list` | Skills hub / bundled skills |
| `hermes` or `hermes --tui` | Interactive chat (needs `DEEPSEEK_API_KEY`) |
| `hermes -z "prompt"` | One-shot prompt (needs API key) |
| `hermes dashboard` | Local web UI (default port 9119) |

DeepSeek key must be in `~/.hermes/.env` as `DEEPSEEK_API_KEY` or via `hermes config set DEEPSEEK_API_KEY 'sk-...'`.

### Gotchas

- `scripts/install-hermes-deepseek.sh` may exit non-zero after a successful upstream install when it runs `uv pip install -e ".[all]"` outside the venv; Hermes is usually still usable—confirm with `hermes --version` and `hermes doctor`.
- `hermes config` has no `get` subcommand; use `hermes config show` or read `~/.hermes/config.yaml`.
- Chat and `-z` one-shot prompts fail fast without `DEEPSEEK_API_KEY` (expected).
- `computer_use` and some platform tools are OS- or key-dependent; see `hermes doctor` warnings.

### Services

No docker-compose or databases in this repo. Optional: `hermes gateway install && hermes gateway start` for messaging (separate setup).
