# fastpaced [![Build Status](https://github.com/davnn/fastpaced/actions/workflows/build.yml/badge.svg)](https://github.com/davnn/fastpaced/actions?query=workflow%3Abuild)

fastpaced is a private blog powered by [Hakyll](https://github.com/jaspervdj/hakyll), a static site generator written in Haskell.

Article content is managed in a separate repository and included as a Git submodule to keep code and content cleanly separated. To initialize or update the articles, run:

```bash
git submodule update --init
```

### Updating code

1. Install or update [Stack](https://github.com/commercialhaskell/stack)
2. Build the project: `stack build`
3. Run the site compiler: `stack exec fastpaced`

### Updating content

Articles are written in [Markdown](https://www.markdownguide.org/). [Pandoc](https://pandoc.org/) is used to transform the `.md` files into `.html` files. Each article lives in its own folder inside `/articles`, where the folder name also defines the output path.

#### Metadata

Each article includes a YAML front matter block:

```yaml
---
title: String
published: Date (YYYY-MM-DD)
author: String
---
```

Optional metadata is available if articles require additional features. The following fields are available:

```yaml
mathematics: Boolean (true | false)
centered: Boolean  (true | false)
image: String (path)
```

* `mathematics` enables mathematical typesetting with [KaTeX](https://github.com/KaTeX/KaTeX). Mathematical content can then be included with `$expr$` for inline content and `$$expr$$` for block content.
* `centered` changes the article to a centered layout instead of left-aligned.
* `image` specifies the path to an image relative to the current article path. This image is used for the site meta data `og:image`. A default image is included if the `image` field is missing.

### Styling content

Pandoc has various possible extensions and this blog uses the `fenced_divs` extension to enable classes to be added to `div` blocks. There are classes implemented for specific content blocks like `.definition`, `.theorem` and `.proof`.

The width of elements can be modified with `.width-small`, `.width-medium`, `.width-large` and `.width-full`, which set the width of the element to 33%, 50% and 66% of the article. Images can optionally be shown with captions with the `.caption` class.

#### Theming

Theming is the only feature implemented using JavaScript. When JavaScript is deactivated the light theme is used. The only theme-specific class is `.themed` for `img` elements, which safely inverts the image colors with a hue-rotation turning white images into black images for dark mode.
