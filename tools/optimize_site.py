"""Minify inline assets in generated pages; never modify content or templates."""
import argparse
from html.parser import HTMLParser
from pathlib import Path

import minify_html


# Preserve prose markup: whitespace rules cannot infer arbitrary CSS display rules.
class InlineAssets(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=False)
        self.offsets = [0]
        for line in source.split('\n'):
            self.offsets.append(self.offsets[-1] + len(line) + 1)
        self.start = None
        self.spans = []
        self.feed(source)
        self.close()

    def source_offset(self):
        line, column = self.getpos()
        return self.offsets[line - 1] + column

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        asset_type = (attributes.get('type') or '').strip().lower()
        inline_script = tag == 'script' and 'src' not in attributes and asset_type in {
            '', 'module', 'text/javascript', 'application/javascript',
        }
        inline_style = tag == 'style' and asset_type in {'', 'text/css'}
        if inline_script or inline_style:
            self.start = (tag, self.source_offset())

    def handle_endtag(self, tag):
        if self.start is not None and tag == self.start[0]:
            self.spans.append((self.start[1], self.source_offset()))
            self.start = None


def minify_page(source):
    # Work backwards so replacing a block cannot invalidate earlier offsets.
    for start, closing in reversed(InlineAssets(source).spans):
        end = source.index('>', closing) + 1
        optimized = minify_html.minify(
            source[start:end], keep_closing_tags=True, minify_css=True, minify_js=True,
        )
        source = source[:start] + optimized + source[end:]
    return source


def optimize_site(root):
    pages = sorted(root.rglob('*.html'))
    if not pages:
        raise ValueError(f'No HTML pages in {root}; build the site first')
    before = after = 0
    edits = {}
    for page in pages:
        original = page.read_bytes()
        try:
            source = original.decode('utf-8')
        except UnicodeDecodeError as error:
            raise ValueError(f'{page}: HTML must be UTF-8') from error
        optimized = minify_page(source).encode('utf-8')
        if len(optimized) < len(original):
            edits[page] = optimized
        before += len(original)
        after += min(len(original), len(optimized))
    # Conversion failures must not leave a partially minified site.
    for page, data in edits.items():
        page.write_bytes(data)
    return len(pages), before, after


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', type=Path, default=Path(__file__).resolve().parents[1] / '_site')
    args = parser.parse_args()
    try:
        count, before, after = optimize_site(args.site)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    reduction = 1 - after / before if before else 0
    print(f'{count} HTML pages: {before:,} → {after:,} bytes ({reduction:.1%} smaller)')


if __name__ == '__main__':
    main()
