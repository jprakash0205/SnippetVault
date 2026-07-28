import os
import re
import yaml
import markdown
import uuid
from datetime import datetime
from markdown.extensions.codehilite import CodeHiliteExtension

def safe_filename(title, category):
    clean_title = re.sub(r'[\\/*?:"<>| ]', '_', title.strip())
    clean_cat = re.sub(r'[\\/*?:"<>| ]', '_', category.strip())
    return f"{clean_cat}___{clean_title}.md"

def parse_filename(filename):
    if filename.endswith(".md"):
        name_part = filename[:-3]
        if "___" in name_part:
            category, title = name_part.split("___", 1)
            return category.replace('_', ' '), title.replace('_', ' ')
        return "General", name_part.replace('_', ' ')
    return "General", filename

def detect_content_type(title, content, category=""):
    """Detects code type based on title extensions, content markers, or assigned category."""
    combined = (title + " " + content + " " + category).lower()
    if 'python' in combined or any(ext in title.lower() for ext in ['.py', '.wsgi']) or 'import ' in content or 'def ' in content:
        return 'python'
    if 'javascript' in combined or 'js' in combined or any(ext in title.lower() for ext in ['.js', '.ts']) or 'const ' in content or 'function ' in content:
        return 'javascript'
    if 'html' in combined or '.html' in title.lower() or '</div>' in content or '<html' in content:
        return 'html'
    if 'css' in combined or '.css' in title.lower() or ('{' in content and ';' in content):
        return 'css'
    if 'json' in combined or 'yaml' in combined or any(ext in title.lower() for ext in ['.json', '.yml', '.yaml']):
        return 'json'
    if 'terminal' in combined or 'bash' in combined or 'sql' in combined or '$ ' in content:
        return 'bash'
    return 'markdown'

def read_snippet_file(filepath, filename):
    category, title = parse_filename(filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception:
        return None

    stat = os.stat(filepath)
    created_dt = datetime.fromtimestamp(stat.st_ctime).isoformat()
    modified_dt = datetime.fromtimestamp(stat.st_mtime).isoformat()
    
    meta = {
        "pinned": False,
        "created": created_dt,
        "modified": modified_dt,
        "category": category,
        "title": title
    }
    
    raw_content = text

    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            try:
                yaml_meta = yaml.safe_load(parts[1])
                if isinstance(yaml_meta, dict):
                    meta.update(yaml_meta)
                raw_content = parts[2].strip()
            except Exception:
                pass

    active_type = detect_content_type(meta["title"], raw_content, meta["category"])

    guess_lang_name = active_type
    if guess_lang_name == 'markdown':
        guess_lang_name = 'text'
    
    # FIXED: Normalise spacing by replacing explicit double newlines (\n\n or \r\n\r\n) with a clean single break
    clean_raw = raw_content.strip()
    clean_raw = re.sub(r'\r\n', '\n', clean_raw)
    clean_raw = re.sub(r'\n{2,}', '\n', clean_raw) # Compresses accidental triple gaps down to one single clean jump
    
    compiler_content = clean_raw
    if active_type != 'markdown' and not clean_raw.startswith('```') and not '```' in clean_raw:
        compiler_content = f"```{guess_lang_name}\n{clean_raw}\n```"
    
    custom_configs = {
        'codehilite': {
            'guess_lang': False,
            'css_class': 'codehilite',
            'noclasses': False
        }
    }
    
    rendered_html = markdown.markdown(
        compiler_content, 
        extensions=['fenced_code', 'codehilite', 'tables'],
        extension_configs=custom_configs
    )
    
    char_count = len(raw_content)
    word_count = len(raw_content.split())

    return {
        "filename": filename,
        "title": meta["title"],
        "category": meta["category"],
        "content": raw_content,
        "html": rendered_html,
        "pinned": meta.get("pinned", False),
        "created": meta.get("created", created_dt),
        "modified": meta.get("modified", modified_dt),
        "content_type": active_type,
        "char_count": char_count,
        "word_count": word_count
    }
