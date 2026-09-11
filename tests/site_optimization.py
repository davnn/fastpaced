"""Regression checks for deployment minification."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from optimize_site import minify_page, optimize_site


class Optimization(unittest.TestCase):
    def test_prose_and_sensitive_text_are_unchanged(self):
        for source in [
            '<pre><code>  x &lt; y\n    print("a  b")\n</code></pre>',
            '<p>Hello <em>beautiful</em> <strong>world</strong> &amp; café.</p>',
            '<span class="math inline">\\frac{x^2}{y} + z</span>',
            '<textarea>line one\n  line two</textarea>',
            '<div><span>Title.</span> <em>Journal</em>, April.</div>',
            '<!-- <script> const x = 1; </script> -->',
            '<script src="external.js">  fallback </script>',
            '<script type="text/template"><p> a  b </p></script>',
            '<script type="application/ld+json">{"name": "a  b"}</script>',
        ]:
            with self.subTest(source=source):
                self.assertEqual(minify_page(source), source)

    def test_only_html_changes_and_second_run_is_stable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            page = root / 'index.html'
            page.write_text('<!DOCTYPE html><html><head><title>Test</title></head><body>\n<script> const message = "hello"; console.log(message); </script>\n<p>Hello</p>\n</body></html>')
            attachment = root / 'example.txt'
            attachment.write_bytes(b'  unchanged\n')
            count, before, after = optimize_site(root)
            self.assertEqual(count, 1)
            self.assertLess(after, before)
            self.assertEqual(attachment.read_bytes(), b'  unchanged\n')
            once = page.read_bytes()
            optimize_site(root)
            self.assertEqual(page.read_bytes(), once)
            self.assertTrue(once.endswith(b'</html>'))

    def test_minified_browser_scripts(self):
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            templates = Path(directory)
            for relative in ['partials/theme.html', 'partials/footer.html', 'article.html']:
                source = (repository / 'templates' / relative).read_text()
                output = templates / relative
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(minify_page(source))
            subprocess.run(['node', str(repository / 'tests/browser_scripts.cjs'), str(templates)],
                           check=True, timeout=30)

    def test_empty_page_cli(self):
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / 'index.html').touch()
            result = subprocess.run(
                [sys.executable, str(repository / 'tools/optimize_site.py'), '--site', directory],
                check=True, capture_output=True, text=True, timeout=30,
            )
            self.assertIn('0.0% smaller', result.stdout)

    def test_invalid_later_page_does_not_modify_earlier_pages(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / 'a.html'
            original = b'<script> const message = "hello"; console.log(message); </script>'
            first.write_bytes(original)
            (root / 'z.html').write_bytes(b'\xff')
            with self.assertRaisesRegex(ValueError, 'z.html: HTML must be UTF-8'):
                optimize_site(root)
            self.assertEqual(first.read_bytes(), original)

    def test_missing_output_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, 'build the site first'):
                optimize_site(Path(directory))


if __name__ == '__main__':
    unittest.main()
