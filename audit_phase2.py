#!/usr/bin/env python3
"""Phase 2: Hierarchy analysis, tabs, modals, and full report generation"""
import re
import json

with open('/home/developer/mempool.miner/new-design.html', 'r') as f:
    new_design = f.read()
with open('/home/developer/mempool.miner/frontend/index.html', 'r') as f:
    index_html = f.read()
with open('/home/developer/mempool.miner/frontend/game.js', 'r') as f:
    game_js = f.read()

with open('/home/developer/mempool.miner/audit_data.json', 'r') as f:
    data = json.load(f)

# ============================================================
# HIERARCHY ANALYSIS
# ============================================================

def find_element(html, attr_type, value):
    """Find an element by id or class and return its opening tag"""
    pattern = rf'<(\w[\w-]*)\s[^>]*{attr_type}=["\']{re.escape(value)}["\'][^>]*>'
    m = re.search(pattern, html)
    if m:
        return m.group(0)
    return None

def get_parent_chain(html, target_id):
    """Get the parent chain of an element by walking backwards through the HTML"""
    pos = html.find(f'id="{target_id}"')
    if pos == -1:
        return []
    parents = []
    depth = 0
    # Walk backwards to find parent tags
    for i in range(pos, -1, -1):
        ch = html[i]
        if ch == '<':
            # Check if this is a closing tag
            if i + 1 < len(html) and html[i+1] == '/':
                depth -= 1
                if depth < 0:
                    # This is the parent
                    tag_match = re.match(r'</(\w[\w-]*)>', html[i:i+20])
                    if tag_match:
                        parents.append(tag_match.group(1))
                    break
            else:
                depth += 1
    return parents

def get_direct_children(html, parent_id):
    """Get direct children of an element by ID"""
    start = html.find(f'id="{parent_id}"')
    if start == -1:
        return []
    # Find the closing > of the parent tag
    tag_end = html.find('>', start)
    if tag_end == -1:
        return []
    
    # Find the matching closing tag
    parent_tag = re.search(r'<(\w[\w-]*)', html[start:tag_end+1])
    if not parent_tag:
        return []
    tag_name = parent_tag.group(1)
    
    depth = 1
    pos = tag_end + 1
    children = []
    
    while pos < len(html) and depth > 0:
        if html[pos] == '<':
            if html[pos:pos+2] == '</':
                closing = re.match(r'</(\w[\w-]*)>', html[pos:pos+30])
                if closing and closing.group(1) == tag_name:
                    depth -= 1
                    if depth == 0:
                        break
                elif closing:
                    depth -= 1
            elif html[pos:pos+2] != '<!':
                opening = re.match(r'<(\w[\w-]*)', html[pos:pos+30])
                if opening:
                    depth += 1
                    if depth == 2:
                        # This is a direct child
                        child_tag = opening.group(1)
                        child_id_match = re.search(r'id=["\']([^"\']+)["\']', html[pos:pos+200])
                        child_class_match = re.search(r'class=["\']([^"\']+)["\']', html[pos:pos+200])
                        child_info = {'tag': child_tag}
                        if child_id_match:
                            child_info['id'] = child_id_match.group(1)
                        if child_class_match:
                            child_info['class'] = child_class_match.group(1)
                        children.append(child_info)
        pos += 1
    
    return children

def get_nested_structure(html, parent_id, max_depth=3):
    """Get nested structure of children"""
    start = html.find(f'id="{parent_id}"')
    if start == -1:
        return []
    tag_end = html.find('>', start)
    if tag_end == -1:
        return []
    parent_tag = re.search(r'<(\w[\w-]*)', html[start:tag_end+1])
    if not parent_tag:
        return []
    tag_name = parent_tag.group(1)
    
    depth = 1
    pos = tag_end + 1
    children = []
    current_depth = 0
    
    while pos < len(html) and depth > 0:
        if html[pos] == '<':
            if html[pos:pos+2] == '</':
                closing = re.match(r'</(\w[\w-]*)>', html[pos:pos+30])
                if closing:
                    if closing.group(1) == tag_name and depth == 1:
                        break
                    depth -= 1
                    if depth <= current_depth and current_depth > 0:
                        current_depth -= 1
            elif html[pos:pos+2] != '<!':
                opening = re.match(r'<(\w[\w-]*)', html[pos:pos+30])
                if opening:
                    depth += 1
                    current_depth = depth - 1
                    if current_depth <= max_depth:
                        child_tag = opening.group(1)
                        child_id_match = re.search(r'id=["\']([^"\']+)["\']', html[pos:pos+200])
                        child_class_match = re.search(r'class=["\']([^"\']+)["\']', html[pos:pos+200])
                        child_info = {'tag': child_tag, 'depth': current_depth}
                        if child_id_match:
                            child_info['id'] = child_id_match.group(1)
                        if child_class_match:
                            child_info['class'] = child_class_match.group(1)
                        children.append(child_info)
        pos += 1
    
    return children

