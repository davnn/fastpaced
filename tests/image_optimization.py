"""Check lossless image conversion and surgical HTML updates."""
from io import BytesIO
from pathlib import Path
import sys
import struct
import zlib
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
from PIL.PngImagePlugin import PngInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from optimize_images import Images, local_image, lossless_webp, optimize_images


class ImageOptimization(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / 'index.html').write_text('Home')
        self.article = self.root / 'articles/example'
        self.article.mkdir(parents=True)
        self.image = self.article / 'a b.png'
        Image.new('RGBA', (100, 50), (255, 0, 0, 128)).save(self.image)
        self.page = self.article / 'index.html'
        self.source = '<p>A <em> B </em> C</p>\r\n<img data-src="other" src="a%20b.png" width="100" height="50" loading="lazy" alt="a &amp; b">'
        self.page.write_bytes(self.source.encode())

    def test_pipeline_dry_run_preservation_and_idempotence(self):
        original = self.image.read_bytes()
        result = optimize_images(self.root, dry_run=True)
        self.assertEqual(result[1], 1)
        self.assertLess(result[3], result[2])
        self.assertEqual(self.page.read_bytes(), self.source.encode())
        self.assertFalse((self.root / 'assets').exists())
        self.assertEqual(optimize_images(self.root), result)
        updated = self.page.read_bytes().decode()
        start, end, url = Images(updated).images[0]
        self.assertEqual(updated[:start] + '"a%20b.png"' + updated[end:], self.source)
        derivative = self.root / url.lstrip('/')
        self.assertTrue(derivative.is_file())
        self.assertEqual(self.image.read_bytes(), original)
        self.assertEqual(optimize_images(self.root), (0, 0, 0, 0))
        self.assertEqual(self.page.read_bytes().decode(), updated)
        # A Hakyll rebuild restores original references; derivative names stay stable.
        self.page.write_bytes(self.source.encode())
        optimize_images(self.root)
        self.assertEqual(self.page.read_bytes().decode(), updated)

    def test_metadata_is_preserved(self):
        info = PngInfo()
        info.add_text('Copyright', 'Example author')
        Image.new('RGB', (100, 50), 'red').save(self.image, pnginfo=info)
        with Image.open(BytesIO(lossless_webp(self.image))) as decoded:
            self.assertIn(b'Example author', decoded.info['xmp'])

    def test_precision_and_custom_gamma_keep_original(self):
        Image.new('I;16', (10, 10), 10000).save(self.image)
        self.assertIsNone(lossless_webp(self.image))
        info = PngInfo()
        info.add(b'gAMA', struct.pack('>I', 100000))
        Image.new('RGB', (100, 50), 'red').save(self.image, pnginfo=info)
        self.assertIsNone(lossless_webp(self.image))

    def test_16_bit_rgb_is_not_mistaken_for_8_bit_rgb(self):
        def chunk(kind, data):
            return (struct.pack('>I', len(data)) + kind + data
                    + struct.pack('>I', zlib.crc32(kind + data)))
        self.image.write_bytes(
            b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 16, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(b'\0' + struct.pack('>HHH', 10000, 20000, 30000)))
            + chunk(b'IEND', b'')
        )
        with Image.open(self.image) as decoded:
            self.assertEqual(decoded.mode, 'RGB')
        self.assertIsNone(lossless_webp(self.image))

    def test_ambiguous_source_attributes_are_untouched(self):
        self.assertEqual(Images('<img src="first.png" src="second.png">').images, [])
        # Mixed casing and attribute-like text inside values remain unambiguous.
        source = '<IMG alt=" src=wrong.png " SRC=right.png>'
        start, end, url = Images(source).images[0]
        self.assertEqual(source[start:end], 'right.png')
        self.assertEqual(url, 'right.png')

    def test_larger_conversion_is_retained(self):
        with patch('optimize_images.lossless_webp', return_value=b'x' * 10000):
            self.assertEqual(optimize_images(self.root)[1], 0)
        self.assertEqual(self.page.read_bytes().decode(), self.source)

    def test_animation_and_finite_loop_fallback(self):
        path = self.article / 'animated.gif'
        frames = [Image.new('RGB', (20, 20), color) for color in ['red', 'blue']]
        frames[0].save(path, save_all=True, append_images=frames[1:], duration=[100, 200], loop=0)
        data = lossless_webp(path)
        self.assertIsNotNone(data)
        with Image.open(BytesIO(data)) as decoded:
            self.assertEqual(decoded.n_frames, 2)
            self.assertEqual(decoded.info['loop'], 0)
        frames[0].save(path, save_all=True, append_images=frames[1:], duration=[100, 200], loop=2)
        self.assertIsNone(lossless_webp(path))

    def test_url_boundaries_and_existing_responsive_markup(self):
        for url in ['https://example.com/a.png', '//example.com/a.png', 'data:image/png,x', 'a.png?v=1']:
            self.assertIsNone(local_image(self.root, self.page, url))
        with self.assertRaisesRegex(ValueError, 'escapes'):
            local_image(self.root, self.page, '../../../private.png')
        self.assertEqual(Images('<picture><img src="a.png"></picture><img src="b.png" srcset="b.png 1x">').images, [])

    def test_corrupt_image_fails_before_writing(self):
        self.image.write_bytes(b'broken')
        with self.assertRaises(OSError):
            optimize_images(self.root)
        self.assertEqual(self.page.read_bytes().decode(), self.source)
        self.assertFalse((self.root / 'assets').exists())


if __name__ == '__main__':
    unittest.main()
