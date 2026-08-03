#!/usr/bin/env python3
"""
Clean PDF extraction artifacts from wiki entity pages.

Usage:
    python3 clean_pdf_artifacts.py /path/to/wiki/entities [file1.md file2.md ...]

If no specific files given, scans ALL .md files in the directory.
Reports issues found, then fixes them in-place.
"""
import os, re, sys

def clean_pdf_artifacts(text):
    """Remove PDF extraction artifacts from wiki page content."""
    
    # 1. Remove full-width bracket artifacts
    text = text.replace('］', '').replace('［', '')
    text = text.replace('】', '').replace('【', '')
    
    # 2. Fix keywords section - remove newlines, normalize
    kw_pattern = r'(## 关键词\n\n)(.*?)(\n\n##)'
    kw_match = re.search(kw_pattern, text, re.DOTALL)
    if kw_match:
        kw_content = kw_match.group(2).replace('\n', '').strip().strip(';；')
        text = text[:kw_match.start()] + kw_match.group(1) + kw_content + kw_match.group(3) + text[kw_match.end():]
    
    # 3. Fix abstract - join broken lines (preserve paragraph breaks)
    for section_name in ['摘要', '主要结论']:
        pattern = rf'(## {section_name}\n\n)(.*?)(\n\n##)'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            content = match.group(2)
            content = re.sub(r'([^\n])\n([^\n])', r'\1\2', content)
            text = text[:match.start()] + match.group(1) + content + match.group(3) + text[match.end():]
    
    # 4. Fix key arguments - join lines within paragraphs
    args_pattern = r'(## 核心论点\n\n)(.*?)(\n\n##)'
    args_match = re.search(args_pattern, text, re.DOTALL)
    if args_match:
        args_content = args_match.group(2)
        paragraphs = args_content.split('\n\n')
        fixed = [re.sub(r'([^\n])\n([^\n])', r'\1\2', p) for p in paragraphs]
        args_content = '\n\n'.join(fixed)
        text = text[:args_match.start()] + args_match.group(1) + args_content + args_match.group(3) + text[args_match.end():]
    
    return text


def scan_for_issues(filepath):
    """Check a single file for PDF artifacts."""
    with open(filepath) as f:
        content = f.read()
    issues = []
    if '］' in content or '［' in content: issues.append("PDF方括号残留")
    if 'Vo1.' in content: issues.append("OCR错误(Vo1.)")
    
    kw_match = re.search(r'## 关键词\n\n(.*?)\n\n##', content, re.DOTALL)
    if kw_match:
        kw = kw_match.group(1).strip()
        if '\n' in kw or '］' in kw or '【' in kw: issues.append("关键词格式异常")
    
    for section in ['摘要', '主要结论']:
        pattern = rf'## {section}\n\n(.*?)\n\n##'
        m = re.search(pattern, content, re.DOTALL)
        if m and re.search(r'[，；。]\n[^\n]', m.group(1)):
            issues.append(f"{section}PDF换行残留")
    
    return issues


def main():
    if len(sys.argv) < 2:
        print("Usage: clean_pdf_artifacts.py <entities_dir> [file1.md ...]")
        sys.exit(1)
    
    entities_dir = sys.argv[1]
    specific_files = sys.argv[2:] if len(sys.argv) > 2 else None
    
    if specific_files:
        files = specific_files
    else:
        files = sorted([f for f in os.listdir(entities_dir) if f.endswith('.md')])
    
    fixed_count = 0
    for fname in files:
        path = os.path.join(entities_dir, fname)
        if not os.path.exists(path):
            print(f"  ⏭️ {fname} (not found)")
            continue
        
        issues = scan_for_issues(path)
        if not issues:
            continue
        
        with open(path) as f:
            original = f.read()
        cleaned = clean_pdf_artifacts(original)
        
        if cleaned != original:
            with open(path, 'w') as f:
                f.write(cleaned)
            print(f"✅ {fname}: fixed {', '.join(issues)}")
            fixed_count += 1
        else:
            print(f"⚠️ {fname}: issues detected but no changes made: {issues}")
    
    # Final verification
    remaining = 0
    for fname in files:
        path = os.path.join(entities_dir, fname)
        if os.path.exists(path) and scan_for_issues(path):
            remaining += 1
    
    print(f"\nFixed: {fixed_count} files | Remaining issues: {remaining}")


if __name__ == '__main__':
    main()
