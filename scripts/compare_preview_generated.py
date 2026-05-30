import json
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.abspath('prototypes/backend/generation/generation_scripts'))
sys.path.insert(0, os.path.abspath('prototypes/backend/generation'))

from utils.loading_json_utils import get_application_component
from utils.template_generation import _render_unified_page
from api.model.llm.template_renderer import render_preview

metadata_path = Path(__file__).resolve().parent / 'fixtures' / 'Bol.com Shopping Platform-export.json'
metadata = metadata_path.read_text(encoding='utf-8')
metadata_json = json.loads(metadata)
interfaces = metadata_json.get('interfaces', [])
print('interfaces count', len(interfaces))

# choose Seller if exists
selected = next((i for i in interfaces if i.get('name') == 'Seller'), interfaces[0] if interfaces else None)
if not selected:
    raise SystemExit('No interface found in metadata')
app_name = selected.get('name')
print('selected app:', app_name)

application_component = get_application_component('bol.com-shopping-platform', app_name, metadata, False)
print('pages:', [p.name for p in application_component.pages[:5]])

tokens = {}
styling = getattr(application_component, 'styling', None)
accent = getattr(styling, 'accent_color', '') if styling else ''
if accent and 'region.header.bg' not in tokens:
    tokens['region.header.bg'] = f'bg-[{accent}]'
    tokens['page.header.text'] = 'text-white'
    tokens['accent.hex'] = accent
    tokens['brand.name'] = app_name

page = application_component.pages[0]
print('page selected:', page.name)

preview_files = render_preview({'tokens': tokens, 'styling': {'accentColor': accent}}, [], app_name)
preview_html = next((f['content'] for f in preview_files if f['path'].endswith(f'_{page.name}.html')), None)
print('preview exists', preview_html is not None)

actual_html = _render_unified_page(
    page=page,
    all_pages=application_component.pages,
    tokens=tokens,
    styling=styling,
    application_name=app_name,
    project_name='bol-com-shopping-platform',
    preview_mode=False,
)
print('actual len', len(actual_html))
print('actual starts', actual_html[:120].replace('\n', ' '))
print('preview starts', preview_html[:120].replace('\n', ' ') if preview_html else 'NONE')
import difflib
ratio = difflib.SequenceMatcher(None, preview_html, actual_html).ratio() if preview_html else None
print('ratio', ratio)
diff = list(difflib.unified_diff(preview_html.splitlines(), actual_html.splitlines(), lineterm='')) if preview_html else []
print('\n'.join(diff[:100]))