# Check hierarchy in new-design.html
print("=" * 60)
print("HIERARCHY ANALYSIS - new-design.html")
print("=" * 60)

for key_id in ['mecha-frame', 'hud-header', 'hud-body', 'hud-footer']:
    el = find_element(new_design, 'id', key_id)
    if el:
        print(f"\n[{key_id}]: {el[:120]}")
    else:
        # Check by class
        el = find_element(new_design, 'class', key_id)
        if el:
            print(f"\n[{key_id}] (class): {el[:120]}")
        else:
            print(f"\n[{key_id}]: NOT FOUND")

# Check stage-center and sidebar-right
for key_class in ['stage-center', 'sidebar-right']:
    el = find_element(new_design, 'class', key_class)
    if el:
        print(f"\n[{key_class}] (class): {el[:120]}")
    else:
        print(f"\n[{key_class}]: NOT FOUND")

# Get structure of mecha-frame in new-design
print("\n--- mecha-frame children (new-design) ---")
children = get_nested_structure(new_design, 'mecha-frame', max_depth=2)
for c in children:
    print(f"  {c}")

# Get structure of hud-body in new-design
print("\n--- hud-body children (new-design) ---")
children = get_nested_structure(new_design, 'hud-body', max_depth=2)
for c in children:
    print(f"  {c}")

print("\n" + "=" * 60)
print("HIERARCHY ANALYSIS - index.html")
print("=" * 60)

for key_id in ['mecha-frame', 'hud-header', 'hud-body', 'hud-footer']:
    el = find_element(index_html, 'id', key_id)
    if el:
        print(f"\n[{key_id}]: {el[:120]}")
    else:
        el = find_element(index_html, 'class', key_id)
        if el:
            print(f"\n[{key_id}] (class): {el[:120]}")
        else:
            print(f"\n[{key_id}]: NOT FOUND")

for key_class in ['stage-center', 'sidebar-right']:
    el = find_element(index_html, 'class', key_class)
    if el:
        print(f"\n[{key_class}] (class): {el[:120]}")
    else:
        print(f"\n[{key_class}]: NOT FOUND")

print("\n--- mecha-frame children (index) ---")
children = get_nested_structure(index_html, 'mecha-frame', max_depth=2)
for c in children:
    print(f"  {c}")

print("\n--- hud-body children (index) ---")
children = get_nested_structure(index_html, 'hud-body', max_depth=2)
for c in children:
    print(f"  {c}")

# ============================================================
# TABS ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("TABS ANALYSIS")
print("=" * 60)

for tab_id in ['tab-tx', 'tab-shop', 'tab-rank', 'tab-info']:
    nd_el = find_element(new_design, 'id', tab_id)
    idx_el = find_element(index_html, 'id', tab_id)
    print(f"\n[{tab_id}]:")
    print(f"  new-design: {'FOUND' if nd_el else 'MISSING'} - {nd_el[:100] if nd_el else ''}")
    print(f"  index:      {'FOUND' if idx_el else 'MISSING'} - {idx_el[:100] if idx_el else ''}")

# Check tab-pane containers
for tab_id in ['tab-tx', 'tab-shop', 'tab-rank', 'tab-info']:
    # Find the tab-pane associated with each tab
    tab_section_start = new_design.find(f'id="{tab_id}"')
    if tab_section_start > 0:
        # Look for the next div.tab-pane or similar
        section = new_design[tab_section_start:tab_section_start+500]
        print(f"\n  new-design content after {tab_id}:")
        print(f"    {section[:200]}")

# ============================================================
# MODALS ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("MODALS ANALYSIS")
print("=" * 60)

for modal_id in ['auth-modal', 'result-modal']:
    nd_el = find_element(new_design, 'id', modal_id)
    idx_el = find_element(index_html, 'id', modal_id)
    print(f"\n[{modal_id}]:")
    print(f"  new-design: {'FOUND' if nd_el else 'MISSING'}")
    print(f"  index:      {'FOUND' if idx_el else 'MISSING'}")
    
    # Get modal structure
    for html_src, label in [(new_design, 'new-design'), (index_html, 'index')]:
        start = html_src.find(f'id="{modal_id}"')
        if start > 0:
            end = html_src.find(f'</div>', start + 100)
            if end > 0:
                snippet = html_src[start:end+6]
                print(f"  {label}: {snippet[:200]}")

