#!/usr/bin/env python3
"""
Append a dynamically generated nav to docs/mkdocs-override.yml.

Reads the upstream nav from docs/mkdocs.yml (untouched by overlays),
picks the sections we publish, fixes paths flattened by the build,
appends the KDocs section, and writes nav YAML to the end of the
INHERIT-based override config.
"""
import sys
import yaml

# Custom loader: silently handles !ENV and !!python/name: tags
class PermissiveLoader(yaml.SafeLoader):
    pass

def _unknown(loader, tag_suffix, node):
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node, deep=True)
    return loader.construct_mapping(node, deep=True)

PermissiveLoader.add_multi_constructor('', _unknown)

# Read upstream nav directly (INHERIT overlay leaves mkdocs.yml untouched)
with open('docs/mkdocs.yml') as f:
    upstream = yaml.load(f, Loader=PermissiveLoader)

KEEP = {'Home', 'Getting Started', 'Developers', 'Service Engineers', 'Contributors'}
STRIP = {'About', 'Roadmap', 'Blog', 'Community'}

doc_nav = []
for item in upstream.get('nav', []):
    if isinstance(item, str):
        doc_nav.append(item)
    elif isinstance(item, dict):
        key = next(iter(item))
        if key in KEEP:
            doc_nav.append(item)
        elif key not in STRIP:
            print(f"patch-mkdocs.py: ERROR — unknown upstream nav section '{key}'; add it to KEEP or STRIP", file=sys.stderr)
            sys.exit(1)

if not doc_nav:
    print("patch-mkdocs.py: ERROR — no matching nav sections found in upstream nav", file=sys.stderr)
    sys.exit(1)

# Fix paths to match the flatten step:
#   docs/developers/  -> developers/
#   docs/service_engineers/ -> service_engineers/
#   docs/contributors/ -> contributors/
FIXES = {
    'docs/developers/': 'developers/',
    'docs/service_engineers/': 'service_engineers/',
    'docs/contributors/': 'contributors/',
}

def fix_path(s):
    for old, new in FIXES.items():
        s = s.replace(old, new)
    return s

def fix_nav(items):
    out = []
    for item in items:
        if isinstance(item, str):
            out.append(fix_path(item))
        elif isinstance(item, dict):
            out.append({
                k: fix_nav(v) if isinstance(v, list) else fix_path(v) if isinstance(v, str) else v
                for k, v in item.items()
            })
    return out

nav = fix_nav(doc_nav)

nav_yaml = yaml.dump({'nav': nav}, default_flow_style=False, allow_unicode=True)

with open('docs/mkdocs-override.yml', 'a') as f:
    f.write('\n')
    f.write(nav_yaml)

print(f"patch-mkdocs.py: nav generated ({len(nav)} top-level sections)")
