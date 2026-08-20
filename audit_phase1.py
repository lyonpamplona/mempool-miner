#!/usr/bin/env python3
"""Phase 1: Extract all structural data from both HTML files and game.js"""
import re
import json

# Read files
with open('/home/developer/mempool.miner/new-design.html', 'r') as f:
    new_design = f.read()
with open('/home/developer/mempool.miner/frontend/index.html', 'r') as f:
    index_html = f.read()
with open('/home/developer/mempool.miner/frontend/game.js', 'r') as f:
    game_js = f.read()

print(f"=== FILE SIZES ===")
print(f"new-design.html: {len(new_design)} chars, {new_design.count(chr(10))} lines")
print(f"index.html: {len(index_html)} chars, {index_html.count(chr(10))} lines")
print(f"game.js: {len(game_js)} chars, {game_js.count(chr(10))} lines")

# Extract all IDs from HTML files
def extract_ids(html):
    ids = set()
    for m in re.finditer(r'''id=["']([^"']+)["']''', html):
        ids.add(m.group(1))
    return sorted(ids)

# Extract all classes from HTML files
def extract_classes(html):
    classes = set()
    for m in re.finditer(r'''class=["']([^"']+)["']''', html):
        for c in m.group(1).split():
            classes.add(c)
    return sorted(classes)

# Extract all tag names with their attributes
def extract_tags(html):
    tags = []
    for m in re.finditer(r'<([a-zA-Z][a-zA-Z0-9-]*)(\s[^>]*)?(\s*/>)?', html):
        tag_name = m.group(1)
        attrs_str = m.group(2) or ''
        tag_id = re.search(r'''id=["']([^"']+)["']''', attrs_str)
        tag_class = re.search(r'''class=["']([^"']+)["']''', attrs_str)
        tags.append({
            'tag': tag_name,
            'id': tag_id.group(1) if tag_id else None,
            'class': tag_class.group(1) if tag_class else None,
            'attrs': attrs_str.strip()
        })
    return tags

new_ids = extract_ids(new_design)
index_ids = extract_ids(index_html)
new_classes = extract_classes(new_design)
index_classes = extract_classes(index_html)

print(f"\n=== IDS ===")
print(f"new-design.html IDs ({len(new_ids)}): {new_ids}")
print(f"index.html IDs ({len(index_ids)}): {index_ids}")

print(f"\n=== CLASSES ===")
print(f"new-design.html classes ({len(new_classes)}): {new_classes}")
print(f"index.html classes ({len(index_classes)}): {index_classes}")

# IDs in new-design but NOT in index
missing_ids = sorted(set(new_ids) - set(index_ids))
# IDs in index but NOT in new-design
extra_ids = sorted(set(index_ids) - set(new_ids))
# Common IDs
common_ids = sorted(set(new_ids) & set(index_ids))

print(f"\n=== ID COMPARISON ===")
print(f"Common IDs ({len(common_ids)}): {common_ids}")
print(f"Missing in index ({len(missing_ids)}): {missing_ids}")
print(f"Extra in index ({len(extra_ids)}): {extra_ids}")

# Classes comparison
missing_classes = sorted(set(new_classes) - set(index_classes))
extra_classes = sorted(set(index_classes) - set(new_classes))
common_classes = sorted(set(new_classes) & set(index_classes))

print(f"\n=== CLASS COMPARISON ===")
print(f"Common classes ({len(common_classes)}): {common_classes}")
print(f"Missing in index ({len(missing_classes)}): {missing_classes}")
print(f"Extra in index ({len(extra_classes)}): {extra_classes}")

# Extract IDs used in game.js via getElementById
js_ids = re.findall(r"getElementById\(['\"]([^'\"]+)['\"]\)", game_js)
js_ids_unique = sorted(set(js_ids))
print(f"\n=== GAME.JS getElementById ===")
print(f"Total calls: {len(js_ids)}")
print(f"Unique IDs ({len(js_ids_unique)}): {js_ids_unique}")

# IDs in game.js but not in index.html
js_missing = sorted(set(js_ids_unique) - set(index_ids))
print(f"\nIDs in game.js but MISSING from index.html ({len(js_missing)}): {js_missing}")

# IDs in game.js that ARE in index.html
js_present = sorted(set(js_ids_unique) & set(index_ids))
print(f"\nIDs in game.js that ARE in index.html ({len(js_present)}): {js_present}")

# Save data for phase 2
data = {
    'new_ids': new_ids,
    'index_ids': index_ids,
    'new_classes': new_classes,
    'index_classes': index_classes,
    'missing_ids': missing_ids,
    'extra_ids': extra_ids,
    'common_ids': common_ids,
    'missing_classes': missing_classes,
    'extra_classes': extra_classes,
    'common_classes': common_classes,
    'js_ids': js_ids,
    'js_ids_unique': js_ids_unique,
    'js_missing': js_missing,
    'js_present': js_present,
    'new_design_lines': new_design.count('\n'),
    'index_lines': index_html.count('\n'),
    'game_js_lines': game_js.count('\n'),
}

with open('/home/developer/mempool.miner/audit_data.json', 'w') as f:
    json.dump(data, f, indent=2)
print("\nData saved to audit_data.json")
