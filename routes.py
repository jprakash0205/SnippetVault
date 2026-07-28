import os
import re
import math
import yaml
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, Response
from config import load_config, save_config, init_dir, DEFAULT_SNIPPETS_DIR
from helpers import read_snippet_file, safe_filename

# Open routes.py and update your instantiation statement:
vault_bp = Blueprint('vault', __name__)

@vault_bp.route("/")
def index():
    config = load_config()
    snippets_dir = config.get("snippets_dir", DEFAULT_SNIPPETS_DIR)
    per_page = int(config.get("per_page", 6))
    
    init_dir(snippets_dir)
    absolute_folder_path = os.path.abspath(snippets_dir)
    
    # Active Search Filter Dashboard Parameters
    search_query = request.args.get("search", "").lower().strip()
    filter_cat = request.args.get("category_filter", "").lower().strip()
    
    # NEW: Fetch explicit start and end date range selections
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    
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
                
                if search_query and not (search_query in snippet_data["title"].lower() or 
                                         search_query in snippet_data["content"].lower() or 
                                         search_query in snippet_data["category"].lower()):
                    continue
                
                if filter_cat and snippet_data["category"].lower() != filter_cat:
                    continue
                    
                # NEW: Clean calendar date range query computation
                if snippet_data.get("modified"):
                    # Extract only the YYYY-MM-DD segment from the ISO timestamp string
                    mod_day = snippet_data["modified"][:10]
                    if start_date and mod_day < start_date:
                        continue
                    if end_date and mod_day > end_date:
                        continue

                all_snippets.append(snippet_data)

                    
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
        category_filter=filter_cat,
        start_date=start_date,
        end_date=end_date,
        folder_path=absolute_folder_path,
        page=page,
        total_pages=total_pages,
        per_page=per_page,
        raw_path_value=snippets_dir
    )

@vault_bp.route("/entry")
@vault_bp.route("/entry/edit/<filename>")
def entry_page(filename=None):
    config = load_config()
    snippets_dir = config.get("snippets_dir", DEFAULT_SNIPPETS_DIR)
    
    snippet = None
    if filename:
        filepath = os.path.join(snippets_dir, filename)
        if os.path.exists(filepath):
            snippet = read_snippet_file(filepath, filename)
            
            # FIXED: Strip duplicate/additional spacing before feeding it to CodeMirror
            if snippet and snippet.get("content"):
                clean_content = snippet["content"].strip()
                # Convert Windows carriage returns (\r\n) cleanly to standard newlines (\n)
                clean_content = re.sub(r'\r\n', '\n', clean_content)
                # Compress accidental double/triple empty line gaps back down to a single line break
                clean_content = re.sub(r'\n{2,}', '\n', clean_content)
                
                # Apply the cleaned text payload back to the editor dictionary context parameter
                snippet["content"] = clean_content
            
    return render_template("entry.html", snippet=snippet)


@vault_bp.route("/save", methods=["POST"])
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
        
        meta_block = {
            "title": title,
            "category": category,
            "pinned": pinned,
            "created": created_time,
            "modified": modified_time
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"---\n{yaml.dump(meta_block)}---\n\n{content}")
            
    return redirect(url_for("vault.index"))

@vault_bp.route("/pin/<filename>")
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
                
    return redirect(url_for("vault.index"))

@vault_bp.route("/delete/<filename>")
def delete_snippet(filename):
    config = load_config()
    snippets_dir = config.get("snippets_dir", DEFAULT_SNIPPETS_DIR)
    
    if not filename.endswith(".md") or "/" in filename or "\\" in filename:
        return "Invalid payload", 400
        
    filepath = os.path.join(snippets_dir, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    return redirect(url_for("vault.index"))

@vault_bp.route("/admin")
def admin_page():
    config = load_config()
    return render_template(
        "admin.html", 
        raw_path_value=config.get("snippets_dir", DEFAULT_SNIPPETS_DIR), 
        per_page=int(config.get("per_page", 6))
    )

@vault_bp.route("/save-config", methods=["POST"])
def update_config():
    new_path = request.form.get("snippets_dir", "").strip()
    try:
        new_per_page = int(request.form.get("per_page", 6))
    except ValueError:
        new_per_page = 6
        
    if new_path:
        save_config({"snippets_dir": new_path, "per_page": new_per_page})
        init_dir(new_path)
    return redirect(url_for("vault.index"))

@vault_bp.route('/favicon.ico')
def favicon():
    svg_data = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" fill="none">
        <!-- Padlock Shackle / Vault Arc -->
        <path d="M9 14V9a7 7 0 1 1 14 0v5" stroke="#3b82f6" stroke-width="2.5" stroke-linecap="round"/>
        
        <!-- Main Vault Body -->
        <rect x="4" y="13" width="24" height="16" rx="4" fill="#1e293b" stroke="#3b82f6" stroke-width="2.5"/>
        
        <!-- Left Curly Brace { -->
        <path d="M12 17c-1 0-2 1-2 2v1c0 1-1 1-1 1s1 0 1 1v1c0 1 1 2 2 2" stroke="#f8fafc" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
        
        <!-- Right Curly Brace } -->
        <path d="M20 17c1 0 2 1 2 2v1c0 1 1 1 1 1s-1 0-1 1v1c0 1-1 2-2 2" stroke="#f8fafc" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>"""
    return Response(svg_data, mimetype='image/svg+xml')