# Check for extra modals in index
extra_modals = [x for x in data['extra_ids'] if 'modal' in x.lower()]
print(f"\nExtra modals in index.html: {extra_modals}")

# ============================================================
# GAME.JS ID MAPPING
# ============================================================
print("\n" + "=" * 60)
print("GAME.JS ID MAPPING")
print("=" * 60)

js_ids = re.findall(r"getElementById\(['\"]([^'\"]+)['\"]\)", game_js)
js_ids_unique = sorted(set(js_ids))

# IDs in game.js but NOT in new-design
js_not_in_new = sorted(set(js_ids_unique) - set(data['new_ids']))
print(f"\nIDs in game.js but NOT in new-design ({len(js_not_in_new)}): {js_not_in_new}")

# IDs in game.js that ARE in new-design
js_in_new = sorted(set(js_ids_unique) & set(data['new_ids']))
print(f"\nIDs in game.js that ARE in new-design ({len(js_in_new)}): {js_in_new}")

# Check if all 164 game.js IDs are in index.html
js_not_in_index = sorted(set(js_ids_unique) - set(data['index_ids']))
print(f"\nIDs in game.js but NOT in index.html ({len(js_not_in_index)}): {js_not_in_index}")

# ============================================================
# GENERATE REPORT
# ============================================================

report = []
report.append("# Auditoria Completa da Estrutura HTML\n")
report.append("## Resumo Executivo\n")
report.append(f"| Métrica | new-design.html | index.html |")
report.append(f"|---------|-----------------|------------|")
report.append(f"| Linhas | {data['new_design_lines']} | {data['index_lines']} |")
report.append(f"| IDs | {len(data['new_ids'])} | {len(data['index_ids'])} |")
report.append(f"| Classes CSS | {len(data['new_classes'])} | {len(data['index_classes'])} |")
report.append(f"| getElementById (game.js) | - | {len(js_ids_unique)} únicos |")
report.append("")

report.append("## 1. Hierarquia Principal\n")
report.append("### Estrutura esperada (new-design.html)\n")
report.append("```\n")
report.append("mecha-frame\n")
report.append("├── hud-header\n")
report.append("├── hud-body\n")
report.append("│   ├── stage-center\n")
report.append("│   └── sidebar-right\n")
report.append("└── hud-footer\n")
report.append("```\n")

# Check each hierarchy element
hierarchy_elements = {
    'mecha-frame': ('id', 'id'),
    'hud-header': ('id', 'class'),
    'hud-body': ('id', 'class'),
    'hud-footer': ('id', 'class'),
    'stage-center': ('class', 'class'),
    'sidebar-right': ('class', 'class'),
}

report.append("### Verificação de elementos hierárquicos\n")
report.append("| Elemento | new-design | index.html | Status |")
report.append("|----------|------------|------------|--------|")

for elem, (nd_attr, idx_attr) in hierarchy_elements.items():
    nd_found = find_element(new_design, nd_attr, elem) is not None
    idx_found = find_element(index_html, idx_attr, elem) is not None
    status = "✅" if (nd_found and idx_found) else ("❌ FALTA" if not idx_found else "⚠️")
    report.append(f"| `{elem}` | {'✅' if nd_found else '❌'} | {'✅' if idx_found else '❌'} | {status} |")

report.append("")

report.append("## 2. IDs: Comparação\n")
report.append(f"- **IDs no new-design.html**: {len(data['new_ids'])}\n")
report.append(f"- **IDs no index.html**: {len(data['index_ids'])}\n")
report.append(f"- **IDs comuns**: {len(data['common_ids'])}\n")
report.append(f"- **IDs faltando no index.html**: {len(data['missing_ids'])}\n")
report.append(f"- **IDs extras no index.html**: {len(data['extra_ids'])}\n")

report.append("\n### IDs faltando no index.html\n")
for mid in data['missing_ids']:
    report.append(f"- `{mid}`")

report.append("\n### IDs extras no index.html (não existem no new-design)\n")
for eid in data['extra_ids']:
    report.append(f"- `{eid}`")

report.append("")

report.append("## 3. Classes CSS: Comparação\n")
report.append(f"- **Classes no new-design.html**: {len(data['new_classes'])}\n")
report.append(f"- **Classes no index.html**: {len(data['index_classes'])}\n")
report.append(f"- **Classes comuns**: {len(data['common_classes'])}\n")
report.append(f"- **Classes faltando no index.html**: {len(data['missing_classes'])}\n")
report.append(f"- **Classes extras no index.html**: {len(data['extra_classes'])}\n")

report.append("\n### Classes faltando no index.html\n")
for mc in data['missing_classes']:
    report.append(f"- `{mc}`")

