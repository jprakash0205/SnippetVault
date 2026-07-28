import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from config import load_config, init_dir, DEFAULT_SNIPPETS_DIR
from routes import vault_bp

# Get the absolute folder directory where run.py lives
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Explicitly map the base folder paths globally
app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, "static"),
    template_folder=os.path.join(BASE_DIR, "templates")
)

# --- NEW: LOGGING CONFIGURATION ---
# Define the log path using your BASE_DIR
log_path = os.path.join(BASE_DIR, "app_errors.log")

# Setup a rotating log handler (1MB max size per file, keeps 3 backups)
log_handler = RotatingFileHandler(log_path, maxBytes=1000000, backupCount=3)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
log_handler.setFormatter(log_formatter)

# Capture WARNING, ERROR, and CRITICAL messages
log_handler.setLevel(logging.WARNING)

# Inject the logger into both Flask and the root system
app.logger.addHandler(log_handler)
logging.getLogger().addHandler(log_handler)
# ----------------------------------

# Register our Blueprint routing layer
app.register_blueprint(vault_bp, url_prefix="/")

# Inject custom Jinja template filters safely
@app.template_filter('js_escaped')
def js_escaped(text):
    if not text:
        return ""
    return (text
            .replace('\\', '\\\\')
            .replace('`', '\\`')
            .replace('$', '\\$')
            .replace('"', '\\"')
            .replace("'", "\\'"))

if __name__ == "__main__":
    initial_config = load_config()
    init_dir(initial_config.get("snippets_dir", DEFAULT_SNIPPETS_DIR))
    
    # Run server locally
    # Note: When running via Task Scheduler, it is best to leave debug=False 
    # to avoid the app auto-restarting in the background.
    app.run(debug=False, host="0.0.0.0", port=5000)
