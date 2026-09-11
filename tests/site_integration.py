"""Exercise the real generator in an isolated site; uses only Python's stdlib."""
from html.parser import HTMLParser
from pathlib import Path
import json
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ATOM = {'atom': 'http://www.w3.org/2005/Atom'}


class Document(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.tags = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class SiteIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        install = subprocess.check_output(
            ['stack', 'path', '--local-install-root'], cwd=ROOT, text=True, timeout=30
        ).strip()
        cls.executable = Path(install) / 'bin' / 'fastpaced'
        if not cls.executable.is_file():
            raise RuntimeError('Site executable missing; run stack build before these tests')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for directory in ('templates', 'assets'):
            shutil.copytree(ROOT / directory, self.root / directory)
        shutil.copy(ROOT / 'index.html', self.root)
        self.article = self.root / 'articles' / 'example'
        self.article.mkdir(parents=True)
        (self.article / 'index.md').write_text('''---
title: Test article
author: Test Author
published: 2026-01-02
image: picture.svg
mathematics: true
---
A fixture with $x^2$, [a local link](notes.txt), and an image.

![Example](picture.svg){width=200 height=100 loading=lazy}
''')
        (self.article / 'picture.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
        (self.article / 'notes.txt').write_text('Downloadable attachment')
        nested = self.article / 'downloads'
        nested.mkdir()
        (nested / 'data.csv').write_text('x,y\n1,2\n')
        (nested / 'notes.md').write_text('Unpublished source')
        draft = self.root / 'articles' / 'draft'
        draft.mkdir()
        (draft / 'index.hidden.md').write_text('Unpublished draft')
        (draft / 'private.txt').write_text('Unpublished attachment')

    def build(self, success=True, command="rebuild"):
        result = subprocess.run([str(self.executable), command, '+RTS', '-N2', '-RTS'], cwd=self.root,
                                text=True, capture_output=True, timeout=60)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def feed_entry(self):
        feed = ET.parse(self.root / '_site/atom.xml')
        entries = feed.findall('atom:entry', ATOM)
        self.assertEqual(len(entries), 1, 'Expected exactly one published fixture article')
        return entries[0]

    def feed_summary(self):
        summary = self.feed_entry().findtext('atom:summary', namespaces=ATOM)
        self.assertIsNotNone(summary, 'Feed entry is missing its summary')
        return summary

    def test_publication_urls_and_feed(self):
        self.build()
        output = self.root / '_site'
        self.assertTrue((output / 'articles/example/notes.txt').is_file())
        self.assertTrue((output / 'articles/example/downloads/data.csv').is_file())
        self.assertFalse(list(output.rglob('*.md')))
        self.assertFalse(list(output.rglob('*.bib')))
        self.assertFalse((output / 'articles/draft').exists())
        for path, canonical in [('index.html', '/'), ('404.html', '/404.html'),
                                ('articles/example/index.html', '/articles/example/')]:
            text = (output / path).read_text()
            tags = Document(text).tags
            self.assertIn(('link', {'rel': 'canonical', 'href': 'https://fastpaced.com' + canonical}), tags)
            self.assertTrue(text.rstrip().endswith('</html>'))
        article = (output / 'articles/example/index.html').read_text()
        self.assertIn('https://fastpaced.com/articles/example/picture.svg', article)
        self.assertIn('datetime="2026-01-02"', article)
        menu = next(attrs for tag, attrs in Document(article).tags if tag == 'input' and attrs.get('id') == 'nav-toggle')
        self.assertNotIn('hidden', menu)
        self.assertEqual(menu['aria-label'], 'Toggle navigation')
        figure = next(attrs for tag, attrs in Document(article).tags
                      if tag == 'img' and attrs.get('src') == 'picture.svg')
        self.assertEqual((figure['width'], figure['height'], figure['loading']),
                         ('200', '100', 'lazy'))
        math_tags = Document(article).tags
        math_css = next(attrs['href'] for tag, attrs in math_tags
                        if tag == 'link' and attrs.get('href', '').endswith('/katex.min.css'))
        math_js = next(attrs['src'] for tag, attrs in math_tags
                       if tag == 'script' and attrs.get('src', '').endswith('/katex.min.js'))
        self.assertEqual(math_css.rsplit('/', 1)[0], math_js.rsplit('/', 1)[0])
        self.assertTrue(math_js.startswith('https://cdn.jsdelivr.net/npm/katex@'))
        self.assertLess(article.index('katex.min.css'), article.index('</head>'))
        homepage = (output / 'index.html').read_text()
        self.assertNotIn('cdn.jsdelivr.net', homepage)
        self.assertNotIn('rel="preconnect"', homepage)
        preloads = [attrs for tag, attrs in Document(article).tags
                    if tag == 'link' and attrs.get('rel') == 'preload' and attrs.get('as') == 'font']
        self.assertEqual(len(preloads), 1)
        self.assertIn('crossorigin', preloads[0])
        font_path = output / preloads[0]['href'].lstrip('/')
        self.assertEqual(font_path.read_bytes()[:4], b'wOF2')
        self.assertTrue((output / 'assets/fonts/OFL.txt').is_file())
        self.assertEqual(article.count('data-cfasync="false"'), 1)
        self.assertLess(article.index('data-cfasync="false"'), article.index('<body>'))
        content = self.feed_summary()
        self.assertNotIn('<script', content)
        self.assertNotIn('disqus_thread', content)
        self.assertIn('https://fastpaced.com/articles/example/picture.svg', content)
        self.assertIn('https://fastpaced.com/articles/example/notes.txt', content)

    def test_metadata_is_escaped_without_double_escaping_feed(self):
        path = self.article / 'index.md'
        text = path.read_text().replace('title: Test article', "title: 'Quotes \" & <tags> café'").replace('author: Test Author', "author: 'Jane \" & <Doe>'")
        text = text.replace('image: picture.svg', "image: '/assets/images/galaxy.jpg'")
        path.write_text(text)
        self.build()
        html = (self.root / '_site/articles/example/index.html').read_text()
        tags = Document(html).tags
        self.assertIn(('meta', {'property': 'og:title', 'content': 'Quotes " & <tags> café'}), tags)
        self.assertIn(('meta', {'property': 'og:image', 'content': 'https://fastpaced.com/assets/images/galaxy.jpg'}), tags)
        self.assertNotIn('<tags>', html)
        title = self.feed_entry().findtext('atom:title', namespaces=ATOM)
        self.assertEqual(title, 'Quotes " & <tags> café')
        schema = html.split('<script type="application/ld+json">', 1)[1].split('</script>', 1)[0]
        self.assertEqual(json.loads(schema)['@type'], 'Blog')

    def test_false_flags_and_reserved_output(self):
        path = self.article / 'index.md'
        path.write_text(path.read_text().replace('mathematics: true', 'mathematics: false\ncentered: false'))
        (self.article / 'index.html').write_text('This must not replace generated HTML')
        self.build()
        html = (self.root / '_site/articles/example/index.html').read_text()
        self.assertNotIn('katex.min.js', html)
        self.assertNotIn('katex.min.css', html)
        self.assertNotIn('cdn.jsdelivr.net', html)
        self.assertNotIn('class="centered"', html)
        self.assertIn('<h1', html)

    def test_feed_resolves_uri_references(self):
        with (self.article / 'index.md').open('a') as article:
            article.write('\n[Parent](../other/) [Fragment](#section) [Query](?download=1) '
                          '[CDN](//example.org/file) [Email](mailto:test@example.org)\n')
        self.build()
        content = self.feed_summary()
        for url in ('https://fastpaced.com/articles/other/',
                    'https://fastpaced.com/articles/example/#section',
                    'https://fastpaced.com/articles/example/?download=1',
                    'https://example.org/file', 'mailto:test@example.org'):
            self.assertIn(url, content)

    def test_invalid_or_missing_metadata_fails(self):
        path = self.article / 'index.md'
        original = path.read_text()
        for replacement, message in [
            (original.replace('mathematics: true', 'mathematics: typo'), 'mathematics must be true or false'),
            (original.replace('author: Test Author\n', ''), 'missing required metadata field author'),
        ]:
            with self.subTest(message=message):
                path.write_text(replacement)
                self.assertIn(message, self.build(success=False))

    def test_reserved_characters_in_article_paths(self):
        renamed = self.article.with_name('reserved#?%')
        self.article.rename(renamed)
        self.build()
        expected = 'https://fastpaced.com/articles/reserved%23%3F%25/'
        html = (self.root / '_site/articles/reserved#?%/index.html').read_text()
        self.assertIn(('link', {'rel': 'canonical', 'href': expected}), Document(html).tags)
        content = self.feed_summary()
        self.assertIn(expected + 'picture.svg', content)

    def test_article_discovery_treats_names_literally(self):
        self.article.rename(self.article.with_name('draft*'))
        draft = self.root / 'articles/draft'
        (draft / 'references.bib').write_text('@book{private, title={Draft only}}')
        shutil.rmtree(self.root / 'assets/csl')
        self.build()
        self.assertTrue((self.root / '_site/articles/draft*/notes.txt').is_file())
        self.assertFalse((self.root / '_site/articles/draft').exists())

    def test_incremental_resource_discovery(self):
        self.build()
        (self.article / 'new.txt').write_text('Added after the first build')
        (self.article / 'references.bib').write_text(
            '@book{new, title={New Reference}, author={Doe, Jane}, year={2026}}'
        )
        with (self.article / 'index.md').open('a') as article:
            article.write('\nNew citation [@new].\n')
        self.build(command='build')
        output = self.root / '_site/articles/example'
        self.assertEqual((output / 'new.txt').read_text(), 'Added after the first build')
        self.assertIn('ref-new', (output / 'index.html').read_text())
        self.assertFalse((output / 'references.bib').exists())

    def test_publication_date_is_validated_before_fallback(self):
        path = self.article / 'index.md'
        original = path.read_text()
        for value in ('invalid', '2026-02-30', '2025-02-29', '2026-1-2', '2026-01-02T12:00:00Z'):
            with self.subTest(published=value):
                path.write_text(original.replace(
                    'published: 2026-01-02', f'published: {value}\ndate: 2020-01-01'
                ))
                self.assertIn('published must be a valid YYYY-MM-DD date', self.build(success=False))
        # A valid leap day remains the source of truth even with another date field.
        path.write_text(original.replace('published: 2026-01-02', 'published: 2024-02-29\ndate: 2020-01-01'))
        self.build()
        html = (self.root / '_site/articles/example/index.html').read_text()
        self.assertIn('datetime="2024-02-29"', html)
        self.assertTrue(self.feed_entry().findtext('atom:published', namespaces=ATOM).startswith('2024-02-29'))

    def test_no_bibliography_does_not_require_csl(self):
        shutil.rmtree(self.root / 'assets/csl')
        self.build()

    def test_citations_and_ambiguous_bibliography(self):
        bibliography = '@book{sample, title={Example Book}, author={Doe, Jane}, year={2020}}'
        (self.article / 'references.bib').write_text(bibliography)
        with (self.article / 'index.md').open('a') as article:
            article.write('\nA citation [@sample].\n')
        self.build()
        html = (self.root / '_site/articles/example/index.html').read_text()
        self.assertIn('ref-sample', html)
        self.assertFalse(list((self.root / '_site').rglob('*.bib')))
        (self.article / 'second.bib').write_text(bibliography)
        self.assertIn('expected at most one .bib file', self.build(success=False))


if __name__ == '__main__':
    unittest.main()
