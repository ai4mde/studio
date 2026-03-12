"""
Static HTML preview generator for Interface candidates.
Generates a complete standalone HTML page with inline CSS for preview.
Supports multiple layout types: sidebar, topnav, dashboard, split, wizard, minimal.
"""

from typing import Dict, List, Any


def generate_preview_html(interface_data: Dict[str, Any], name: str = "Preview") -> str:
    """
    Generate a static HTML preview of an Interface.
    
    Args:
        interface_data: Interface.data structure with sections, pages, categories, styling
        name: Application name for display
        
    Returns:
        Complete HTML string with inline CSS
    """
    styling = interface_data.get('styling', {})
    sections = interface_data.get('sections', [])
    pages = interface_data.get('pages', [])
    categories = interface_data.get('categories', [])
    
    # Extract styling values
    layout_type = styling.get('layoutType', 'sidebar')
    style_type = styling.get('selectedStyle', 'modern')
    radius = styling.get('radius', 8)
    text_color = styling.get('textColor', '#000000')
    accent_color = styling.get('accentColor', '#3b82f6')
    background_color = styling.get('backgroundColor', '#ffffff')
    
    # Route to appropriate layout generator
    layout_generators = {
        'sidebar': _generate_sidebar_layout,
        'topnav': _generate_topnav_layout,
        'dashboard': _generate_dashboard_layout,
        'split': _generate_split_layout,
        'wizard': _generate_wizard_layout,
        'minimal': _generate_minimal_layout,
    }
    
    generator = layout_generators.get(layout_type, _generate_sidebar_layout)
    return generator(name, styling, sections, pages, categories)


def _generate_sidebar_layout(name: str, styling: Dict, sections: List, pages: List, categories: List) -> str:
    """Sidebar navigation layout."""
    r = styling.get('radius', 8)
    tc = styling.get('textColor', '#1a1a1a')
    ac = styling.get('accentColor', '#3b82f6')
    bg = styling.get('backgroundColor', '#f8fafc')
    
    menu = _build_sidebar_menu(pages, tc, ac)
    content = _build_card_content(sections, r, ac, tc)
    
    return f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{name}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:{bg};color:{tc};display:flex;min-height:100vh}}
