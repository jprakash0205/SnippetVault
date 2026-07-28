import os
import re
import math
import json
import yaml
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for
import markdown

app = Flask(__name__)

CONFIG_FILE = "app_config.json"
DEFAULT_SNIPPETS_DIR = str(Path.home() / "snippets")

DEFAULT_CONFIG = {
    "snippets_dir": DEFAULT_SNIPPETS_DIR,
    "per_page": 6
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

def init_dir(directory):
    try:
        os.makedirs(directory, exist_ok=True)
    except Exception:
        pass

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

def detect_content_type(title, content):
    """Detects type/language based on title extensions or content markers."""
    combined = (title + " " + content).lower()
    if any(ext in title.lower() for ext in ['.py', '.wsgi']) or 'import ' in content or 'def ' in content:
        return 'python'
    if any(ext in title.lower() for ext in ['.js', '.ts']) or 'const ' in content or 'function ' in content:
        return 'javascript'
    if '.html' in title.lower() or '</div>' in content or '<html' in content:
        return 'html'
    if '.css' in title.lower() or '{' in content and ';' in content:
        return 'css'
    if any(ext in title.lower() for ext in ['.json', '.yml', '.yaml']):
        return 'json'
    if any(ext in title.lower() for ext in ['.sh', '.bash']) or '$ ' in content:
        return 'bash'
    return 'markdown'

def read_snippet_file(filepath, filename):
    """Reads file, extracts Front Matter metadata, and parses Markdown content."""
    category, title = parse_filename(filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception:
        return None

    # Default metadata
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
    # Parse YAML front matter if present
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

    rendered_html = markdown.markdown(raw_content, extensions=['fenced_code', 'codehilite'])
    content_type = detect_content_type(meta["title"], raw_content)

    return {
        "filename": filename,
        "title": meta["title"],
        "category": meta["category"],
        "content": raw_content,
        "html": rendered_html,
        "pinned": meta.get("pinned", False),
        "created": meta.get("created", created_dt),
        "modified": meta.get("modified", modified_dt),
        "content_type": content_type
    }

@app.route("/")
def index():
    config = load_config()
    snippets_dir = config.get("snippets_dir", DEFAULT_SNIPPETS_DIR)
    per_page = int(config.get("per_page", 6))
    
    init_dir(snippets_dir)
    absolute_folder_path = os.path.abspath(snippets_dir)
    
    # Filters
    search_query = request.args.get("search", "").lower().strip()
    filter_date = request.args.get("date_filter", "")  # today, week, month, year
    filter_cat = request.args.get("category_filter", "").lower().strip()
    
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        page = 1
        
    all_snippets = []
    categories_set = set()

    if os.path.exists(snippets_dir):
        for filename in os.listdir(snippets_dir):
            if filename.endswith(".md"):
                filepath = os.path.join(snippets_dir, filename)
                snippet_data = read_snippet_file(filepath, filename)
                if not snippet_data:
                    continue
                
                categories_set.add(snippet_data["category"])
                
                # Apply Text Search Filter
                if search_query and not (search_query in snippet_data["title"].lower() or 
                                         search_query in snippet_data["content"].lower() or 
                                         search_query in snippet_data["category"].lower()):
                    continue
                
                # Apply Category Filter
                if filter_cat and snippet_data["category"].lower() != filter_cat:
                    continue
                    
                # Apply Date Filter (Based on Modified Date)
                if filter_date:
                    try:
                        mod_dt = datetime.fromisoformat(snippet_data["modified"])
                        now = datetime.now()
                        delta_days = (now - mod_dt).days
                        if filter_date == "today" and delta_days > 0: continue
                        elif filter_date == "week" and delta_days > 7: continue
                        elif filter_date == "month" and delta_days > 30: continue
                        elif filter_date == "year" and delta_days > 365: continue
                    except Exception:
                        pass

                all_snippets.append(snippet_data)
                    
    # Sort Rule: Pinned first, then sorted by Title alphabetically
    all_snippets.sort(key=lambda x: (not x["pinned"], x["title"].lower()))
    
    total_items = len(all_snippets)
    total_pages = math.ceil(total_items / per_page) or 1
    page = max(1, min(page, total_pages))
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_snippets = all_snippets[start_idx:end_idx]
                    
    return render_template(
        "list.html", 
        snippets=paginated_snippets, 
        categories=sorted(list(categories_set)),
        q=search_query, 
        date_filter=filter_date,
        category_filter=filter_cat,
        folder_path=absolute_folder_path,
        page=page,
        total_pages=total_pages,
        per_page=per_page,
        raw_path_value=snippets_dir
    )

@app.route("/entry")
@app.route("/entry/edit/<filename>")
def entry_page(filename=None):
    config = load_config()
    snippets_dir = config.get("snippets_dir", DEFAULT_SNIPPETS_DIR)
    
    snippet = None
    if filename:
        filepath = os.path.join(snippets_dir, filename)
        if os.path.exists(filepath):
            snippet = read_snippet_file(filepath, filename)
            
    return render_template("entry.html", snippet=snippet)

@app.route("/save", methods=["POST"])
def save_snippet():
    config = load_config()
    snippets_dir = config.get("snippets_dir", DEFAULT_SNIPPETS_DIR)
    init_dir(snippets_dir)
    
    old_filename = request.form.get("old_filename")
    title = request.form.get("title").strip()
    content = request.form.get("content").strip()
    category = request.form.get("category", "General").strip()
    pinned = request.form.get("pinned") == "true"
    
    created_time = request.form.get("created_time") or datetime.now().isoformat()
    modified_time = datetime.now().isoformat()
    
    if title and content:
        if old_filename:
            old_filepath = os.path.join(snippets_dir, old_filename)
            if os.path.exists(old_filepath):
                os.remove(old_filepath)
                
        filename = safe_filename(title, category)
        filepath = os.path.join(snippets_dir, filename)
        
        # Build YAML Front Matter block
        meta_block = {
            "title": title,
            "category": category,
            "pinned": pinned,
            "created": created_time,
            "modified": modified_time
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"---\n{yaml.dump(meta_block)}---\n\n{content}")
            
    return redirect(url_for("index"))

@app.route("/pin/<filename>")
def toggle_pin(filename):
    config = load_config()
    snippets_dir = config.get("snippets_dir", DEFAULT_SNIPPETS_DIR)
    filepath = os.path.join(snippets_dir, filename)
    
    if os.path.exists(filepath):
        snippet = read_snippet_file(filepath, filename)
        if snippet:
            meta_block = {
                "title": snippet["title"],
                "category": snippet["category"],
                "pinned": not snippet["pinned"],
                "created": snippet["created"],
                "modified": snippet["modified"]
            }
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"---\n{yaml.dump(meta_block)}---\n\n{snippet['content']}")
                
    return redirect(url_for("index"))

@app.route("/delete/<filename>")
def delete_snippet(filename):
    config = load_config()
    snippets_dir = config.get("snippets_dir", DEFAULT_SNIPPETS_DIR)
    
    if not filename.endswith(".md") or "/" in filename or "\\" in filename:
        return "Invalid payload", 400
        
    filepath = os.path.join(snippets_dir, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    
    return redirect(url_for("index"))

@app.route("/admin")
def admin_page():
    config = load_config()
    return render_template(
        "admin.html",
        raw_path_value=config.get("snippets_dir", DEFAULT_SNIPPETS_DIR),
        per_page=int(config.get("per_page", 6))
        )

@app.route("/save-config", methods=["POST"])
def update_config():
    new_path = request.form.get("snippets_dir", "").strip()
    
    try:
        new_per_page = int(request.form.get("per_page", 6))
    except ValueError:
        new_per_page = 6
        
    if new_path:
        save_config({"snippets_dir": new_path, "per_page": new_per_page})
        init_dir(new_path)
        
    return redirect(url_for("index"))

@app.template_filter('js_escaped')
def js_escaped(text):
    if not text:
        return ""
    return (text
            .replace('\\', '\\\\')  # Escapes literal backslashes
            .replace('`', '\\`')    # Escapes backticks (useful for JS template literals)
            .replace('$', '\\$')    # Escapes dollar signs
            .replace('"', '\\"')    # Escapes double quotes
            .replace("'", "\\'"))   # Escapes single quotes

if __name__ == "__main__":
    initial_config = load_config()
    init_dir(initial_config.get("snippets_dir", DEFAULT_SNIPPETS_DIR))
    app.run(debug=True, port=5000)