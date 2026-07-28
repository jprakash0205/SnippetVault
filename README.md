### Logs
1. `app_errors.log` (from Python): Will log specific code errors, broken routes, or failed database links while the app is actively running.
2. `background_terminal.log` (from the .bat file): Will catch crashes that happen before Python can even boot up your app (such as missing external modules or syntax errors).