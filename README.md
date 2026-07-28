# SnippetVault

A local, file-based code-snippet manager. Snippets are stored as plain Markdown files with YAML front matter — no database — and served through a small Flask app with search, filtering, pinning, and syntax-aware rendering.

Built as a personal productivity tool, not part of the GenAI/data-engineering portfolio below (see [jprakash0205](https://github.com/jprakash0205)'s profile for those).

---

## Features

- **Markdown + YAML storage** — every snippet is a `.md` file with front matter (`title`, `category`, `pinned`, `created`, `modified`), so your snippets are plain text you own, not locked in a database
- **Search & filter** — free-text search across title/content/category, plus category and date-range (today/week/month/year) filters
- **Pinning** — pin important snippets to keep them at the top, sorted alphabetically otherwise
- **Auto-detected syntax highlighting** — guesses the language (Python, JavaScript, HTML, CSS, JSON, Bash) from the title extension or content, and renders via `codehilite`
- **Pagination** — configurable results-per-page
- **Admin page** — change the snippets storage directory and page size without touching code
- **Rotating error logging** — `run.py` wires up a rotating file handler (1MB per file, 3 backups) capturing warnings and above to `app_errors.log`
- **Windows convenience launchers** — `start_app.bat` and `launch.vbs` for one-click/no-console startup on Windows

---

## Tech stack

Python · Flask · PyYAML · Python-Markdown (with `fenced_code` and `codehilite` extensions) · Jinja2

---

## Getting started

```bash
git clone https://github.com/jprakash0205/SnippetVault.git
cd SnippetVault
pip install -r requirements.txt
python run.py
```

The app starts on `http://localhost:5000`. On first run it creates a default snippets folder at `~/snippets` — change this any time from the **Admin** page (`/admin`).

On Windows, you can instead double-click `start_app.bat` (or `launch.vbs` for a console-free launch).

---

## Project structure

```
SnippetVault/
├── run.py              # Production entry point — registers routes, sets up logging
├── routes.py            # Flask blueprint: all route handlers
├── config.py             # Config load/save helpers
├── helpers.py            # Snippet parsing/formatting utilities
├── app_config.json       # Runtime config (snippets_dir, per_page) — created/updated via /admin
├── templates/             # Jinja2 templates
├── static/                # CSS/JS assets
├── start_app.bat / launch.vbs   # Windows launch helpers
└── requirements.txt
```

> **Note:** `app.py` in this repo is an earlier, self-contained version of the app (routes defined inline, debug mode on) that predates the `run.py`/`routes.py`/`config.py` refactor. `run.py` is the current entry point — `app.py` is kept for reference but isn't used to run the app.

---

## Logs

- `app_errors.log` — application-level errors, broken routes, or failed file operations while the app is running (from the Python rotating handler)
- `background_terminal.log` — captures failures that occur before Flask even starts (e.g. missing dependencies, syntax errors), written by the `.bat` launcher

---

## License

MIT — see `LICENSE`.
