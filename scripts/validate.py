"""Dependency-free structural, color, and syntax contrast checks (Python 3.9+)."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate JSON key: {key}')
        result[key] = value
    return result


def luminance(color):
    channels = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return sum((c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4) * w
               for c, w in zip(channels, (0.2126, 0.7152, 0.0722)))


def check_colors(value):
    if isinstance(value, dict):
        for child in value.values():
            check_colors(child)
    elif isinstance(value, list):
        for child in value:
            check_colors(child)
    elif isinstance(value, str) and value.startswith('#'):
        if not re.fullmatch(r'#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?', value):
            raise ValueError(f'Invalid hex color: {value}')


def main():
    family = json.loads((ROOT / 'themes/zed-paper.json').read_text(),
                        object_pairs_hook=unique_object)
    assert family['name'] and family['author']
    assert len(family['themes']) == 2
    assert {t['appearance'] for t in family['themes']} == {'light', 'dark'}
    assert len({t['name'] for t in family['themes']}) == 2
    for theme in family['themes']:
        style = theme['style']
        check_colors(style)
        for key in ('editor.background', 'editor.foreground', 'text', 'players', 'syntax'):
            assert style[key], f'Missing {key}'
        ratios = []
        for capture, token in style['syntax'].items():
            assert re.fullmatch(r'#[0-9a-fA-F]{6}', token['color']), capture
            for background in ('editor.background', 'editor.active_line.background'):
                bg, fg = luminance(style[background]), luminance(token['color'])
                ratio = (max(bg, fg) + 0.05) / (min(bg, fg) + 0.05)
                assert ratio >= 4.5, (theme['name'], capture, background, ratio)
                ratios.append(ratio)
        print(f"{theme['name']}: {len(style['syntax'])} syntax colors; minimum contrast {min(ratios):.2f}:1")
    print('Theme checks passed (not a full upstream JSON Schema validation).')


if __name__ == '__main__':
    main()
