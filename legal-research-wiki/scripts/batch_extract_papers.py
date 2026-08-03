import pymupdf, os, hashlib, json, sys

papers_dir = sys.argv[1] if len(sys.argv) > 1 else "."
results = []

for fname in sorted(os.listdir(papers_dir)):
    if not fname.endswith('.pdf'):
        continue
    path = os.path.join(papers_dir, fname)

    with open(path, 'rb') as f:
        sha = hashlib.sha256(f.read()).hexdigest()

    doc = pymupdf.open(path)
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    text = "\n".join(text_parts)

    txt_path = path.replace('.pdf', '.txt')
    with open(txt_path, 'w') as f:
        f.write(text)

    results.append({
        "file": fname,
        "sha256": sha,
        "pages": len(text_parts),
        "chars": len(text)
    })

print(json.dumps(results, ensure_ascii=False))
