"""Create verified lossless WebP derivatives for local article images."""
import argparse
import base64
import hashlib
import json
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
from typing import NamedTuple

from PIL import Image, ImageSequence

DERIVED = Path('assets/derived')
# Tokenize attributes so data-src and quoted attribute contents cannot match src.
ATTRIBUTE = re.compile(r'''\s+([^\s=/>]+)(?:\s*=\s*("[^"]*"|'[^']*'|[^\s>]+))?''')


class ImageResult(NamedTuple):
    original_size: int
    selected_size: int
    target: Path | None
    data: bytes | None


class Images(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.offsets = [0]
        for line in source.split('\n'):
            self.offsets.append(self.offsets[-1] + len(line) + 1)
        self.images = []
        self.picture = 0
        self.feed(source)
        self.close()

    def handle_starttag(self, tag, attrs):
        if tag == 'picture':
            self.picture += 1
        attributes = dict(attrs)
        if tag != 'img' or self.picture or 'srcset' in attributes:
            return
        # Duplicate attributes are invalid; avoid disagreeing with browser parsing.
        if sum(name == 'src' for name, _ in attrs) != 1:
            return
        raw = self.get_starttag_text()
        for match in ATTRIBUTE.finditer(raw[4:]):
            if match[1].lower() == 'src' and match[2] is not None:
                line, column = self.getpos()
                start = self.offsets[line - 1] + column + 4
                self.images.append((start + match.start(2), start + match.end(2), attributes['src']))
                break

    def handle_endtag(self, tag):
        if tag == 'picture':
            self.picture = max(0, self.picture - 1)


def local_image(root, page, url):
    parsed = urlsplit(url)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        return None
    path = unquote(parsed.path)
    candidate = (root / path.lstrip('/') if path.startswith('/') else page.parent / path).resolve()
    if not candidate.is_relative_to(root):
        raise ValueError(f'Image escapes site directory: {url}')
    if candidate.is_relative_to(root / DERIVED) or candidate.suffix.lower() not in {'.png', '.gif'}:
        return None
    return candidate


def webp_metadata(image):
    """Return preservable WebP metadata, or None when conversion is unsafe."""
    # WebP is 8-bit. RGBA conversion would hide precision loss in our check.
    if image.mode not in {'1', 'L', 'LA', 'P', 'RGB', 'RGBA'}:
        return None
    # Custom PNG gamma/chromaticity cannot be carried by WebP without an ICC
    # conversion. Preserve the source unless an explicit profile defines it.
    if not image.info.get('icc_profile') and 'srgb' not in image.info:
        gamma = image.info.get('gamma')
        if 'chromaticity' in image.info or (gamma is not None and abs(gamma - 0.45455) > 0.00001):
            return None
    metadata = {key: image.info[key] for key in ('icc_profile', 'exif', 'xmp')
                if image.info.get(key)}
    text = dict(getattr(image, 'text', {}))
    if 'XML:com.adobe.xmp' in text and 'xmp' in metadata:
        if text['XML:com.adobe.xmp'].encode('utf-8') == metadata['xmp']:
            del text['XML:com.adobe.xmp']
    if image.info.get('comment'):
        text['gifCommentBase64'] = base64.b64encode(image.info['comment']).decode('ascii')
    if image.getexif().get(274, 1) != 1:
        return None
    if text:
        if 'xmp' in metadata:
            return None  # Do not overwrite an existing XMP packet.
        packet = ET.Element('{adobe:ns:meta/}xmpmeta')
        rdf = ET.SubElement(packet, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF')
        description = ET.SubElement(rdf, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description')
        description.set('{https://fastpaced.com/ns/image/}pngText',
                        json.dumps(text, sort_keys=True, ensure_ascii=False))
        metadata['xmp'] = ET.tostring(packet, encoding='utf-8')
    return metadata


def lossless_webp(source):
    # Pillow presents even 16-bit RGB PNGs as RGB mode after decoding. Inspect
    # IHDR bit depth before an 8-bit conversion can hide that precision loss.
    with source.open('rb') as stream:
        header = stream.read(25)
    with Image.open(source) as image:
        if header.startswith(b'\x89PNG\r\n\x1a\n') and len(header) == 25 and header[24] > 8:
            return None
        animated = getattr(image, 'n_frames', 1) > 1
        loop = image.info.get('loop')
        # Reject unsupported loop semantics before materializing every frame.
        if animated and loop != 0:
            return None
        metadata = webp_metadata(image)
        if metadata is None:
            return None
        frames = []
        durations = []
        for frame in ImageSequence.Iterator(image):
            frames.append(frame.convert('RGBA'))
            durations.append(frame.info.get('duration', 0))
        options = dict(format='WEBP', lossless=True, method=4, exact=True, **metadata)
        if animated:
            options.update(save_all=True, append_images=frames[1:], duration=durations, loop=loop)
        output = BytesIO()
        frames[0].save(output, **options)
        data = output.getvalue()
    with Image.open(BytesIO(data)) as decoded:
        if any(decoded.info.get(key) != value for key, value in metadata.items()):
            raise ValueError(f'Conversion changed metadata: {source}')
        if decoded.n_frames != len(frames):
            return None  # Encoders can merge identical frames; keep original semantics.
        if animated and decoded.info.get('loop') != loop:
            return None
        for index, frame in enumerate(ImageSequence.Iterator(decoded)):
            if frame.convert('RGBA').tobytes() != frames[index].tobytes():
                raise ValueError(f'Lossless conversion changed pixels: {source}')
            if animated and frame.info.get('duration', 0) != durations[index]:
                return None
    return data


def optimize_images(site, dry_run=False):
    root = site.resolve()
    pages = sorted((root / 'articles').rglob('*.html'))
    if not (root / 'index.html').is_file():
        raise ValueError('Site output missing; build the site first')
    results = {}
    edits = {}
    for page in pages:
        source = page.read_bytes().decode('utf-8')
        replacements = []
        for start, end, url in Images(source).images:
            image = local_image(root, page, url)
            if image is None:
                continue
            if image not in results:
                original_size = image.stat().st_size
                data = lossless_webp(image)
                if data is None or len(data) >= original_size:
                    results[image] = ImageResult(original_size, original_size, None, None)
                else:
                    name = hashlib.sha256(data).hexdigest() + '.webp'
                    target = DERIVED / name
                    results[image] = ImageResult(original_size, len(data), target, data)
            target = results[image].target
            if target is not None:
                replacements.append((start, end, '"/' + target.as_posix() + '"'))
        for start, end, replacement in reversed(replacements):
            source = source[:start] + replacement + source[end:]
        if replacements:
            edits[page] = source.encode('utf-8')
    # Validate all referenced images before writing any HTML or derivatives.
    if not dry_run:
        for _, _, target, data in results.values():
            if target is not None:
                destination = root / target
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(data)
        for page, data in edits.items():
            page.write_bytes(data)
    before = sum(result.original_size for result in results.values())
    after = sum(result.selected_size for result in results.values())
    converted = sum(result.target is not None for result in results.values())
    return len(results), converted, before, after


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', type=Path, default=Path(__file__).resolve().parents[1] / '_site')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        count, converted, before, after = optimize_images(args.site, args.dry_run)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    reduction = 1 - after / before if before else 0
    print(f'{count} source images: {converted} converted, {count - converted} retained; '
          f'{before:,} → {after:,} bytes ({reduction:.1%} smaller)'
          + (' [dry run]' if args.dry_run else ''))


if __name__ == '__main__':
    main()
