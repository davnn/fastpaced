"""Generate the site's WOFF2 subset from rendered HTML and the pinned source font."""
import argparse
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'tools/fonts/eb-garamond-latin-v31.woff2'
OUTPUT = ROOT / 'assets/fonts/eb-garamond-subset.woff2'
# Printable ASCII supports routine edits. Typography includes generated hyphens.
BASE_CHARACTERS = set(range(0x20, 0x7F)) | set(map(ord, '\u00a0\u00ad‐‑–—‘’“”…'))


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ignored = 0
        self.characters = set()

    def handle_starttag(self, tag, attrs):
        if tag in {'head', 'script', 'style'}:
            self.ignored += 1

    def handle_endtag(self, tag):
        if tag in {'head', 'script', 'style'}:
            self.ignored -= 1

    def handle_data(self, data):
        if not self.ignored:
            self.characters.update(map(ord, data))


def build_subset(site):
    pages = sorted(site.rglob('*.html'))
    if not pages:
        raise ValueError(f'No HTML found in {site}; run stack exec fastpaced rebuild first')
    characters = set(BASE_CHARACTERS)
    for page in pages:
        parser = VisibleText()
        parser.feed(page.read_text(encoding='utf-8'))
        parser.close()
        characters.update(parser.characters)
    with TTFont(SOURCE, recalcTimestamp=False) as font:
        supported = set(font.getBestCmap())
        options = subset.Options()
        options.layout_features = ['*']  # Preserve kerning, ligatures and shaping.
        subsetter = subset.Subsetter(options=options)
        required_characters = characters & supported
        subsetter.populate(unicodes=required_characters)
        subsetter.subset(font)
        font.flavor = 'woff2'
        buffer = BytesIO()
        font.save(buffer)
        data = buffer.getvalue()
    # Re-open the actual output to verify coverage and the variable weight range.
    with TTFont(BytesIO(data)) as output:
        if not required_characters <= set(output.getBestCmap()):
            raise ValueError('Subset lost a character required by the rendered site')
        if [(a.axisTag, a.minValue, a.maxValue) for a in output['fvar'].axes] != [('wght', 400, 800)]:
            raise ValueError('Subset changed the supported font weights')
    return data, len(required_characters)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', type=Path, default=ROOT / '_site')
    parser.add_argument('--check', action='store_true', help='Fail if the committed subset needs updating')
    args = parser.parse_args()
    try:
        data, characters = build_subset(args.site)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_bytes() != data:
            parser.exit(1, 'Font subset is out of date; run tools/subset_font.py and rebuild the site\n')
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_bytes(data)
    original = SOURCE.stat().st_size
    print(f'{characters} characters, variable weights 400–800: {original:,} → {len(data):,} bytes '
          f'({100 * (1 - len(data) / original):.1f}% smaller)')


if __name__ == '__main__':
    main()
