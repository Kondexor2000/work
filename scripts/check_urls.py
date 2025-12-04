import re
from pathlib import Path

workspace = Path(__file__).resolve().parent.parent

def find_template_urls():
    tpl_dir = workspace / 'templates'
    pattern = re.compile(r"\{%\s*url\s+['\"]([^'\"]+)['\"]")
    names = {}
    for p in tpl_dir.rglob('*.html'):
        try:
            text = p.read_text(encoding='utf-8')
        except Exception:
            continue
        for m in pattern.finditer(text):
            name = m.group(1)
            names.setdefault(name, set()).add(str(p.relative_to(workspace)))
    return names


def find_defined_urls():
    pattern = re.compile(r"name\s*=\s*['\"]([^'\"]+)['\"]")
    names = set()
    for p in workspace.rglob('*.py'):
        if p.name.startswith('urls') or 'urls' in str(p.parent).lower() or 'urls' in p.name:
            try:
                text = p.read_text(encoding='utf-8')
            except Exception:
                continue
            for m in pattern.finditer(text):
                names.add(m.group(1))
    return names


tpl = find_template_urls()
defined = find_defined_urls()

all_tpl_names = set(tpl.keys())

missing = set()
for name in all_tpl_names:
    if ':' in name:
        # if namespaced, check the base name as well
        base = name.split(':', 1)[1]
        if name not in defined and base not in defined:
            missing.add(name)
    else:
        if name not in defined:
            missing.add(name)

print('Total template URL usages:', sum(len(v) for v in tpl.values()))
print('Unique template URL names:', len(all_tpl_names))
print('Defined URL names found in code:', len(defined))
print('\n--- Missing URL names (used in templates but not defined) ---')
if not missing:
    print('None — wszystkie używane nazwy URL występują w plikach `urls.py` (lub są namespacowane).')
else:
    for name in sorted(missing):
        locations = ', '.join(sorted(tpl[name]))
        print(f"- {name}: {locations}")

print('\n--- Quick lists ---')
print('\nTemplate-only names:')
print('\n'.join(sorted(all_tpl_names)))

print('\nDefined names:')
print('\n'.join(sorted(defined)))
