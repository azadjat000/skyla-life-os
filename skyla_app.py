import os
import subprocess
import time
import urllib.request

import webview


APP_DIR = os.path.dirname(os.path.abspath(__file__))
URL = "http://127.0.0.1:5000"
ICON = os.path.join(APP_DIR, "app", "static", "skyla-icon.png")
SPLASH = os.path.join(APP_DIR, "skyla-splash.html")


def server_running():
    try:
        urllib.request.urlopen(URL, timeout=1)
        return True
    except Exception:
        return False


def start_server():
    if server_running():
        return

    log_path = os.path.join(APP_DIR, "skyla-server.log")

    with open(log_path, "a") as log:
        subprocess.Popen(
            [
                os.path.join(APP_DIR, ".venv", "bin", "python"),
                os.path.join(APP_DIR, "run.py"),
            ],
            cwd=APP_DIR,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )


def wait_for_server():
    for _ in range(30):
        if server_running():
            return True
        time.sleep(1)
    return False


def create_splash():
    icon_uri = "file://" + ICON

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Skyla Life OS</title>

<style>
* {{
    box-sizing: border-box;
}}

html, body {{
    margin: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
}}

body {{
    display: flex;
    align-items: center;
    justify-content: center;
    background:
        radial-gradient(circle at 50% 35%, #172b63 0%, #081638 45%, #030817 100%);
    font-family: Arial, Helvetica, sans-serif;
    color: white;
}}

.container {{
    text-align: center;
    animation: appear .7s ease;
}}

.logo {{
    width: 210px;
    height: 210px;
    object-fit: cover;
    border-radius: 42px;
    box-shadow:
        0 0 30px rgba(34,211,238,.35),
        0 0 70px rgba(139,92,246,.25);
}}

.title {{
    margin-top: 22px;
    font-size: 34px;
    font-weight: 700;
    letter-spacing: 2px;
}}

.subtitle {{
    margin-top: 7px;
    font-size: 14px;
    letter-spacing: 5px;
    color: #67e8f9;
}}

.loading {{
    width: 220px;
    height: 5px;
    margin: 30px auto 0;
    border-radius: 20px;
    background: rgba(255,255,255,.12);
    overflow: hidden;
}}

.loading::after {{
    content: "";
    display: block;
    width: 0%;
    height: 100%;
    border-radius: 20px;
    background: linear-gradient(
        90deg,
        #22d3ee,
        #6366f1,
        #a855f7,
        #ec4899
    );
    animation: progress 3s linear forwards;
}}

.status {{
    margin-top: 13px;
    color: rgba(255,255,255,.55);
    font-size: 12px;
    letter-spacing: 1px;
}}

@keyframes progress {{
    from {{ width: 0%; }}
    to {{ width: 100%; }}
}}

@keyframes appear {{
    from {{
        opacity: 0;
        transform: scale(.92);
    }}
    to {{
        opacity: 1;
        transform: scale(1);
    }}
}}
</style>
</head>

<body>
<div class="container">
    <img class="logo" src="{icon_uri}">
    <div class="title">Skyla</div>
    <div class="subtitle">LIFE OS</div>
    <div class="loading"></div>
    <div class="status">Initializing your Life OS...</div>
</div>
</body>
</html>
"""

    with open(SPLASH, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    create_splash()
    start_server()

    if not wait_for_server():
        raise RuntimeError("Skyla server could not be started.")

    splash_uri = "file://" + SPLASH

    window = webview.create_window(
        "Skyla Life OS",
        splash_uri,
        width=1440,
        height=900,
        min_size=(1000, 650),
        resizable=True,
        confirm_close=True,
        background_color="#030817",
    )

    def open_dashboard():
        time.sleep(3)
        window.load_url(URL)

    webview.start(open_dashboard)


if __name__ == "__main__":
    main()
