"""Find local CJK fonts without downloading or redistributing them."""

from pathlib import Path


def resolve_font(explicit=None, *, handwriting=False):
    if explicit:
        path = Path(explicit).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f'Font not found: {path}')
        return str(path)
    preferred = ['LingWaiSC-Medium.otf', 'LXGWWenKai-Regular.ttf'] if handwriting else ['STHEITI.ttf']
    names = preferred + ['NotoSansSC-Regular.otf', 'NotoSansCJK-Regular.ttc', 'NotoSerifCJK-Regular.ttc']
    roots = [Path('/System/Library/Fonts'), Path('/Library/Fonts'),
             Path.home() / 'Library/Fonts', Path('/usr/share/fonts'),
             Path.home() / '.local/share/fonts']
    roots += sorted(Path('/System/Library/AssetsV2').glob('com_apple_MobileAsset_Font*'))
    for name in names:
        for root in roots:
            if root.is_dir():
                match = next(root.rglob(name), None)
                if match:
                    return str(match)
    option = '--hand-font' if handwriting else '--print-font'
    raise FileNotFoundError(f'No CJK font found. Supply {option} /path/to/font.ttf; no fonts are bundled.')