.sidebar{{width:220px;background:#fff;border-right:1px solid #e2e8f0;padding:16px 0;position:fixed;height:100vh}}
.sidebar h1{{padding:0 16px 16px;font-size:16px;color:{ac};border-bottom:1px solid #e2e8f0}}
.sidebar .cat{{padding:8px 16px 4px;font-size:10px;font-weight:600;text-transform:uppercase;color:#94a3b8;margin-top:12px}}
.sidebar a{{display:block;padding:8px 16px;color:{tc};text-decoration:none;font-size:13px;border-left:3px solid transparent}}
.sidebar a:hover,.sidebar a.active{{background:{_lighten(ac)};border-left-color:{ac};color:{ac}}}
.main{{flex:1;margin-left:220px;padding:24px}}
.topbar{{display:flex;justify-content:space-between;align-items:center;margin-bottom:24px}}
.topbar h2{{font-size:22px}}
.btn{{padding:8px 16px;background:{ac};color:#fff;border:none;border-radius:{r}px;cursor:pointer;font-size:13px}}
.card{{background:#fff;border-radius:{r}px;padding:20px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,0.08)}}
.card h3{{font-size:14px;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid #e2e8f0}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;padding:10px;background:{bg};font-size:11px;font-weight:600;text-transform:uppercase;color:#64748b}}
td{{padding:10px;border-bottom:1px solid #e2e8f0;font-size:13px}}
.badge{{display:inline-block;padding:3px 6px;border-radius:4px;font-size:10px;font-weight:600;margin-right:4px}}
.b-c{{background:#dcfce7;color:#16a34a}}.b-u{{background:#dbeafe;color:#2563eb}}.b-d{{background:#fee2e2;color:#dc2626}}
</style></head>
<body>
<nav class="sidebar"><h1>{name}</h1><a href="#" class="active">Home</a>{menu}</nav>
<main class="main"><div class="topbar"><h2>Dashboard</h2><button class="btn">+ New</button></div>{content}</main>
</body></html>'''


def _generate_topnav_layout(name: str, styling: Dict, sections: List, pages: List, categories: List) -> str:
    """Top navigation bar layout."""
    r = styling.get('radius', 0)
    tc = styling.get('textColor', '#333')
    ac = styling.get('accentColor', '#22c55e')
    bg = styling.get('backgroundColor', '#fff')
    
    menu = _build_topnav_menu(pages, tc)
    content = _build_table_content(sections, ac, tc)
    
    return f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{name}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Arial,sans-serif;background:#f5f5f5;color:{tc}}}
.topnav{{background:{ac};padding:0 20px;display:flex;align-items:center;height:52px;box-shadow:0 2px 4px rgba(0,0,0,0.1)}}
.topnav .logo{{font-size:18px;font-weight:bold;color:#fff;margin-right:30px}}
.topnav a{{color:rgba(255,255,255,0.9);text-decoration:none;padding:14px 14px;font-size:13px;border-bottom:3px solid transparent}}
.topnav a:hover,.topnav a.active{{background:rgba(0,0,0,0.1);border-bottom-color:#fff}}
.dropdown{{position:relative}}.dropdown-content{{display:none;position:absolute;top:100%;left:0;background:#fff;min-width:160px;box-shadow:0 4px 12px rgba(0,0,0,0.15);z-index:100}}
.dropdown:hover .dropdown-content{{display:block}}
.dropdown-content a{{color:{tc};padding:10px 14px;display:block;border-bottom:none}}.dropdown-content a:hover{{background:#f0f0f0}}
.container{{max-width:1100px;margin:0 auto;padding:24px 16px}}
.breadcrumb{{font-size:12px;color:#666;margin-bottom:16px}}
.page-title{{font-size:24px;font-weight:normal;margin-bottom:16px;padding-bottom:8px;border-bottom:2px solid {ac}}}
.toolbar{{background:#fff;padding:10px 14px;border:1px solid #ddd;border-bottom:none;display:flex;gap:6px}}
.toolbar button{{padding:6px 12px;background:{ac};color:#fff;border:none;cursor:pointer;font-size:12px}}
.toolbar button.sec{{background:#666}}
table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #ddd}}
th{{text-align:left;padding:12px 10px;background:#f9f9f9;border-bottom:2px solid #ddd;font-weight:bold;font-size:12px}}
td{{padding:10px;border-bottom:1px solid #eee;font-size:13px}}
tr:hover td{{background:#fafafa}}
.section{{margin-bottom:24px}}
.section-header{{background:#f0f0f0;padding:10px 14px;font-weight:bold;border:1px solid #ddd}}
</style></head>
<body>
<nav class="topnav"><div class="logo">{name}</div><a href="#" class="active">Home</a>{menu}</nav>
<div class="container"><div class="breadcrumb">Home &gt; Data</div><h1 class="page-title">Data Management</h1>{content}</div>
</body></html>'''


def _generate_dashboard_layout(name: str, styling: Dict, sections: List, pages: List, categories: List) -> str:
    """Dashboard with metrics layout (typically dark theme)."""
    r = styling.get('radius', 16)
    tc = styling.get('textColor', '#e2e8f0')
    ac = styling.get('accentColor', '#f59e0b')
    bg = styling.get('backgroundColor', '#1e293b')
    
    content = _build_dashboard_widgets(sections, r, ac, tc, bg)
    
    return f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{name}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',system-ui,sans-serif;background:{bg};color:{tc};min-height:100vh}}
.dash{{display:grid;grid-template-columns:64px 1fr;min-height:100vh}}
.icon-nav{{background:#0f172a;padding:16px 0;display:flex;flex-direction:column;align-items:center;gap:6px}}
.icon-nav .logo{{width:36px;height:36px;background:{ac};border-radius:10px;display:flex;align-items:center;justify-content:center;font-weight:bold;color:#0f172a;margin-bottom:16px;font-size:14px}}
.icon-nav a{{width:40px;height:40px;display:flex;align-items:center;justify-content:center;color:#64748b;text-decoration:none;border-radius:10px;font-size:16px}}
.icon-nav a:hover,.icon-nav a.active{{background:{bg};color:{ac}}}
.main{{padding:20px}}
.top-bar{{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}}
.top-bar h1{{font-size:20px}}
.search{{background:#334155;border:none;padding:8px 14px;border-radius:{r}px;color:{tc};width:260px;font-size:13px}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px}}
.stat{{background:#334155;border-radius:{r}px;padding:16px}}
.stat .label{{font-size:11px;color:#94a3b8;text-transform:uppercase}}
.stat .value{{font-size:24px;font-weight:700;color:{ac};margin-top:2px}}
.stat .change{{font-size:11px;color:#22c55e;margin-top:2px}}
.widgets{{display:grid;grid-template-columns:2fr 1fr;gap:14px}}
.widget{{background:#334155;border-radius:{r}px;padding:16px}}
.widget h3{{font-size:13px;margin-bottom:14px;display:flex;justify-content:space-between}}
.widget h3 span{{font-size:11px;color:{ac};cursor:pointer}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;padding:8px 0;font-size:10px;color:#94a3b8;text-transform:uppercase;border-bottom:1px solid #475569}}
td{{padding:10px 0;font-size:12px;border-bottom:1px solid #475569}}
.badge{{display:inline-block;padding:3px 8px;border-radius:14px;font-size:10px}}
.b-s{{background:rgba(34,197,94,0.2);color:#22c55e}}.b-w{{background:rgba(245,158,11,0.2);color:#f59e0b}}.b-i{{background:rgba(59,130,246,0.2);color:#3b82f6}}
.activity-item{{display:flex;align-items:center;padding:10px 0;border-bottom:1px solid #475569}}
.activity-item:last-child{{border-bottom:none}}
.dot{{width:6px;height:6px;border-radius:50%;background:{ac};margin-right:10px}}
.activity-text{{font-size:12px;flex:1}}
.activity-time{{font-size:10px;color:#94a3b8}}
</style></head>
<body>
<div class="dash">
<nav class="icon-nav"><div class="logo">{name[0].upper()}</div><a href="#" class="active">⌂</a><a href="#">📊</a><a href="#">📁</a><a href="#">👤</a><a href="#">⚙</a></nav>
<main class="main">
<div class="top-bar"><h1>Dashboard</h1><input type="text" class="search" placeholder="Search..."></div>
<div class="stats">
<div class="stat"><div class="label">Total Items</div><div class="value">2,847</div><div class="change">↑ 12%</div></div>
<div class="stat"><div class="label">Active</div><div class="value">142</div><div class="change">↑ 8%</div></div>
<div class="stat"><div class="label">Pending</div><div class="value">28</div><div class="change">↓ 3%</div></div>
<div class="stat"><div class="label">Complete</div><div class="value">89%</div><div class="change">↑ 5%</div></div>
</div>
{content}
</main></div>
</body></html>'''


def _generate_split_layout(name: str, styling: Dict, sections: List, pages: List, categories: List) -> str:
    """Two-panel split layout."""
    r = styling.get('radius', 8)
    tc = styling.get('textColor', '#374151')
    ac = styling.get('accentColor', '#8b5cf6')
    bg = styling.get('backgroundColor', '#faf5ff')
    
    menu = _build_list_menu(pages, tc, ac)
    content = _build_detail_content(sections, r, ac, tc)
    
    return f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{name}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:{bg};color:{tc};min-height:100vh}}
.header{{background:{ac};color:#fff;padding:12px 20px;display:flex;align-items:center;justify-content:space-between}}
.header h1{{font-size:16px;font-weight:600}}
.header input{{background:rgba(255,255,255,0.2);border:none;padding:6px 12px;border-radius:{r}px;color:#fff;font-size:12px;width:200px}}
.header input::placeholder{{color:rgba(255,255,255,0.7)}}
.split{{display:grid;grid-template-columns:300px 1fr;height:calc(100vh - 48px)}}
.list-panel{{background:#fff;border-right:1px solid #e5e7eb;overflow-y:auto}}
.list-header{{padding:12px 16px;border-bottom:1px solid #e5e7eb;font-size:12px;font-weight:600;color:#6b7280;display:flex;justify-content:space-between}}
.list-item{{padding:12px 16px;border-bottom:1px solid #f3f4f6;cursor:pointer;display:flex;align-items:center;gap:10px}}
.list-item:hover{{background:#f9fafb}}
.list-item.active{{background:{_lighten(ac)};border-left:3px solid {ac}}}
.list-avatar{{width:32px;height:32px;border-radius:50%;background:{ac};color:#fff;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:600}}
.list-info h4{{font-size:13px;margin-bottom:2px}}
.list-info p{{font-size:11px;color:#6b7280}}
.detail-panel{{padding:24px;overflow-y:auto}}
.detail-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}}
.detail-header h2{{font-size:18px}}
.btn{{padding:8px 14px;background:{ac};color:#fff;border:none;border-radius:{r}px;cursor:pointer;font-size:12px}}
.btn-outline{{background:transparent;border:1px solid {ac};color:{ac}}}
.detail-card{{background:#fff;border-radius:{r}px;padding:20px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,0.06)}}
.detail-card h3{{font-size:13px;color:#6b7280;margin-bottom:12px}}
.field{{margin-bottom:12px}}
.field label{{display:block;font-size:11px;color:#6b7280;margin-bottom:4px}}
.field input,.field select{{width:100%;padding:8px 10px;border:1px solid #e5e7eb;border-radius:{r}px;font-size:13px}}
</style></head>
<body>
<div class="header"><h1>{name}</h1><input type="text" placeholder="Search..."></div>
<div class="split">
<div class="list-panel"><div class="list-header"><span>All Items</span><span>24 total</span></div>{menu}</div>
<div class="detail-panel"><div class="detail-header"><h2>Item Details</h2><div><button class="btn btn-outline">Edit</button> <button class="btn">Save</button></div></div>{content}</div>
</div>
</body></html>'''


def _generate_wizard_layout(name: str, styling: Dict, sections: List, pages: List, categories: List) -> str:
    """Step-by-step wizard layout."""
    r = styling.get('radius', 12)
    tc = styling.get('textColor', '#1f2937')
    ac = styling.get('accentColor', '#0ea5e9')
    bg = styling.get('backgroundColor', '#f0f9ff')
    
    steps = _build_wizard_steps(sections, ac)
    content = _build_wizard_content(sections, r, ac, tc)
    
    return f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{name}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:{bg};color:{tc};min-height:100vh;display:flex;flex-direction:column}}
.header{{background:#fff;padding:16px 24px;border-bottom:1px solid #e0f2fe;display:flex;align-items:center;gap:12px}}
.header h1{{font-size:18px;color:{ac}}}
.wizard-container{{flex:1;display:flex;flex-direction:column;max-width:800px;margin:0 auto;padding:32px 24px;width:100%}}
.steps{{display:flex;justify-content:center;margin-bottom:32px}}
.step{{display:flex;align-items:center}}
.step-circle{{width:32px;height:32px;border-radius:50%;background:#e0f2fe;color:{ac};display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:600}}
.step.active .step-circle{{background:{ac};color:#fff}}
.step.done .step-circle{{background:#22c55e;color:#fff}}
.step-label{{margin-left:8px;font-size:12px;color:#6b7280}}
.step.active .step-label{{color:{tc};font-weight:600}}
.step-line{{width:60px;height:2px;background:#e0f2fe;margin:0 8px}}
.step.done+.step .step-line{{background:{ac}}}
.wizard-content{{background:#fff;border-radius:{r}px;padding:32px;flex:1;box-shadow:0 1px 3px rgba(0,0,0,0.06)}}
.wizard-content h2{{font-size:20px;margin-bottom:8px}}
.wizard-content p{{color:#6b7280;font-size:13px;margin-bottom:24px}}
.form-group{{margin-bottom:16px}}
.form-group label{{display:block;font-size:12px;font-weight:600;margin-bottom:6px}}
.form-group input,.form-group select,.form-group textarea{{width:100%;padding:10px 12px;border:1px solid #e5e7eb;border-radius:{r}px;font-size:13px}}
.wizard-footer{{display:flex;justify-content:space-between;margin-top:24px;padding-top:24px;border-top:1px solid #e5e7eb}}
.btn{{padding:10px 20px;border-radius:{r}px;cursor:pointer;font-size:13px;font-weight:500}}
.btn-primary{{background:{ac};color:#fff;border:none}}
.btn-secondary{{background:#fff;border:1px solid #d1d5db;color:{tc}}}
</style></head>
<body>
<div class="header"><h1>{name}</h1></div>
<div class="wizard-container">
<div class="steps">{steps}</div>
<div class="wizard-content"><h2>Step Details</h2><p>Complete the following information to proceed.</p>{content}
<div class="wizard-footer"><button class="btn btn-secondary">← Previous</button><button class="btn btn-primary">Continue →</button></div>
</div>
</div>
</body></html>'''


def _generate_minimal_layout(name: str, styling: Dict, sections: List, pages: List, categories: List) -> str:
    """Minimal single-page with tabs layout."""
    r = styling.get('radius', 4)
    tc = styling.get('textColor', '#18181b')
    ac = styling.get('accentColor', '#ec4899')
    bg = styling.get('backgroundColor', '#fdf2f8')
    
    tabs = _build_tabs(sections, ac)
    content = _build_minimal_content(sections, r, ac, tc)
    
    return f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{name}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:system-ui,sans-serif;background:{bg};color:{tc};min-height:100vh}}
.container{{max-width:960px;margin:0 auto;padding:40px 24px}}
.header{{text-align:center;margin-bottom:32px}}
.header h1{{font-size:28px;font-weight:300;margin-bottom:8px}}
.header p{{color:#71717a;font-size:14px}}
.tabs{{display:flex;justify-content:center;gap:4px;margin-bottom:24px;background:#fff;padding:4px;border-radius:{r}px;display:inline-flex;margin-left:50%;transform:translateX(-50%)}}
.tab{{padding:8px 16px;border-radius:{r}px;font-size:13px;cursor:pointer;color:#71717a;border:none;background:transparent}}
.tab.active{{background:{ac};color:#fff}}
.tab:hover:not(.active){{background:#fce7f3}}
.content-area{{background:#fff;border-radius:{r}px;padding:24px;box-shadow:0 1px 2px rgba(0,0,0,0.05)}}
.section-title{{font-size:16px;font-weight:600;margin-bottom:16px;display:flex;align-items:center;gap:8px}}
.section-title::before{{content:'';width:4px;height:16px;background:{ac};border-radius:2px}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;padding:10px 12px;font-size:11px;font-weight:600;text-transform:uppercase;color:#a1a1aa;border-bottom:1px solid #f4f4f5}}
td{{padding:12px;font-size:13px;border-bottom:1px solid #f4f4f5}}
.actions{{display:flex;justify-content:flex-end;gap:8px;margin-top:16px}}
.btn{{padding:8px 14px;border-radius:{r}px;font-size:12px;cursor:pointer}}
.btn-primary{{background:{ac};color:#fff;border:none}}
.btn-ghost{{background:transparent;border:1px solid #e4e4e7;color:{tc}}}
</style></head>
<body>
<div class="container">
<div class="header"><h1>{name}</h1><p>Manage your data efficiently</p></div>
<div class="tabs">{tabs}</div>
<div class="content-area">{content}
<div class="actions"><button class="btn btn-ghost">Cancel</button><button class="btn btn-primary">Save Changes</button></div>
</div>
</div>
</body></html>'''


# Helper functions
def _lighten(color: str) -> str:
    if not color.startswith('#') or len(color) != 7:
        return '#f0f0f0'
    try:
        r = min(255, int(color[1:3], 16) + 40)
        g = min(255, int(color[3:5], 16) + 40)
        b = min(255, int(color[5:7], 16) + 40)
        return f"#{r:02x}{g:02x}{b:02x}"
    except (ValueError, TypeError):
        return '#f0f0f0'


def _build_sidebar_menu(pages: List, tc: str, ac: str) -> str:
    categorized = {}
    for p in pages:
        cat = p.get('category', {}).get('label', '') if isinstance(p.get('category'), dict) else ''
        categorized.setdefault(cat or 'General', []).append(p.get('name', 'Page'))
    
    html = ''
    for cat, names in categorized.items():
        html += f'<div class="cat">{cat}</div>'
        for n in names:
            html += f'<a href="#">{n}</a>'
    return html or '<a href="#">Sample</a>'


def _build_topnav_menu(pages: List, tc: str) -> str:
    categorized = {}
    for p in pages:
        cat = p.get('category', {}).get('label', '') if isinstance(p.get('category'), dict) else ''
        if cat:
            categorized.setdefault(cat, []).append(p.get('name', 'Page'))
    
    html = ''
    for cat, names in categorized.items():
        items = ''.join([f'<a href="#">{n}</a>' for n in names])
        html += f'<div class="dropdown"><a href="#">{cat} ▼</a><div class="dropdown-content">{items}</div></div>'
    return html or '<a href="#">Data</a>'


def _build_card_content(sections: List, r: int, ac: str, tc: str) -> str:
    if not sections:
        return '<div class="card"><h3>No Data</h3></div>'
    
    html = ''
    for s in sections[:2]:
        name = s.get('name', 'Section')
        attrs = [a.get('name', 'col') for a in s.get('attributes', [])[:3]] or ['Name', 'Status']
        ops = s.get('operations', {})
        badges = ''
        if ops.get('create'): badges += '<span class="badge b-c">C</span>'
        if ops.get('update'): badges += '<span class="badge b-u">U</span>'
        if ops.get('delete'): badges += '<span class="badge b-d">D</span>'
        
        headers = ''.join([f'<th>{a}</th>' for a in attrs])
        rows = ''.join([f'<tr>{"".join([f"<td>Data {i+1}</td>" for _ in attrs])}</tr>' for i in range(3)])
        html += f'<div class="card"><h3>{name} {badges}</h3><table><tr>{headers}</tr>{rows}</table></div>'
    return html


def _build_table_content(sections: List, ac: str, tc: str) -> str:
    if not sections:
        return '<div class="section"><div class="section-header">No Data</div></div>'
    
    html = ''
    for s in sections[:2]:
        name = s.get('name', 'Section')
        attrs = [a.get('name', 'col') for a in s.get('attributes', [])[:4]] or ['ID', 'Name', 'Status']
        headers = ''.join([f'<th>{a}</th>' for a in attrs])
        rows = ''.join([f'<tr>{"".join([f"<td>Row {i+1}</td>" for _ in attrs])}</tr>' for i in range(4)])
        html += f'''<div class="section"><div class="section-header">{name}</div>
<div class="toolbar"><button>Add</button><button class="sec">Export</button></div>
<table><tr>{headers}</tr>{rows}</table></div>'''
    return html


def _build_dashboard_widgets(sections: List, r: int, ac: str, tc: str, bg: str) -> str:
    s = sections[0] if sections else {'name': 'Items', 'attributes': []}
    name = s.get('name', 'Recent Items')
    
    rows = ''.join([f'<tr><td>Item {i+1}</td><td><span class="badge b-s">Active</span></td><td>2h ago</td></tr>' for i in range(4)])
    activities = ''.join([f'<div class="activity-item"><div class="dot"></div><div class="activity-text">Activity {i+1}</div><div class="activity-time">{i}h ago</div></div>' for i in range(4)])
    
    return f'''<div class="widgets">
<div class="widget"><h3>{name} <span>View All →</span></h3><table><tr><th>Name</th><th>Status</th><th>Updated</th></tr>{rows}</table></div>
<div class="widget"><h3>Activity <span>View All →</span></h3>{activities}</div>
</div>'''


def _build_list_menu(pages: List, tc: str, ac: str) -> str:
    items = pages[:6] if pages else [{'name': f'Item {i}'} for i in range(5)]
    html = ''
    for i, p in enumerate(items):
        name = p.get('name', f'Item {i+1}')
        active = ' active' if i == 0 else ''
        html += f'<div class="list-item{active}"><div class="list-avatar">{name[0].upper()}</div><div class="list-info"><h4>{name}</h4><p>Updated recently</p></div></div>'
    return html


def _build_detail_content(sections: List, r: int, ac: str, tc: str) -> str:
    s = sections[0] if sections else {'name': 'Details', 'attributes': []}
    attrs = [a.get('name', 'Field') for a in s.get('attributes', [])[:4]] or ['Name', 'Email', 'Status']
    
    fields = ''.join([f'<div class="field"><label>{a}</label><input type="text" value="Sample {a}"></div>' for a in attrs])
    return f'<div class="detail-card"><h3>Information</h3>{fields}</div>'


def _build_wizard_steps(sections: List, ac: str) -> str:
    steps = ['Info', 'Details', 'Review']
    html = ''
    for i, step in enumerate(steps):
        cls = 'active' if i == 0 else ''
        line = '<div class="step-line"></div>' if i > 0 else ''
        html += f'{line}<div class="step {cls}"><div class="step-circle">{i+1}</div><div class="step-label">{step}</div></div>'
    return html


def _build_wizard_content(sections: List, r: int, ac: str, tc: str) -> str:
    s = sections[0] if sections else {'attributes': []}
    attrs = [a.get('name', 'Field') for a in s.get('attributes', [])[:3]] or ['Name', 'Email']
    
    fields = ''.join([f'<div class="form-group"><label>{a}</label><input type="text" placeholder="Enter {a.lower()}"></div>' for a in attrs])
    return fields


def _build_tabs(sections: List, ac: str) -> str:
    tabs = [s.get('name', f'Tab {i+1}') for i, s in enumerate(sections[:3])] or ['Overview', 'Details', 'History']
    html = ''
    for i, t in enumerate(tabs):
        cls = ' active' if i == 0 else ''
        html += f'<button class="tab{cls}">{t}</button>'
    return html


def _build_minimal_content(sections: List, r: int, ac: str, tc: str) -> str:
    """Build content for minimal layout."""
    s = sections[0] if sections else {'name': 'Data', 'attributes': []}
    name = s.get('name', 'Overview')
    attrs = [a.get('name', 'col') for a in s.get('attributes', [])[:4]] or ['Name', 'Value', 'Status']
    
    headers = ''.join([f'<th>{a}</th>' for a in attrs])
    rows = ''.join([f'<tr>{"".join([f"<td>Sample {i+1}</td>" for _ in attrs])}</tr>' for i in range(4)])
    return f'<div class="section-title">{name}</div><table><tr>{headers}</tr>{rows}</table>'
