# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Tanzawa is a Django-based IndieWeb blogging system focused on sustainability. It supports Micropub, Webmentions, IndieAuth, multiple post types (notes, articles, bookmarks, replies, checkins, trips), and a plugin system for optional features (exercise, health, comments-by-email, "Now" page, etc.).

Stack: Django + Django REST Framework, GeoDjango on SpatiaLite (geo-enabled SQLite), HTMX + Stimulus + _hyperscript + Tailwind for the front end, uWSGI for production. (`@hotwired/turbo` is listed in `front/package.json` but **not actually imported anywhere in JS**; the `turbo_response` Django middleware is wired up server-side but there's no client-side Turbo to receive its responses. Treat HTMX as the real interactivity driver.)

## Commands

`manage.py` lives at `apps/manage.py`, not the repo root.

### Docker (recommended dev path)

```bash
docker image build . -t tanzawa
docker run --rm -p 8000:8000 -v $PWD:/app -it tanzawa bash
# Then inside the container:
python3 apps/manage.py migrate
python3 apps/manage.py createsuperuser
python3 apps/manage.py runserver 0.0.0.0:8000
```

### Bare metal

Requires Python 3.10+ and SpatiaLite (`libsqlite3-mod-spatialite`, `spatialite-bin`, `binutils`, `libproj-dev`, `gdal-bin`). On macOS set `SPATIALITE_LIBRARY_PATH` in `.env` (sample paths in `.env.sample`).

```bash
pip install -r requirements_dev.txt
cp .env.sample .env
python3 -c "import secrets; print(secrets.token_urlsafe())" | xargs -I{} -n1 echo SECRET_KEY={} >> .env
python3 apps/manage.py migrate
python3 apps/manage.py runserver
```

Settings load env vars via `envparse` from the file path in the `ENV_FILE` env var. If `ENV_FILE` is unset, no `.env` is read — you must export vars manually or set `ENV_FILE=.env`.

### Tests, lint, typecheck

All run through `tox` (CI runs `tox` with no args, which runs `py311,flake8,typecheck,lint`):

```bash
tox                          # full CI suite
tox -e py311                 # pytest only (excludes @pytest.mark.slow)
tox -e py311 -- -k test_name # run a single test by name
tox -e py311 -- tests/unit/  # run one directory
tox -e py311 -- -m slow      # run only the slow-marked tests
tox -e lint                  # flake8 + black --check + isort --check
tox -e typecheck             # mypy on apps/
tox -e fmt                   # black + isort write mode
```

`tox` forces `ENV_FILE=.env.tox` and `DJANGO_SETTINGS_MODULE=tests.settings`. `tests/settings.py` is a thin `from core.settings import *`; the only real difference is that `.env.tox` force-enables the `health` and `exercise` plugins via `FORCE_ENABLED_PLUGINS`.

`pytest` config lives in `tox.ini` (`[pytest]`): `pythonpath = apps`, `testpaths = tests`.

### Front end

```bash
cd front
npm install
npm run build      # production webpack build → ../static/
npm start          # postcss --watch for Tailwind dev
```

The production Docker build (`Dockerfile.fly`) runs `npm run build` then `manage.py collectstatic --noinput`. After modifying templates or adding a theme, you must rebuild Tailwind or `collectstatic` won't pick up the new CSS.

### Plugins

Plugins are toggled per-install (state stored in DB), not via settings:

```bash
python3 apps/manage.py enable_plugin <identifier>      # e.g. blog.tanzawa.plugins.nowpage
python3 apps/manage.py disable_plugin <identifier>
```

`enable_plugin` only toggles the `MPlugin.enabled` flag in the DB — it does **not** run migrations (read `apps/data/plugins/pool.py:58` if you're skeptical). Plugin migrations are picked up by any normal `manage.py migrate` because plugin apps are auto-added to `INSTALLED_APPS` once their directory exists under `tanzawa_plugin/`, regardless of enabled state. So the actual upgrade flow is: pull new plugin code → `migrate` → optionally `enable_plugin`.

`FORCE_ENABLED_PLUGINS` (env var, comma-separated identifiers) bypasses the DB toggle — used by the test env and useful for force-enabling plugins in containerized deployments.

## Architecture

### Layered structure under `apps/`

Tanzawa enforces a layered architecture. Imports flow **downward only**: `interfaces → application → domain → data → core`. Crossing these boundaries upward (e.g. `domain` importing `interfaces`) breaks the model.

| Layer | Role | Examples |
|---|---|---|
| `apps/core/` | Django project config — `settings.py`, root `urls.py`, `wsgi.py`/`asgi.py`, custom SpatiaLite DB engine in `core/db/`. | `core.settings`, `core.urls` |
| `apps/data/` | Models and persistence. Each subpackage is a Django app with `models.py` + migrations. No business logic. | `data.entry`, `data.post`, `data.streams`, `data.indieweb`, `data.plugins` |
| `apps/domain/` | Pure business logic operating directly on data-layer models. Conventional file split: `operations.py` (state changes — `create_entry()`, `update_entry()` with `@transaction.atomic`) and `queries.py` (read-only). | `domain/entry/operations.py`, `domain/entry/queries.py`, `domain/indieweb/webmention/_queries.py` |
| `apps/application/` | Workflow orchestration — defines DTOs (`Bookmark`, `Checkin`, `Reply`, `Location`), validates input, composes calls into `domain/*`. The `_create_entry.py`/`_update_entry.py`/`_post_to_bridgy.py`/`_open_graph.py` modules in `application/entry/` are the canonical example: leading-underscore implementations re-exported by the package `__init__.py`. | `application.entry.create_entry`, `application.entry.post_to_bridgy`, `application.indieweb`, `application.feeds` |
| `apps/interfaces/` | Views, forms, URL routing, management commands, middleware, templatetags. Public site under `interfaces/public/`, authenticated dashboard under `interfaces/dashboard/`, admin under `interfaces/admin/` (each `_entry.py`/`_post.py`/`_indieweb.py`/etc. file is re-exported by `admin/__init__.py`), common middleware/templatetags under `interfaces/common/`. | `interfaces.public.urls`, `interfaces.dashboard.urls`, `interfaces.commands.management` |

Project-wide templates are at `apps/templates/`; per-app templates live inside each interface package.

### URL composition

`core/urls.py` mounts in this order, and **order matters**:

1. `/a/` → `interfaces.dashboard.urls` (authenticated UI)
2. `/webmention/`, `/admin/`, `/auth/`, `/favicon.ico`
3. **Plugin urls** (from `plugin_pool.urls()`) — included before public urls so plugin paths take precedence
4. `interfaces.public.urls` — **catch-all last**, because stream slugs (`/notes`, `/articles`, etc.) are matched here and would otherwise shadow plugin paths

### Plugin system

Bundled plugins live in `apps/tanzawa_plugin/<name>/`. `core/settings.py` auto-appends every subdirectory of `tanzawa_plugin/` containing `__init__.py` to `INSTALLED_APPS`.

A plugin is a normal Django app plus:

- A `Plugin` subclass of `data.plugins.plugin.Plugin` registered with `data.plugins.pool.plugin_pool` from a `plugin.py` module (discovered via `autodiscover_modules("plugin")`).
- Optional `urls.py` (public, mounted at the root by the pool) and `admin_urls.py` (mounted under `/a/plugins/<slug>/`, all views must use `@login_required`).

Plugins can also hook into feed rendering (`feed_before_content`, `feed_after_content`) and the public top nav (`render_navigation`).

When working on plugins, keep migrations runnable: enable the plugin first (`enable_plugin`), then `makemigrations <app_label>`. Plugin migrations are included in any normal `manage.py migrate` run because their app is in `INSTALLED_APPS`.

> **Doc-vs-code warnings.** `docs/plugins/custom-plugins.md` contains three claims that are NOT implemented in the actual code:
> 1. `PLUGINS_RUN_MIGRATIONS_STARTUP` env var — no readers in `apps/`.
> 2. `PLUGINS` env var for out-of-tree plugins — no readers in `apps/`. Only `FORCE_ENABLED_PLUGINS` exists.
> 3. "Tanzawa will automatically run migrations when the plugin is activated" — false. `enable_plugin` only updates a DB flag; see `apps/data/plugins/pool.py:58`.
>
> Treat the plugin docs as aspirational on these three points. The real behavior: `manage.py migrate` picks up everything because plugins are always in `INSTALLED_APPS`.

### Themes

Themes live in `front/src/themes/<name>/` and are picked up automatically by `core/settings.py` (`THEMES`, `THEMES_ROOT`, `THEME_STATICFILE_DIRS`). Each theme ships its own `tailwind.config.js` and a `static/<name>/style.css` built with Tailwind 3. The active theme is selected in the Django admin under Site Settings; production deploys must re-run `collectstatic` after a theme change.

### Front-end conventions

- **Stimulus controllers** live in `front/src/controllers/` (dashboard) and `front/src/public_controllers/` (public site). Loaded via `Application.start()` + `require.context` in `front/src/application.js`.
- **HTMX + _hyperscript** drive most interactivity (forms, inline editing, dropdowns). The `django_htmx.middleware.HtmxMiddleware` is active in `core/settings.py`. Scripts are shipped as standalone files in `static/js/htmx.min.js` and `static/js/_hyperscript.min.js` — not bundled by webpack.
- **Webpack** builds two JS entries (`app.js`, `public.js`) and the Tailwind CSS bundle. Config in `front/webpack.config.js`; outputs go to `../static/{js,tailwind}/`.
- **Tailwind v3** with content scan paths in `front/tailwind.config.js` — read the "Runtime gotchas" section below before changing the build layout, the scan paths are relative and easy to break.
- **Leaflet** for maps; **SVG-rendered exercise routes** via `polyline` + `cairosvg` (forces a runtime `libcairo2` dep — see gotchas).

## Conventions

- **Python 3.11** is the canonical version (`basepython` in `tox.ini`, `python_version` in mypy config).
- **Formatting**: black with `line-length = 120`, isort with `profile = "black"`. First-party imports are declared in `pyproject.toml`: `application, core, data, domain, interfaces, tanzawa_plugin, tests`.
- **flake8**: max-line-length 120, max-complexity 10, excludes `migrations,urls.py,manage.py,settings.py,admin.py`.
- **mypy**: `check_untyped_defs = True`, ignores `migrations`, `apps.settings`, `admin` modules.
- Tests under `tests/` use a parallel layout to `apps/` (`tests/unit/`, `tests/integration/`, `tests/test_indieweb/`, `tests/test_public/`, `tests/tanzawa_plugins/`, etc.). Factories live in `tests/factories/`. The `slow` pytest marker is excluded by default in the `py311` env.
- A leading underscore on a module filename (e.g. `application/entry/_create_entry.py`, `interfaces/admin/_entry.py`, `data/indieweb/models/_t_webmention.py`) signals it's intended to be accessed via the package's `__init__.py` re-exports, not imported directly. The convention spans all layers — 29 files at the time of writing.
- `DEBUG=True` automatically enables `django-debug-toolbar` (added to `INSTALLED_APPS` and middleware in `core/settings.py`, mounted at `/__debug__/`).

## Deployment notes

Three deployment paths exist in the repo:

- **Fly.io** (upstream's primary target): `Dockerfile.fly` + `fly.toml.example`. Single-stage, full `python:3` image (~1.2 GB), bundles `requirements_dev.txt`. Static served by Fly's edge via `[[statics]]` in `fly.toml`. Docs at `docs/deployment/index.md`.
- **Docker Compose** (fork-only, under `deploy/`): three-stage build (`node:20-bookworm-slim` → `python:3.11-slim-bookworm` build → slim runtime), ~465 MB, no dev deps. Caddy fronts the app and serves `/static/*` + `/media/*` directly from named volumes. Multi-arch image published to `ghcr.io/rmdes/tanzawa` by `.github/workflows/publish-docker.yml`.
- **Local dev**: `Dockerfile` is the upstream-shipped dev image — installs `requirements_dev.txt`, no entrypoint. Use it with the README's `docker run -v $PWD:/app -it tanzawa bash` flow to get a shell, then run migrations/runserver manually.

Sentry is wired in `core/settings.py` and activated by `ENABLE_SENTRY=True` + `SENTRY_DSN`.

## Runtime gotchas (hard-won)

Things that cost a debug cycle to discover and are not obvious from a casual code read. Read these before touching the build, the static pipeline, or the plugin loader.

### Native libs need to be at the right phase

Several Python deps compile from source at pip install: **uWSGI, PyMuPDF, cairosvg/cairocffi, lxml** (via `extruct`). The upstream `Dockerfile.fly` uses the full `python:3` image *deliberately* because slim variants strip `gcc` and Python headers. If you switch to a slim variant you must install `build-essential python3-dev libxml2-dev libxslt1-dev zlib1g-dev` before pip and (optionally) purge them after.

At *runtime*, the only extra system library required is **`libcairo2`**. `cairosvg → cairocffi` does `dlopen("libcairo.so.2")` at module import. And module import runs at Django startup, regardless of which plugins are enabled, because `core/settings.py:97-99` auto-installs every subdirectory of `tanzawa_plugin/` — including `exercise`, which has `import cairosvg` at the top of `tanzawa_plugin/exercise/domain/exercise/operations.py`. Strip libcairo2 and the entire app fails to boot.

### Tailwind needs `apps/` to be a sibling of `front/`

`front/tailwind.config.js` lists its template scan paths as `'../apps/**/*.html'`, `'../apps/**/forms.py'`, `'../apps/**/forms/**/*.py'`, `'../apps/interfaces/public/**/*.py'` — relative to `front/`. If you build the front in isolation (e.g. a multi-stage Docker build that copies only `front/`), the compiled `style.css` silently drops every Tailwind class used only in Django templates. There are no warnings, no errors, no console output. The CSS file loads fine — it's just missing classes.

**Smoke test**: a healthy Tailwind compile for Tanzawa is ~25–30 KB. A "broken" one (no template scan) is ~16 KB. If your CSS is suspiciously small, this is why.

### uWSGI does not serve static files

`apps/interfaces/public/uwsgi.ini` only configures `http-socket :8000` + the Django wsgi mount. There is no `static-map`. Any deployment behind a reverse proxy must handle `/static/*` AND `/media/*` itself, or you must add `--static-map=/static=<path>` to the uwsgi command line — but don't modify the upstream `.ini` file unless you intend to upstream the change.

### Django named volumes shadow image content

If you `COPY` files into a path in the Docker image and then mount a named volume at the same path, the first container start populates the volume from the image — and that volume persists forever, ignoring image updates. Common with `STATIC_ROOT` overlapping a shared volume between app and reverse-proxy containers.

**Fix**: build into a non-mount path (e.g. `/app/staticfiles-image/`) and rsync to the volume mount on each container boot in the entrypoint. The `deploy/bootstrap.sh` script in this repo demonstrates the pattern.

### Login URL is `/auth/login/`

`LOGIN_URL = "login"` in `core/settings.py` is a URL *name*, not a path. The actual path is mounted by `path("auth/", include("django.contrib.auth.urls"))` in `core/urls.py:13`. There is no `/a/login/` — `/a/` is the authenticated dashboard root that *redirects* unauthenticated users to `/auth/login/`. Use `/auth/login/` for healthchecks or unauthenticated 200 probes.

### `ENV_FILE` env var is optional

`core/settings.py` does `env.read_envfile(path=os.environ.get("ENV_FILE"))`. When `ENV_FILE` is unset, envparse emits a benign warning ("Could not any envfile") and falls back to reading from `os.environ`. Docker compose's `env_file:` directive populates `os.environ` directly, so containers should leave `ENV_FILE` unset. The `tox` environment sets `ENV_FILE=.env.tox` explicitly via `tox.ini`.
