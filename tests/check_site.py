"""Check the generated site's routes and feed using only the standard library."""
from pathlib import Path
import xml.etree.ElementTree as ET

site = Path('_site')
articles = list(Path('articles').glob('*/index.md'))
assert articles, 'Initialize the articles submodule before checking the site'
for source in articles:
    output = site / source.with_suffix('.html')
    html = output.read_text()
    url = f'https://fastpaced.com/{source.parent}/'
    assert f'<link rel="canonical" href="{url}">' in html, output
    assert '<article ' in html, output
    assert not (site / source).exists(), f'Article source was copied: {source}'
assert not list((site / 'articles').rglob('*.md')), 'Markdown sources must not be published'
assert '<link rel="canonical" href="https://fastpaced.com/404.html">' in (site / '404.html').read_text()
assert '<link rel="canonical" href="https://fastpaced.com/">' in (site / 'index.html').read_text()
feed = ET.parse(site / 'atom.xml')
ns = {'atom': 'http://www.w3.org/2005/Atom'}
entries = feed.findall('atom:entry', ns)
assert len(entries) == len(articles), 'Feed must include every article'
assert all('<article ' in entry.findtext('atom:summary', default='', namespaces=ns) for entry in entries)
expected_urls = {f'https://fastpaced.com/{source.parent}/' for source in articles}
assert {entry.find('atom:link', ns).attrib['href'] for entry in entries} == expected_urls
assert (site / 'assets/images/galaxy.jpg').is_file()
print(f'Checked {len(articles)} article pages, canonical URLs, assets, and Atom feed')
