import json

with open('audit_reconciliation.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for cname, cdata in data.items():
    print(f'=== {cname} ===')
    can_folders = cdata.get('canonical_folders', {})
    mismatches = 0
    for doc in cdata.get('doc_details', []):
        sub = doc['subcategory']
        can_fid = can_folders.get(sub)
        parents = doc['drive_parents']
        in_canonical = can_fid in parents if can_fid else False
        if not in_canonical:
            print(f"  Doc ID {doc['id']} (Article {doc['article_id']}, {sub}): Drive parents={parents}, Canonical folder={can_fid}")
            mismatches += 1
    if mismatches == 0:
        print(f"  All {len(cdata.get('doc_details', []))} documents 100% matched to canonical subcategory folders!")
    else:
        print(f"  Total with non-canonical parents: {mismatches}")