report.append("\n### Classes extras no index.html\n")
for ec in data['extra_classes']:
    report.append(f"- `{ec}`")

report.append("")

report.append("## 4. Abas (Tabs)\n")
report.append("| Aba | new-design | index.html | Status |")
report.append("|-----|------------|------------|--------|")

for tab_id in ['tab-tx', 'tab-shop', 'tab-rank', 'tab-info']:
    nd_found = find_element(new_design, 'id', tab_id) is not None
    idx_found = find_element(index_html, 'id', tab_id) is not None
    status = "✅" if (nd_found and idx_found) else "❌"
    report.append(f"| `{tab_id}` | {'✅' if nd_found else '❌'} | {'✅' if idx_found else '❌'} | {status} |")

report.append("")

report.append("## 5. Modais\n")
report.append("| Modal | new-design | index.html | Status |")
report.append("|-------|------------|------------|--------|")

for modal_id in ['auth-modal', 'result-modal']:
    nd_found = find_element(new_design, 'id', modal_id) is not None
    idx_found = find_element(index_html, 'id', modal_id) is not None
    status = "✅" if (nd_found and idx_found) else "❌"
    report.append(f"| `{modal_id}` | {'✅' if nd_found else '❌'} | {'✅' if idx_found else '❌'} | {status} |")

report.append(f"\n### Modais extras no index.html\n")
for em in extra_modals:
    report.append(f"- `{em}`")

report.append("")

report.append("## 6. IDs do game.js (getElementById)\n")
report.append(f"- **Total de chamadas getElementById**: {len(js_ids)}\n")
report.append(f"- **IDs únicos**: {len(js_ids_unique)}\n")
report.append(f"- **IDs presentes no index.html**: {len(set(js_ids_unique) & set(data['index_ids']))}\n")
report.append(f"- **IDs faltando no index.html**: {len(js_not_in_index)}\n")
report.append(f"- **IDs no game.js mas NÃO no new-design**: {len(js_not_in_new)}\n")
report.append(f"- **IDs no game.js que ESTÃO no new-design**: {len(js_in_new)}\n")

if js_not_in_index:
    report.append("\n### IDs do game.js faltando no index.html\n")
    for jid in js_not_in_index:
        report.append(f"- `{jid}`")
else:
    report.append("\n✅ **Todos os 164 IDs do game.js estão presentes no index.html**\n")

report.append("\n### IDs no game.js mas NÃO no new-design (funcionalidades novas)\n")
for jid in js_not_in_new:
    report.append(f"- `{jid}`")

report.append("")

report.append("## 7. Conclusão\n")
report.append("### Resumo de conformidade\n")

issues = []
if data['missing_ids']:
    issues.append(f"- {len(data['missing_ids'])} ID(s) do new-design faltam no index.html")
if data['missing_classes']:
    issues.append(f"- {len(data['missing_classes'])} classe(s) CSS do new-design faltam no index.html")
if js_not_in_index:
    issues.append(f"- {len(js_not_in_index)} ID(s) do game.js faltam no index.html")

if not issues:
    report.append("✅ **index.html contém todos os IDs e classes essenciais do new-design.html**\n")
    report.append("✅ **Todos os 164 IDs do game.js estão presentes no index.html**\n")
else:
    for issue in issues:
        report.append(f"⚠️ {issue}\n")

report.append("\n### Observações\n")
report.append(f"- O index.html tem **{len(data['extra_ids'])} IDs extras** e **{len(data['extra_classes'])} classes extras** em relação ao new-design.html, correspondendo a funcionalidades adicionais implementadas no game.js (achievements, boss battles, decoder, market, staking, seasons, skills, chat, friends, cards, energy, global events, PWA, etc.)\n")
report.append(f"- O index.html é **{data['index_lines']} linhas** vs **{data['new_design_lines']} linhas** do new-design.html\n")
report.append(f"- O new-design.html serve como base de referência visual; o index.html é a versão funcional completa\n")

with open('/home/developer/mempool.miner/audit-html-estrutura.md', 'w') as f:
    f.write('\n'.join(report))

print("\n" + "=" * 60)
print("RELATÓRIO GERADO: audit-html-estrutura.md")
print("=" * 60)
print(f"\nResumo:")
print(f"  - IDs faltando no index: {len(data['missing_ids'])}")
print(f"  - IDs extras no index: {len(data['extra_ids'])}")
print(f"  - Classes faltando: {len(data['missing_classes'])}")
print(f"  - Classes extras: {len(data['extra_classes'])}")
print(f"  - game.js IDs faltando no index: {len(js_not_in_index)}")
print(f"  - game.js IDs não no new-design: {len(js_not_in_new)}")
