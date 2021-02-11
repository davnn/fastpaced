# fastpaced

[![Build Status](https://www.travis-ci.org/davnn/fastpaced.svg?branch=master)](https://www.travis-ci.org/davnn/fastpaced)

This is a private blog proudly powered by [Hakyll](https://github.com/jaspervdj/hakyll), the Haskell static site generator.

Articles are in their own repository to keep code and content separate; they are included via git submodule. Use

```
git submodule init
git submodule update --remote
```

to initialize and update the articles.

[Travis CI](https://travis-ci.org/) is used to build this repository and to push the results to the github-pages branch. An update to the master branch of the [fastpaced articles repository](https://github.com/davnn/fastpaced-articles) automatically triggers a new Travis build.

Articles are written in [Markdown](https://www.markdownguide.org/) and [Pandoc](https://pandoc.org/) is used to transform the ``.md`` files into ``.html`` files. Each articles lives in its own folder inside ``/articles``. The folder name of an article also represents its HTML ``path``.

All articles have metadata attached to them in form of a YAML front matter. The following metadata field are required for all articles.

```
---
title: String
published: Date (YYYY-MM-DD)
author: String
---
```

Optional metadata is available if articles require additional features. The following fields are available:

```
mathematics: Boolean (true | false)
centered: Boolean  (true | false)
image: String (path)
```

The ``mathematics`` field enables mathematical typesetting with [KaTeX](https://github.com/KaTeX/KaTeX). Mathematical content can then be included with ``$expr$`` for inline content and ``$$expr$$`` for block content.

The ``centered`` field changes the article to a centered layout instead of left-aligned.

The ``image`` field specifies the path to an image relative from the current article path. This image is used for the site meta data ``og:image``. A default image is included if the ``image`` field is missing.

Pandoc has various possible extension and this blog uses the ``fenced_divs`` extension to enable classes to be added to ``div`` blocks. There are classes implemented for specific content blocks like ``.definition``, ``.theorem`` and ``.proof``. Additionally, the width of elements can be modified with ``.width-small``, ``.width-medium``, ``.width-large`` and ``.width-full``, which set the width of the element to 33%, 50% and 66% of the article. Images can optionally be shown with captions with the ``.caption`` class.
