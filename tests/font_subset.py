"""Check font character collection and reproducibility on isolated HTML."""
from io import BytesIO
from pathlib import Path
import sys
import tempfile
import unittest

from fontTools.ttLib import TTFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from subset_font import VisibleText, build_subset


class FontSubset(unittest.TestCase):
    def test_metadata_and_scripts_do_not_add_characters(self):
        parser = VisibleText()
        parser.feed('<head><title>Ω</title><style>Ж</style></head>'
                    '<body><script>λ</script><p>café &amp; tea</p></body>')
        parser.close()
        self.assertEqual(parser.characters, set(map(ord, 'café & tea')))

    def test_trailing_character_reference_and_deterministic_output(self):
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory)
            # HTML accepts a numeric reference terminated by end-of-file.
            (site / 'index.html').write_text('<!doctype html><body>caf&#233', encoding='utf-8')
            first, count = build_subset(site)
            self.assertEqual(build_subset(site), (first, count))
            with TTFont(BytesIO(first)) as font:
                self.assertIn(ord('é'), font.getBestCmap())
                self.assertEqual([(axis.axisTag, axis.minValue, axis.maxValue)
                                  for axis in font['fvar'].axes], [('wght', 400, 800)])


if __name__ == '__main__':
    unittest.main()
