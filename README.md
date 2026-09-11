# fastpaced [![Build Status](https://github.com/davnn/fastpaced/actions/workflows/build.yml/badge.svg)](https://github.com/davnn/fastpaced/actions?query=workflow%3Abuild)

A static blog built with [Hakyll](https://github.com/jaspervdj/hakyll). Markdown
articles live in the `articles` Git submodule; templates, styling and tooling live here.

## Develop

Install Stack, a C/C++ toolchain and zlib headers (Ubuntu:
`sudo apt install build-essential zlib1g-dev`). Stack installs the pinned compiler;
the first build can take several minutes. Checks also need Python 3, Node.js, Bash
and jq. Commands below use uv for the pinned Python environment; alternatively,
install `tools/requirements.txt` in a virtual environment and invoke its Python.

```bash
git submodule update --init --recursive
stack build
stack exec fastpaced watch
```

The preview normally serves `http://127.0.0.1:8000`. Output is in `_site/`, cache in
`_cache/`. Restart the preview after rebuilding Haskell code. Stop `watch` before
rebuilding or optimizing the same directories; use a separate checkout for parallel
work. A clean `rebuild` removes stale pages and image derivatives.

## Validate and prepare production output

This matches CI's checks and asset-processing order:

```bash
stack build --ghc-options=-Werror
stack exec fastpaced rebuild
node tests/browser_scripts.cjs
uv run --with-requirements tools/requirements.txt python -m unittest discover -s tests -p "*.py"
uv run --with-requirements tools/requirements.txt python tools/optimize_images.py
uv run --with-requirements tools/requirements.txt python tools/optimize_site.py
uv run --with-requirements tools/requirements.txt python tools/subset_font.py --check
```

Test discovery picks up new Python modules automatically. Individual test files
remain runnable, and integration fixtures do not modify the article submodule.
Run asset processing after the final Hakyll build; later builds can overwrite it.
Only eligible, smaller derivatives are selected. Images retain their native sizes;
original downloads and feed image URLs stay available. Use
`tools/optimize_images.py --dry-run` to inspect savings without writing output.

## Write articles

Publish from `articles/<slug>/index.md`, with front matter such as:

```yaml
---
title: Example article
author: David Muhr
published: 2026-09-09
mathematics: true
---
```

| Field | Meaning |
| --- | --- |
| `title`, `author` | Required, nonempty text. |
| `published` | Required real date in exact `YYYY-MM-DD` form. |
| `mathematics` | Enable KaTeX for `$inline$` and `$$display$$` math; defaults to false. |
| `centered` | Center the article layout; defaults to false. |
| `abstract` | Optional summary. |
| `image` | Optional social-preview image: relative, site-root or absolute URL. |

Boolean values must be true/false. Invalid metadata fails the build. Only folders
with `index.md` publish. Other Markdown and `.bib` files are not published, while other
attachments in published folders are public, including nested downloads.
Article-root `index.html` is reserved for generated output.

Use at most one `.bib` file per article and cite with `[@citation-key]`. The citation
style is `assets/csl/chicago-author-date.csl`; multiple bibliographies fail explicitly.
Commit and publish content changes in the submodule before updating its reference here.

## Style figures and blocks

Fenced divs support `.definition`, `.theorem` and `.proof`. Figure width classes
are capped to available space:

| Class | Width |
| --- | ---: |
| `.width-small` | 17.5rem |
| `.width-medium` | 21.875rem |
| `.width-large` | 26.25rem |
| `.width-full` | 43.75rem |

```markdown
![Figure description](figure.png){.width-medium .caption width=720 height=480 loading=lazy}
```

Supply original pixel dimensions; CSS preserves the aspect ratio. Keep leading
figures eager and later figures lazy (current articles keep their first two eager).
Add `.caption` to display the caption and `.themed` for dark-mode inversion with
hue rotation; check colored figures in both themes. Without JavaScript, the site
uses its light theme and leaves math source readable.

## Update the font subset

EB Garamond is local, preloaded and uses `font-display: optional`: slow connections
may retain the fallback to avoid a late swap. The subset preserves weights 400–800,
shaping, printable ASCII, common typography and characters used in rendered pages.
Unsupported characters fall back; KaTeX supplies separate math fonts.

After content or font-tool changes, regenerate if the final subset check fails:

```bash
stack exec fastpaced rebuild
uv run --with-requirements tools/requirements.txt python tools/subset_font.py
stack exec fastpaced rebuild
```

Commit `assets/fonts/eb-garamond-subset.woff2` with the relevant change, then repeat
production validation. The source font lives in `tools/fonts/`; the OFL license is
published with the subset.

## Reference

- [Architecture and output contracts](docs/architecture.md)
- [Dependencies, updates and automatic merging](docs/dependencies.md)
- [Image conversion policy](docs/image-optimization.md)
- [Performance measurements and limits](docs/font-performance.md)
