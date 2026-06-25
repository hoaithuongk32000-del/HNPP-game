#!/usr/bin/env python3
"""
HNPP - Hanoi Academy People's Police Website
All-in-one single Python file (Flask + SQLite)
Responsive for PC and Mobile
Features: Content builder, Image upload, Markdown links, Multi-DB, Role hierarchy, Password encryption
"""

import os
import json
import uuid
import secrets
import sqlite3
import re
import base64
import hashlib
from datetime import datetime, timezone
from functools import wraps
from urllib.request import urlopen, Request
from urllib.error import URLError

from flask import (
    Flask, request, redirect,
    url_for, session, flash, g, abort, jsonify, send_from_directory
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from markupsafe import escape
from flask import get_flashed_messages as _flask_gfm

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_ACCOUNT = os.path.join(BASE_DIR, "account.db")
DB_BAIDANG = os.path.join(BASE_DIR, "baidang.db")
DB_MAIN = os.path.join(BASE_DIR, "main.db")

UPLOAD_DIR = os.path.join(BASE_DIR, "Hinhanh", "baidang")
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

MOD_KEY = "PUNKX--MEUG-4KK8-Q0SJ-FHXK"
MOD_PASS = "HNPP_AD-NO-PASS[18]ok"
MOD_PASS_PARAM = "hhoaihuongvntr"

PASSWORD_PAGE_KEY = "mu6jAG5ZxVP$72G"
PASSWORD_PAGE_PASS = "hoaithuong"

LOGO_URL = "https://inviva.vn/wp-content/uploads/2026/04/logo-cong-an-vector-03.png"

CATEGORIES = ["Tin tức", "Developer", "Quyết định", "Nghị định", "Sự kiện", "Luật"]

ROLE_LEVELS = {
    "creators": 1,
    "trial_moderator": 2,
    "moderator": 3,
    "trial_admin": 4,
    "admin": 5,
    "headadmin": 6,
}

ROLE_LABELS = {
    "creators": "Creators",
    "trial_moderator": "Trial Moderator",
    "moderator": "Moderator",
    "trial_admin": "Trial Admin",
    "admin": "Admin",
    "headadmin": "Headadmin",
}

app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

# ── Persistent secret keys ──────────────────────────────────────────────────


def _ensure_main_db():
    db = sqlite3.connect(DB_MAIN)
    db.execute(
        "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
    )
    db.commit()
    return db


def get_persistent_secret(name):
    db = _ensure_main_db()
    row = db.execute("SELECT value FROM settings WHERE key=?", (name,)).fetchone()
    if row:
        val = row[0]
    else:
        val = secrets.token_hex(32)
        db.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (name, val))
        db.commit()
    db.close()
    return val


app.secret_key = os.environ.get("SECRET_KEY") or get_persistent_secret("app_secret")
ENC_KEY = get_persistent_secret("enc_key")

# ── Encryption helpers (reversible, for /password/ page) ─────────────────────


def encrypt_password(plaintext):
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", ENC_KEY.encode(), salt, 100000)
    data = plaintext.encode("utf-8")
    ext_key = (key * (len(data) // len(key) + 1))[: len(data)]
    encrypted = bytes(a ^ b for a, b in zip(data, ext_key))
    return base64.urlsafe_b64encode(salt + encrypted).decode("ascii")


def decrypt_password(ciphertext):
    raw = base64.urlsafe_b64decode(ciphertext.encode("ascii"))
    salt, encrypted = raw[:16], raw[16:]
    key = hashlib.pbkdf2_hmac("sha256", ENC_KEY.encode(), salt, 100000)
    ext_key = (key * (len(encrypted) // len(key) + 1))[: len(encrypted)]
    return bytes(a ^ b for a, b in zip(encrypted, ext_key)).decode("utf-8")


# ── Database ────────────────────────────────────────────────────────────────


def get_account_db():
    if "_db_acc" not in g:
        g._db_acc = sqlite3.connect(DB_ACCOUNT)
        g._db_acc.row_factory = sqlite3.Row
    return g._db_acc


def get_baidang_db():
    if "_db_bd" not in g:
        g._db_bd = sqlite3.connect(DB_BAIDANG)
        g._db_bd.row_factory = sqlite3.Row
    return g._db_bd


def get_main_db():
    if "_db_main" not in g:
        g._db_main = sqlite3.connect(DB_MAIN)
        g._db_main.row_factory = sqlite3.Row
    return g._db_main


@app.teardown_appcontext
def close_dbs(exc):
    for key in ("_db_acc", "_db_bd", "_db_main"):
        db = g.pop(key, None)
        if db:
            db.close()


def init_db():
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    db = sqlite3.connect(DB_ACCOUNT)
    db.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        password_enc TEXT NOT NULL,
        display_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'creators',
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )""")
    db.commit()
    db.close()

    db = sqlite3.connect(DB_BAIDANG)
    db.execute("""CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        description TEXT DEFAULT '',
        content TEXT NOT NULL DEFAULT '',
        content_modules TEXT NOT NULL DEFAULT '[]',
        category TEXT NOT NULL DEFAULT 'Tin tức',
        author_id INTEGER NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        is_published INTEGER NOT NULL DEFAULT 1
    )""")
    db.commit()
    db.close()

    _ensure_main_db()


def slugify(text):
    t = text.lower().strip()
    for src, dst in [
        (r"[àáạảãâầấậẩẫăằắặẳẵ]", "a"),
        (r"[èéẹẻẽêềếệểễ]", "e"),
        (r"[ìíịỉĩ]", "i"),
        (r"[òóọỏõôồốộổỗơờớợởỡ]", "o"),
        (r"[ùúụủũưừứựửữ]", "u"),
        (r"[ỳýỵỷỹ]", "y"),
        (r"[đ]", "d"),
    ]:
        t = re.sub(src, dst, t)
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


# ── Auth helpers ─────────────────────────────────────────────────────────────


def get_current_user():
    if "user_id" in session:
        db = get_account_db()
        return db.execute(
            "SELECT * FROM users WHERE id=?", (session["user_id"],)
        ).fetchone()
    return None


def role_level(user):
    if not user:
        return 0
    return ROLE_LEVELS.get(user["role"], 0)


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Vui lòng đăng nhập.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def creator_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Vui lòng đăng nhập.", "warning")
            return redirect(url_for("login"))
        user = get_current_user()
        if not user or role_level(user) < ROLE_LEVELS["creators"]:
            flash("Bạn không có quyền truy cập.", "danger")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Vui lòng đăng nhập.", "warning")
            return redirect(url_for("login"))
        user = get_current_user()
        if not user or role_level(user) < ROLE_LEVELS["trial_admin"]:
            flash("Bạn không có quyền truy cập.", "danger")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return wrapper


# ── Text rendering helpers ──────────────────────────────────────────────────


def render_text_with_links(text):
    parts = []
    last_end = 0
    for m in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text):
        before = str(escape(text[last_end : m.start()])).replace("\n", "<br>")
        parts.append(before)
        link_text = str(escape(m.group(1)))
        link_url = str(escape(m.group(2)))
        parts.append(
            f'<a href="{link_url}" style="color:#1976d2;text-decoration:underline" target="_blank">{link_text}</a>'
        )
        last_end = m.end()
    after = str(escape(text[last_end:])).replace("\n", "<br>")
    parts.append(after)
    return "".join(parts)


def build_style_css(style):
    css = []
    if style.get("color"):
        css.append(f"color:{escape(style['color'])}")
    if style.get("bold"):
        css.append("font-weight:bold")
    if style.get("italic"):
        css.append("font-style:italic")
    td = []
    if style.get("strikethrough"):
        td.append("line-through")
    if style.get("underline"):
        td.append("underline")
    if td:
        css.append(f"text-decoration:{' '.join(td)}")
    return ";".join(css)


def render_modules_html(modules_json):
    try:
        modules = json.loads(modules_json) if isinstance(modules_json, str) else modules_json
    except (json.JSONDecodeError, TypeError):
        return ""
    if not modules:
        return ""
    parts = []
    for mod in modules:
        mt = mod.get("type", "text")
        content = mod.get("content", "")
        images = mod.get("images", [])
        style = mod.get("style", {})
        link = mod.get("link", {})
        css = build_style_css(style)
        style_attr = f' style="{css}"' if css else ""

        if mt == "text":
            parts.append(f'<div class="mod-text"{style_attr}>{render_text_with_links(content)}</div>')

        elif mt == "image" and images:
            parts.append(f'<div class="mod-image"><img src="/{escape(images[0])}" alt="" loading="lazy"></div>')

        elif mt == "image_left_text" and images:
            img = f'<img src="/{escape(images[0])}" alt="" loading="lazy">'
            parts.append(
                f'<div class="mod-img-text"{style_attr}>'
                f'<div class="mod-img-side">{img}</div>'
                f'<div class="mod-text-side">{render_text_with_links(content)}</div></div>'
            )

        elif mt == "image_right_text" and images:
            img = f'<img src="/{escape(images[0])}" alt="" loading="lazy">'
            parts.append(
                f'<div class="mod-text-img"{style_attr}>'
                f'<div class="mod-text-side">{render_text_with_links(content)}</div>'
                f'<div class="mod-img-side">{img}</div></div>'
            )

        elif mt == "double_image":
            imgs = "".join(f'<img src="/{escape(i)}" alt="" loading="lazy">' for i in images[:2])
            parts.append(f'<div class="mod-images mod-images-2">{imgs}</div>')

        elif mt == "triple_image":
            imgs = "".join(f'<img src="/{escape(i)}" alt="" loading="lazy">' for i in images[:3])
            parts.append(f'<div class="mod-images mod-images-3">{imgs}</div>')

        elif mt == "quad_image":
            imgs = "".join(f'<img src="/{escape(i)}" alt="" loading="lazy">' for i in images[:4])
            parts.append(f'<div class="mod-images mod-images-4">{imgs}</div>')

        elif mt == "link_preview":
            url = str(escape(link.get("url", "#")))
            title = str(escape(link.get("title", url)))
            desc = str(escape(link.get("description", "")))
            parts.append(
                f'<a href="{url}" class="mod-link-preview" target="_blank">'
                f'<div class="mod-link-title">{title}</div>'
                f'<div class="mod-link-desc">{desc}</div></a>'
            )
    return "\n".join(parts)


# ── Render helper ───────────────────────────────────────────────────────────


def render_page(title, body_html, status=200):
    user = get_current_user()
    year = datetime.now(timezone.utc).year
    flashes = ""
    for cat, msg in _flask_gfm(with_categories=True):
        flashes += f'<div class="flash {cat}">{msg}</div>'
    nav_extra = ""
    if user:
        rl = role_level(user)
        if rl >= ROLE_LEVELS["creators"]:
            nav_extra += f'\n<a href="{url_for("creator")}">Tạo bài</a>'
        if rl >= ROLE_LEVELS["trial_admin"]:
            nav_extra += f'\n<a href="{url_for("admin_panel")}">Admin</a>'
        nav_extra += f'\n<a href="{url_for("logout")}">Đăng xuất</a>'
    else:
        nav_extra = f'<a href="{url_for("login")}">Đăng nhập</a>'

    html = LAYOUT.replace("{{TITLE}}", title)
    html = html.replace("{{NAV_EXTRA}}", nav_extra)
    html = html.replace("{{FLASHES}}", flashes)
    html = html.replace("{{BODY}}", body_html)
    html = html.replace("{{YEAR}}", str(year))
    html = html.replace("{{URL_HOME}}", url_for("home"))
    html = html.replace("{{URL_LOGIN}}", url_for("login"))
    html = html.replace("{{URL_LUAT}}", url_for("luat_hnpp"))
    html = html.replace("{{URL_POSTS}}", url_for("list_posts"))
    html = html.replace("{{URL_GAME}}", url_for("group_game"))
    html = html.replace("{{URL_SUPPORT}}", url_for("support"))
    html = html.replace("{{URL_TOS}}", url_for("tos"))
    html = html.replace("{{URL_POLICY}}", url_for("chinh_sach"))
    html = html.replace("{{URL_COPYRIGHT}}", url_for("ban_quyen"))
    html = html.replace("{{URL_ADMIN}}", url_for("admin_panel"))
    html = html.replace("{{URL_CREATOR}}", url_for("creator"))
    html = html.replace("{{LOGO_URL}}", LOGO_URL)
    return html, status


# ── Layout ──────────────────────────────────────────────────────────────────

LAYOUT = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{TITLE}} - HNPP</title>
<style>
:root{--primary:#b71c1c;--primary-dark:#7f0000;--accent:#ffd600;--bg:#f5f5f5;--text:#212121;--white:#fff;--border:#e0e0e0;--shadow:0 2px 8px rgba(0,0,0,.10)}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{font-family:'Segoe UI','Roboto',Arial,sans-serif;background:var(--bg);color:var(--text);line-height:1.6;min-height:100vh;display:flex;flex-direction:column}
.top-bar{background:var(--primary-dark);color:var(--white);font-size:.78rem;padding:4px 0;text-align:center}
.top-bar a{color:var(--accent);text-decoration:none;margin:0 8px}
header{background:linear-gradient(135deg,var(--primary) 0%,var(--primary-dark) 100%);color:var(--white);position:sticky;top:0;z-index:1000;box-shadow:0 2px 12px rgba(0,0,0,.18)}
.header-inner{max-width:1200px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;padding:0 16px;height:64px}
.logo{display:flex;align-items:center;gap:10px;text-decoration:none;color:var(--white)}
.logo-img{width:42px;height:42px;border-radius:50%;object-fit:cover;background:var(--white)}
.logo-text{font-size:1.15rem;font-weight:700;letter-spacing:.5px;line-height:1.2}
.logo-sub{font-size:.72rem;font-weight:400;opacity:.85}
nav{display:flex;align-items:center;gap:2px}
nav a{color:var(--white);text-decoration:none;padding:8px 13px;border-radius:6px;font-size:.88rem;font-weight:500;transition:background .2s;white-space:nowrap}
nav a:hover{background:rgba(255,255,255,.15)}
.hamburger{display:none;flex-direction:column;gap:5px;cursor:pointer;background:none;border:none;padding:8px}
.hamburger span{display:block;width:26px;height:3px;background:var(--white);border-radius:2px;transition:.3s}
.banner{background:linear-gradient(135deg,var(--primary-dark) 0%,var(--primary) 60%,#d32f2f 100%);color:var(--white);text-align:center;padding:48px 16px 40px}
.banner h1{font-size:2rem;font-weight:800;margin-bottom:8px;text-transform:uppercase;letter-spacing:1px}
.banner p{font-size:1.05rem;opacity:.92;max-width:600px;margin:0 auto}
main{max-width:1200px;margin:0 auto;padding:24px 16px 48px;flex:1;width:100%}
.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:20px;margin-top:20px}
.card{background:var(--white);border-radius:10px;box-shadow:var(--shadow);padding:24px;transition:transform .2s,box-shadow .2s;border-left:4px solid var(--primary)}
.card:hover{transform:translateY(-3px);box-shadow:0 6px 20px rgba(0,0,0,.13)}
.card h3{color:var(--primary);margin-bottom:8px;font-size:1.1rem}
.card p{color:#555;font-size:.92rem}
.card .meta{font-size:.78rem;color:#999;margin-top:10px}
.card a{color:var(--primary);text-decoration:none;font-weight:600}
.card a:hover{text-decoration:underline}
.section-title{font-size:1.35rem;font-weight:700;color:var(--primary);border-bottom:3px solid var(--primary);padding-bottom:8px;margin-bottom:20px;display:flex;align-items:center;gap:8px}
.section-title::before{content:'';width:6px;height:24px;background:var(--accent);border-radius:3px;display:inline-block}
.page-content{background:var(--white);border-radius:10px;box-shadow:var(--shadow);padding:32px;margin-top:16px}
.page-content h1,.page-content h2{color:var(--primary);margin-bottom:16px}
.page-content h3{color:var(--primary-dark);margin:18px 0 8px}
.page-content p{margin-bottom:12px}
.page-content ul,.page-content ol{margin-left:24px;margin-bottom:12px}
.form-container{max-width:480px;margin:32px auto;background:var(--white);padding:36px;border-radius:12px;box-shadow:var(--shadow)}
.form-container.wide{max-width:860px}
.form-container h2{text-align:center;color:var(--primary);margin-bottom:24px;font-size:1.4rem}
.form-group{margin-bottom:18px}
.form-group label{display:block;margin-bottom:6px;font-weight:600;font-size:.9rem;color:#333}
.form-group input,.form-group textarea,.form-group select{width:100%;padding:10px 14px;border:2px solid var(--border);border-radius:8px;font-size:.95rem;transition:border .2s;font-family:inherit}
.form-group input:focus,.form-group textarea:focus,.form-group select:focus{border-color:var(--primary);outline:none}
.form-group textarea{min-height:180px;resize:vertical}
.btn{display:inline-block;background:var(--primary);color:var(--white);padding:11px 28px;border:none;border-radius:8px;font-size:.95rem;font-weight:600;cursor:pointer;transition:background .2s;text-decoration:none;text-align:center}
.btn:hover{background:var(--primary-dark)}
.btn-full{width:100%}
.btn-sm{padding:6px 16px;font-size:.82rem}
.btn-outline{background:transparent;color:var(--primary);border:2px solid var(--primary)}
.btn-outline:hover{background:var(--primary);color:var(--white)}
.btn-accent{background:var(--accent);color:var(--primary-dark)}
.btn-accent:hover{background:#ffca00}
.btn-danger{background:#c62828}
.btn-danger:hover{background:#8e0000}
.flash{max-width:1200px;margin:12px auto;padding:12px 20px;border-radius:8px;font-size:.9rem;font-weight:500}
.flash.success{background:#e8f5e9;color:#2e7d32;border:1px solid #a5d6a7}
.flash.danger{background:#ffebee;color:#c62828;border:1px solid #ef9a9a}
.flash.warning{background:#fff8e1;color:#f57f17;border:1px solid #ffe082}
.flash.info{background:#e3f2fd;color:#1565c0;border:1px solid #90caf9}
.table-wrapper{overflow-x:auto}
table{width:100%;border-collapse:collapse;margin-top:12px;font-size:.9rem}
th,td{padding:10px 14px;text-align:left;border-bottom:1px solid var(--border)}
th{background:var(--primary);color:var(--white);font-weight:600}
tr:hover{background:#fafafa}
footer{background:#1a1a1a;color:#ccc;padding:36px 16px 20px;margin-top:auto}
.footer-inner{max-width:1200px;margin:0 auto;display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:24px}
.footer-col h4{color:var(--accent);margin-bottom:12px;font-size:1rem}
.footer-col a{color:#ccc;text-decoration:none;display:block;padding:3px 0;font-size:.88rem}
.footer-col a:hover{color:var(--accent)}
.footer-bottom{text-align:center;margin-top:24px;padding-top:16px;border-top:1px solid #333;font-size:.8rem;color:#888}
.two-col{display:grid;grid-template-columns:1fr 320px;gap:24px;margin-top:20px}
.sidebar .widget{background:var(--white);border-radius:10px;box-shadow:var(--shadow);padding:20px;margin-bottom:16px}
.sidebar .widget h4{color:var(--primary);font-size:1rem;margin-bottom:12px;border-bottom:2px solid var(--accent);padding-bottom:6px}
.sidebar .widget ul{list-style:none}
.sidebar .widget li{padding:5px 0;border-bottom:1px solid #f0f0f0}
.sidebar .widget li a{color:var(--text);text-decoration:none;font-size:.88rem}
.sidebar .widget li a:hover{color:var(--primary)}
.badge{display:inline-block;padding:2px 10px;border-radius:12px;font-size:.72rem;font-weight:600;text-transform:uppercase}
.badge-creators{background:#e8f5e9;color:#2e7d32}
.badge-trial_moderator{background:#e3f2fd;color:#1565c0}
.badge-moderator{background:#e3f2fd;color:#0d47a1}
.badge-trial_admin{background:#fff3e0;color:#e65100}
.badge-admin{background:var(--primary);color:var(--white)}
.badge-headadmin{background:var(--accent);color:var(--primary-dark)}
.badge-user{background:#e3f2fd;color:#1565c0}
.post-header{margin-bottom:20px}
.post-header h1{font-size:1.8rem;color:var(--primary);line-height:1.3}
.post-meta{color:#888;font-size:.85rem;margin-top:8px}
.post-body{font-size:1rem;line-height:1.8}
.post-body p{margin-bottom:14px}
.post-desc{color:#555;font-size:1rem;margin:12px 0 20px;padding:12px 16px;background:#f9f9f9;border-left:3px solid var(--accent);border-radius:4px}
.quick-links{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;margin:20px 0}
.quick-link{background:var(--white);border-radius:10px;padding:20px;text-align:center;box-shadow:var(--shadow);transition:transform .2s;text-decoration:none;color:var(--text)}
.quick-link:hover{transform:translateY(-3px)}
.quick-link .icon{font-size:2rem;margin-bottom:8px}
.quick-link span{font-size:.88rem;font-weight:600;display:block}
.stats-bar{display:flex;gap:16px;flex-wrap:wrap;margin:20px 0}
.stat-item{flex:1;min-width:140px;background:var(--white);border-radius:10px;padding:16px;text-align:center;box-shadow:var(--shadow);border-top:3px solid var(--primary)}
.stat-item .num{font-size:1.8rem;font-weight:800;color:var(--primary)}
.stat-item .label{font-size:.8rem;color:#888}
details{background:var(--white);padding:16px;border-radius:8px;margin-bottom:8px;box-shadow:var(--shadow)}
summary{cursor:pointer;font-weight:600;color:var(--primary)}
.cb-label{display:flex;align-items:center;gap:8px;font-weight:400!important;cursor:pointer}
/* Module rendering styles */
.mod-text{margin:16px 0;line-height:1.8}
.mod-image{margin:16px 0;text-align:center}
.mod-image img{max-width:100%;border-radius:8px;box-shadow:var(--shadow)}
.mod-img-text,.mod-text-img{display:flex;gap:20px;margin:16px 0;align-items:flex-start;flex-wrap:wrap}
.mod-img-side{flex:0 0 40%;max-width:40%}
.mod-img-side img{width:100%;border-radius:8px;box-shadow:var(--shadow)}
.mod-text-side{flex:1;min-width:200px;line-height:1.8}
.mod-images{display:grid;gap:12px;margin:16px 0}
.mod-images img{width:100%;border-radius:8px;box-shadow:var(--shadow);object-fit:cover}
.mod-images-2{grid-template-columns:1fr 1fr}
.mod-images-3{grid-template-columns:1fr 1fr 1fr}
.mod-images-4{grid-template-columns:1fr 1fr}
.mod-link-preview{display:block;border:2px solid var(--border);border-radius:10px;padding:20px;margin:16px 0;text-decoration:none;color:var(--text);transition:border-color .2s,box-shadow .2s}
.mod-link-preview:hover{border-color:var(--primary);box-shadow:var(--shadow)}
.mod-link-title{font-size:1.1rem;font-weight:700;color:var(--primary);margin-bottom:6px}
.mod-link-desc{font-size:.9rem;color:#666}
@media(max-width:768px){
.header-inner{height:56px}
nav{display:none;flex-direction:column;position:absolute;top:56px;left:0;right:0;background:var(--primary-dark);padding:12px 0;box-shadow:0 4px 12px rgba(0,0,0,.2)}
nav.open{display:flex}
nav a{padding:12px 24px;border-radius:0}
.hamburger{display:flex}
.banner h1{font-size:1.4rem}
.banner p{font-size:.9rem}
.two-col{grid-template-columns:1fr}
.card-grid{grid-template-columns:1fr}
.form-container{padding:24px 16px;margin:16px}
.page-content{padding:20px 16px}
.footer-inner{grid-template-columns:1fr}
.quick-links{grid-template-columns:repeat(2,1fr)}
.stats-bar{flex-direction:column}
.logo-text{font-size:.95rem}
.mod-img-text,.mod-text-img{flex-direction:column}
.mod-img-side{flex:none;max-width:100%}
.mod-images-3{grid-template-columns:1fr}
.mod-images-4{grid-template-columns:1fr 1fr}
}
</style>
</head>
<body>
<div class="top-bar">
    <a href="{{URL_TOS}}">Điều khoản</a> |
    <a href="{{URL_POLICY}}">Chính sách</a> |
    <a href="{{URL_COPYRIGHT}}">Bản quyền</a> |
    <a href="{{URL_SUPPORT}}">Hỗ trợ</a>
</div>
<header>
<div class="header-inner">
    <a href="{{URL_HOME}}" class="logo">
        <img src="{{LOGO_URL}}" alt="HNPP" class="logo-img">
        <div>
            <div class="logo-text">HNPP</div>
            <div class="logo-sub">Hanoi Academy People's Police</div>
        </div>
    </a>
    <button class="hamburger" onclick="document.querySelector('nav').classList.toggle('open')">
        <span></span><span></span><span></span>
    </button>
    <nav>
        <a href="{{URL_HOME}}">Trang chủ</a>
        <a href="{{URL_LUAT}}">Luật HNPP</a>
        <a href="{{URL_POSTS}}">Bài đăng</a>
        <a href="{{URL_GAME}}">Group Game</a>
        <a href="{{URL_SUPPORT}}">Support</a>
        {{NAV_EXTRA}}
    </nav>
</div>
</header>
{{FLASHES}}
{{BODY}}
<footer>
<div class="footer-inner">
    <div class="footer-col">
        <h4>HNPP</h4>
        <p style="font-size:.85rem">Hanoi Academy People's Police<br>Cổng thông tin chính thức</p>
    </div>
    <div class="footer-col">
        <h4>Liên kết</h4>
        <a href="{{URL_HOME}}">Trang chủ</a>
        <a href="{{URL_LUAT}}">Luật HNPP</a>
        <a href="{{URL_POSTS}}">Bài đăng</a>
        <a href="{{URL_GAME}}">Group Game</a>
    </div>
    <div class="footer-col">
        <h4>Pháp lý</h4>
        <a href="{{URL_TOS}}">Điều khoản sử dụng</a>
        <a href="{{URL_POLICY}}">Chính sách bảo mật</a>
        <a href="{{URL_COPYRIGHT}}">Bản quyền</a>
    </div>
    <div class="footer-col">
        <h4>Hỗ trợ</h4>
        <a href="{{URL_SUPPORT}}">Liên hệ hỗ trợ</a>
        <a href="{{URL_ADMIN}}">Quản trị</a>
    </div>
</div>
<div class="footer-bottom">&copy; {{YEAR}} HNPP - Hanoi Academy People's Police. All rights reserved.</div>
</footer>
<script>
document.querySelectorAll('nav a').forEach(function(a){
    a.addEventListener('click',function(){document.querySelector('nav').classList.remove('open');});
});
</script>
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════════════════
# 1. TRANG CHU
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/")
def home():
    db = get_baidang_db()
    posts = db.execute(
        "SELECT * FROM posts WHERE is_published=1 ORDER BY created_at DESC LIMIT 6"
    ).fetchall()
    pc = db.execute("SELECT COUNT(*) FROM posts WHERE is_published=1").fetchone()[0]
    uc = get_account_db().execute("SELECT COUNT(*) FROM users").fetchone()[0]

    cards = ""
    for p in posts:
        raw = p["content"]
        snippet = str(escape(raw[:150])) + ("..." if len(raw) > 150 else "")
        cards += f"""<div class="card">
            <h3><a href="{url_for('view_post', slug=p['slug'])}">{escape(p['title'])}</a></h3>
            <p>{snippet}</p>
            <div class="meta">{p['category']} &bull; {p['created_at'][:16]}</div>
        </div>"""
    if not posts:
        cards = '<div class="page-content"><p>Chưa có bài đăng nào.</p></div>'

    cat_items = ""
    for c in CATEGORIES:
        cat_items += f'<li><a href="{{{{URL_POSTS}}}}?cat={c}">{c}</a></li>'

    body = f"""
    <div class="banner">
        <h1>Cổng Thông Tin HNPP</h1>
        <p>Hanoi Academy People's Police &mdash; Hệ thống thông tin pháp luật và quản lý nội bộ</p>
    </div>
    <main>
        <div class="stats-bar">
            <div class="stat-item"><div class="num">{pc}</div><div class="label">Bài đăng</div></div>
            <div class="stat-item"><div class="num">{uc}</div><div class="label">Thành viên</div></div>
            <div class="stat-item"><div class="num">{len(CATEGORIES)}</div><div class="label">Mục</div></div>
            <div class="stat-item"><div class="num">24/7</div><div class="label">Hỗ trợ</div></div>
        </div>
        <div class="quick-links">
            <a href="{{{{URL_LUAT}}}}" class="quick-link"><div class="icon">&#9878;</div><span>Luật HNPP</span></a>
            <a href="{{{{URL_POSTS}}}}" class="quick-link"><div class="icon">&#128240;</div><span>Bài đăng</span></a>
            <a href="{{{{URL_GAME}}}}" class="quick-link"><div class="icon">&#127918;</div><span>Group Game</span></a>
            <a href="{{{{URL_SUPPORT}}}}" class="quick-link"><div class="icon">&#128172;</div><span>Hỗ trợ</span></a>
            <a href="{{{{URL_TOS}}}}" class="quick-link"><div class="icon">&#128220;</div><span>Điều khoản</span></a>
            <a href="{{{{URL_COPYRIGHT}}}}" class="quick-link"><div class="icon">&copy;</div><span>Bản quyền</span></a>
        </div>
        <div class="two-col">
            <div>
                <div class="section-title">Bài đăng mới nhất</div>
                <div class="card-grid" style="grid-template-columns:1fr">{cards}</div>
            </div>
            <div class="sidebar">
                <div class="widget">
                    <h4>Mục</h4>
                    <ul>{cat_items}</ul>
                </div>
                <div class="widget">
                    <h4>Thông báo</h4>
                    <p style="font-size:.88rem;color:#555">Chào mừng bạn đến với cổng thông tin HNPP. Vui lòng tuân thủ các quy định và luật lệ của hệ thống.</p>
                </div>
            </div>
        </div>
    </main>"""
    return render_page("Trang chủ", body)


# ═══════════════════════════════════════════════════════════════════════════
# 2. DANG NHAP
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        db = get_account_db()
        user = db.execute(
            "SELECT * FROM users WHERE username=?", (username,)
        ).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            flash(f"Xin chào, {user['display_name']}!", "success")
            return redirect(url_for("home"))
        flash("Tên đăng nhập hoặc mật khẩu không đúng.", "danger")
    body = f"""<main>
    <div class="form-container">
        <h2>&#128274; Đăng nhập</h2>
        <form method="POST">
            <div class="form-group"><label>Tên đăng nhập</label>
                <input type="text" name="username" required autocomplete="username" placeholder="Nhập tên đăng nhập"></div>
            <div class="form-group"><label>Mật khẩu</label>
                <input type="password" name="password" required autocomplete="current-password" placeholder="Nhập mật khẩu"></div>
            <button type="submit" class="btn btn-full">Đăng nhập</button>
        </form>
        <p style="text-align:center;margin-top:16px;font-size:.85rem;color:#888">
            Chỉ dành cho tài khoản được tạo trước bởi quản trị viên.</p>
    </div></main>"""
    return render_page("Đăng nhập", body)


@app.route("/logout")
def logout():
    session.clear()
    flash("Đã đăng xuất.", "info")
    return redirect(url_for("home"))


# ═══════════════════════════════════════════════════════════════════════════
# 3. TRANG AN - MOD
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/mod")
def mod_page():
    key = request.args.get("key", "")
    passw = request.args.get(MOD_PASS_PARAM, "")
    if key != MOD_KEY or passw != MOD_PASS:
        abort(404)
    db = get_account_db()
    users = db.execute("SELECT * FROM users ORDER BY id").fetchall()

    role_opts = "".join(
        f'<option value="{r}">{ROLE_LABELS[r]}</option>' for r in ROLE_LEVELS
    )

    rows = ""
    for u in users:
        badge_cls = f"badge-{u['role']}"
        label = ROLE_LABELS.get(u["role"], u["role"])
        rows += f"""<tr>
            <td>{u['id']}</td><td>{u['username']}</td><td>{u['display_name']}</td>
            <td><span class="badge {badge_cls}">{label}</span></td>
            <td>{u['created_at'][:16]}</td>
            <td><form method="POST" action="{url_for('mod_delete')}" style="display:inline">
                <input type="hidden" name="mod_key" value="{key}">
                <input type="hidden" name="mod_pass" value="{passw}">
                <input type="hidden" name="user_id" value="{u['id']}">
                <button type="submit" class="btn btn-sm btn-danger" onclick="return confirm('Xóa tài khoản này?')">Xóa</button>
            </form></td></tr>"""

    body = f"""<main>
    <div class="form-container wide">
        <h2>&#128272; Quản lý tài khoản</h2>
        <form method="POST" action="{url_for('mod_create')}">
            <input type="hidden" name="mod_key" value="{key}">
            <input type="hidden" name="mod_pass" value="{passw}">
            <div class="section-title" style="font-size:1rem">Tạo tài khoản mới</div>
            <div class="form-group"><label>Tên đăng nhập</label><input type="text" name="username" required placeholder="Tên đăng nhập"></div>
            <div class="form-group"><label>Tên hiển thị</label><input type="text" name="display_name" required placeholder="Tên hiển thị"></div>
            <div class="form-group"><label>Mật khẩu</label><input type="password" name="password" required placeholder="Mật khẩu"></div>
            <div class="form-group"><label>Quyền hạn</label>
                <select name="role">{role_opts}</select></div>
            <button type="submit" class="btn btn-full btn-accent">Tạo tài khoản</button>
        </form>
        <div style="margin-top:32px">
            <div class="section-title" style="font-size:1rem">Danh sách tài khoản</div>
            <div class="table-wrapper"><table>
                <thead><tr><th>ID</th><th>Username</th><th>Tên</th><th>Quyền</th><th>Ngày tạo</th><th>Hành động</th></tr></thead>
                <tbody>{rows}</tbody>
            </table></div>
        </div>
    </div></main>"""
    return render_page("Quản lý tài khoản", body)


@app.route("/mod/create", methods=["POST"])
def mod_create():
    key = request.form.get("mod_key", "")
    passw = request.form.get("mod_pass", "")
    if key != MOD_KEY or passw != MOD_PASS:
        abort(404)
    username = request.form.get("username", "").strip()
    display_name = request.form.get("display_name", "").strip()
    password = request.form.get("password", "")
    role = request.form.get("role", "creators")
    if role not in ROLE_LEVELS:
        role = "creators"
    if not username or not password:
        flash("Vui lòng điền đầy đủ thông tin.", "warning")
        return redirect(f"/mod?key={key}&{MOD_PASS_PARAM}={passw}")
    db = get_account_db()
    try:
        pw_hash = generate_password_hash(password)
        pw_enc = encrypt_password(password)
        db.execute(
            "INSERT INTO users (username,password_hash,password_enc,display_name,role) VALUES (?,?,?,?,?)",
            (username, pw_hash, pw_enc, display_name, role),
        )
        db.commit()
        flash(f"Tạo tài khoản '{username}' thành công!", "success")
    except sqlite3.IntegrityError:
        flash(f"Tên đăng nhập '{username}' đã tồn tại.", "danger")
    return redirect(f"/mod?key={key}&{MOD_PASS_PARAM}={passw}")


@app.route("/mod/delete", methods=["POST"])
def mod_delete():
    key = request.form.get("mod_key", "")
    passw = request.form.get("mod_pass", "")
    if key != MOD_KEY or passw != MOD_PASS:
        abort(404)
    db = get_account_db()
    db.execute("DELETE FROM users WHERE id=?", (request.form.get("user_id"),))
    db.commit()
    flash("Đã xóa tài khoản.", "success")
    return redirect(f"/mod?key={key}&{MOD_PASS_PARAM}={passw}")


# ═══════════════════════════════════════════════════════════════════════════
# 4. CREATOR - Content Builder
# ═══════════════════════════════════════════════════════════════════════════

CREATOR_CSS = """
<style>
.desc-counter{text-align:right;font-size:.78rem;color:#888;margin-top:4px}
.desc-counter.over{color:#c62828}
.builder-toolbar{display:flex;gap:10px;margin:20px 0;flex-wrap:wrap;align-items:center}
.btn-add{background:var(--primary);color:#fff;border:none;padding:10px 24px;border-radius:8px;font-size:1rem;cursor:pointer;display:flex;align-items:center;gap:6px;font-weight:600}
.btn-add:hover{background:var(--primary-dark)}
.add-modal-overlay{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.5);z-index:2000;align-items:center;justify-content:center}
.add-modal-overlay.show{display:flex}
.add-modal{background:#fff;border-radius:14px;padding:28px;max-width:700px;width:95%;max-height:85vh;overflow-y:auto;box-shadow:0 8px 32px rgba(0,0,0,.2)}
.add-modal h3{color:var(--primary);margin-bottom:20px;text-align:center;font-size:1.2rem}
.module-options{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:14px}
.module-option{border:2px solid var(--border);border-radius:10px;padding:14px 10px;text-align:center;cursor:pointer;transition:border-color .2s,transform .2s}
.module-option:hover{border-color:var(--primary);transform:translateY(-2px)}
.module-option .illust{height:60px;display:flex;align-items:center;justify-content:center;margin-bottom:8px}
.module-option span{font-size:.82rem;font-weight:600;color:#333}
.illust-lines div{width:70%;height:3px;background:#bbb;margin:3px auto;border-radius:2px}
.illust-lines div:nth-child(2){width:55%}
.illust-img{width:60px;height:45px;background:#e3f2fd;border:2px dashed #90caf9;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:1.3rem}
.illust-row{display:flex;gap:4px;align-items:stretch}
.illust-box{background:#e3f2fd;border:1px solid #90caf9;border-radius:3px;display:flex;align-items:center;justify-content:center;font-size:.7rem;color:#1565c0}
.illust-lines-sm div{width:100%;height:2px;background:#bbb;margin:2px 0;border-radius:1px}
.illust-link{width:80%;border:2px solid #90caf9;border-radius:6px;padding:6px;text-align:left}
.illust-link div:first-child{height:3px;width:60%;background:#1565c0;border-radius:2px;margin-bottom:4px}
.illust-link div:last-child{height:2px;width:90%;background:#bbb;border-radius:2px}
#modulesList{margin:16px 0}
.module-card{background:#fff;border:2px solid var(--border);border-radius:10px;padding:16px;margin-bottom:14px;position:relative;transition:border-color .2s}
.module-card:hover{border-color:var(--primary)}
.module-card .module-type-label{font-size:.72rem;color:#888;text-transform:uppercase;font-weight:600;margin-bottom:8px}
.module-toolbar{display:flex;gap:4px;flex-wrap:wrap;margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid #f0f0f0;align-items:center}
.module-toolbar button,.module-toolbar label{padding:5px 10px;border:1px solid var(--border);border-radius:5px;cursor:pointer;font-size:.8rem;background:#fff;transition:background .2s}
.module-toolbar button:hover,.module-toolbar label:hover{background:#f5f5f5}
.module-toolbar button.active{background:var(--primary);color:#fff;border-color:var(--primary)}
.module-toolbar .tb-bold{font-weight:700}
.module-toolbar .tb-italic{font-style:italic}
.module-toolbar .tb-strike{text-decoration:line-through}
.module-toolbar .tb-under{text-decoration:underline}
.module-toolbar .tb-del{background:#ffebee;color:#c62828;border-color:#ef9a9a}
.module-toolbar .tb-del:hover{background:#c62828;color:#fff}
.module-toolbar .tb-edit{background:#e3f2fd;color:#1565c0;border-color:#90caf9}
.module-toolbar input[type=color]{width:32px;height:28px;border:1px solid var(--border);border-radius:5px;cursor:pointer;padding:0}
.module-content textarea{width:100%;min-height:100px;padding:10px;border:2px solid var(--border);border-radius:8px;font-family:inherit;font-size:.95rem;resize:vertical}
.module-content textarea:focus{border-color:var(--primary);outline:none}
.module-content .img-preview{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
.module-content .img-preview img{width:120px;height:90px;object-fit:cover;border-radius:6px;border:2px solid var(--border)}
.module-content .img-upload-area{border:2px dashed var(--border);border-radius:8px;padding:20px;text-align:center;cursor:pointer;margin-top:8px;transition:border-color .2s}
.module-content .img-upload-area:hover{border-color:var(--primary)}
.module-content .link-input{margin-top:8px}
.module-content .link-input input{width:100%;padding:8px 12px;border:2px solid var(--border);border-radius:8px;font-size:.9rem}
.module-content .link-input input:focus{border-color:var(--primary);outline:none}
.module-content .link-preview-box{border:2px solid var(--border);border-radius:8px;padding:14px;margin-top:8px;background:#f9f9f9}
.module-content .link-preview-box h4{color:var(--primary);margin-bottom:4px;font-size:.95rem}
.module-content .link-preview-box p{color:#666;font-size:.85rem;margin:0}
.module-text-preview{padding:8px 0;line-height:1.6;white-space:pre-wrap;word-wrap:break-word}
</style>
"""

CREATOR_JS = """
<script>
let modules = [];
const UPLOAD_URL = '/api/upload-image';
const LINK_PREVIEW_URL = '/api/link-preview';

const TYPE_LABELS = {
    'text': 'Nội dung',
    'image': 'Hình ảnh',
    'image_left_text': 'Hình trái + Nội dung phải',
    'image_right_text': 'Hình phải + Nội dung trái',
    'double_image': 'Hình ảnh đôi',
    'triple_image': 'Hình ảnh tam',
    'quad_image': 'Hình ảnh tứ',
    'link_preview': 'Trang khác'
};

const IMG_COUNTS = {
    'image': 1,
    'image_left_text': 1,
    'image_right_text': 1,
    'double_image': 2,
    'triple_image': 3,
    'quad_image': 4
};

function uid() { return 'mod_' + Math.random().toString(36).substr(2, 9); }

function addModule(type) {
    let mod = {
        id: uid(), type: type, content: '', images: [],
        link: {url:'', title:'', description:''},
        style: {color:'#000000', bold:false, italic:false, strikethrough:false, underline:false}
    };
    modules.push(mod);
    renderModules();
    closeAddModal();
}

function deleteModule(idx) {
    if(confirm('Xóa mục này?')) { modules.splice(idx, 1); renderModules(); }
}

function toggleStyle(idx, prop) {
    modules[idx].style[prop] = !modules[idx].style[prop];
    renderModules();
}

function updateColor(idx, val) {
    modules[idx].style.color = val;
    renderModules();
}

function updateContent(idx, val) {
    modules[idx].content = val;
}

function updateLinkUrl(idx) {
    let input = document.getElementById('link_url_'+idx);
    let url = input.value.trim();
    modules[idx].link.url = url;
    if(url) fetchLinkPreview(idx, url);
}

function fetchLinkPreview(idx, url) {
    fetch(LINK_PREVIEW_URL + '?url=' + encodeURIComponent(url))
    .then(r => r.json())
    .then(data => {
        modules[idx].link.title = data.title || url;
        modules[idx].link.description = data.description || '';
        renderModules();
    })
    .catch(() => {
        modules[idx].link.title = url;
        modules[idx].link.description = '';
        renderModules();
    });
}

function uploadImage(idx, imgIdx, fileInput) {
    let file = fileInput.files[0];
    if(!file) return;
    let ext = file.name.split('.').pop().toLowerCase();
    if(!['jpg','jpeg','png','webp'].includes(ext)) {
        alert('Chỉ hỗ trợ JPG, PNG, WebP');
        return;
    }
    let fd = new FormData();
    fd.append('image', file);
    fetch(UPLOAD_URL, {method:'POST', body:fd})
    .then(r => r.json())
    .then(data => {
        if(data.error) { alert(data.error); return; }
        while(modules[idx].images.length <= imgIdx) modules[idx].images.push('');
        modules[idx].images[imgIdx] = data.path;
        renderModules();
    })
    .catch(e => alert('Lỗi tải ảnh: '+e));
}

function openAddModal() { document.getElementById('addModalOverlay').classList.add('show'); }
function closeAddModal() { document.getElementById('addModalOverlay').classList.remove('show'); }

function renderModules() {
    let container = document.getElementById('modulesList');
    let html = '';
    modules.forEach((mod, idx) => {
        let s = mod.style;
        let boldActive = s.bold ? ' active' : '';
        let italicActive = s.italic ? ' active' : '';
        let strikeActive = s.strikethrough ? ' active' : '';
        let underActive = s.underline ? ' active' : '';

        html += '<div class="module-card">';
        html += '<div class="module-type-label">' + (TYPE_LABELS[mod.type]||mod.type) + '</div>';

        // Toolbar
        html += '<div class="module-toolbar">';
        html += '<input type="color" value="'+(s.color||'#000000')+'" onchange="updateColor('+idx+',this.value)" title="Sửa màu">';
        html += '<button type="button" class="tb-bold'+boldActive+'" onclick="toggleStyle('+idx+',\\'bold\\')" title="In đậm">B</button>';
        html += '<button type="button" class="tb-italic'+italicActive+'" onclick="toggleStyle('+idx+',\\'italic\\')" title="In nghiêng">I</button>';
        html += '<button type="button" class="tb-strike'+strikeActive+'" onclick="toggleStyle('+idx+',\\'strikethrough\\')" title="Gạch giữa">S</button>';
        html += '<button type="button" class="tb-under'+underActive+'" onclick="toggleStyle('+idx+',\\'underline\\')" title="Gạch chân">U</button>';
        html += '<button type="button" class="tb-del" onclick="deleteModule('+idx+')" title="Xóa">Xóa</button>';
        html += '</div>';

        // Content area
        html += '<div class="module-content">';

        if(mod.type === 'text') {
            html += '<textarea onchange="updateContent('+idx+',this.value)" placeholder="Nhập nội dung... Hỗ trợ [text](url) cho link">'+escHtml(mod.content)+'</textarea>';
        }
        else if(mod.type === 'link_preview') {
            html += '<div class="link-input"><input type="text" id="link_url_'+idx+'" value="'+escHtml(mod.link.url)+'" placeholder="Nhập URL trang..." onblur="updateLinkUrl('+idx+')"></div>';
            if(mod.link.title) {
                html += '<div class="link-preview-box"><h4>'+escHtml(mod.link.title)+'</h4><p>'+escHtml(mod.link.description)+'</p></div>';
            }
        }
        else {
            // Types with images
            let imgCount = IMG_COUNTS[mod.type] || 1;
            let hasText = mod.type === 'image_left_text' || mod.type === 'image_right_text';

            html += '<div class="img-preview">';
            for(let i=0; i<imgCount; i++) {
                if(mod.images[i]) {
                    html += '<img src="/'+escHtml(mod.images[i])+'" alt="">';
                }
            }
            html += '</div>';

            for(let i=0; i<imgCount; i++) {
                html += '<div class="img-upload-area">';
                html += '<input type="file" accept=".jpg,.jpeg,.png,.webp" onchange="uploadImage('+idx+','+i+',this)" style="width:100%">';
                html += '<div style="font-size:.8rem;color:#888;margin-top:4px">Hình '+(i+1)+' (JPG, PNG, WebP)</div>';
                html += '</div>';
            }

            if(hasText) {
                html += '<textarea onchange="updateContent('+idx+',this.value)" placeholder="Nhập nội dung..." style="margin-top:10px">'+escHtml(mod.content)+'</textarea>';
            }
        }

        html += '</div></div>';
    });
    container.innerHTML = html;
}

function escHtml(s) {
    if(!s) return '';
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function serializeModules() {
    document.getElementById('content_modules_input').value = JSON.stringify(modules);
    // Generate plain text content summary
    let summary = '';
    modules.forEach(m => {
        if(m.content) summary += m.content + '\\n';
        if(m.type === 'image') summary += '[Hình ảnh]\\n';
        if(m.type.includes('image') && m.type !== 'image') summary += '[Hình ảnh + Nội dung]\\n';
        if(m.type === 'link_preview') summary += '[Link: '+(m.link.title||m.link.url)+']\\n';
    });
    document.getElementById('content_input').value = summary.trim();
    return true;
}

function descCounter() {
    let ta = document.getElementById('desc_input');
    let counter = document.getElementById('desc_counter');
    let len = ta.value.length;
    counter.textContent = len + '/500';
    counter.className = 'desc-counter' + (len > 500 ? ' over' : '');
}

// Initialize modules from existing data (for edit mode)
function initModules(data) {
    try { modules = JSON.parse(data); } catch(e) { modules = []; }
    renderModules();
}
</script>
"""


@app.route("/creator", methods=["GET", "POST"])
@creator_required
def creator():
    db = get_baidang_db()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()[:500]
        content = request.form.get("content", "").strip()
        content_modules = request.form.get("content_modules", "[]")
        category = request.form.get("category", "Tin tức")
        is_published = 1 if request.form.get("is_published") else 0
        slug = slugify(title)
        if not title:
            flash("Vui lòng điền tiêu đề.", "warning")
        else:
            if db.execute("SELECT id FROM posts WHERE slug=?", (slug,)).fetchone():
                slug += "-" + secrets.token_hex(3)
            db.execute(
                "INSERT INTO posts (title,slug,description,content,content_modules,category,author_id,is_published) VALUES (?,?,?,?,?,?,?,?)",
                (title, slug, description, content, content_modules, category, session["user_id"], is_published),
            )
            db.commit()
            flash("Đăng bài thành công!", "success")
            return redirect(url_for("creator"))

    my_posts = db.execute(
        "SELECT * FROM posts WHERE author_id=? ORDER BY created_at DESC",
        (session["user_id"],),
    ).fetchall()
    rows = ""
    for p in my_posts:
        status = "Xuất bản" if p["is_published"] else "Nháp"
        rows += f"""<tr>
            <td><a href="{url_for('view_post', slug=p['slug'])}">{escape(p['title'])}</a></td>
            <td>{p['category']}</td><td>{p['created_at'][:16]}</td><td>{status}</td>
            <td>
                <a href="{url_for('edit_post', post_id=p['id'])}" class="btn btn-sm btn-outline">Sửa</a>
                <form method="POST" action="{url_for('delete_post', post_id=p['id'])}" style="display:inline">
                    <button type="submit" class="btn btn-sm btn-danger" onclick="return confirm('Xóa bài viết này?')">Xóa</button>
                </form>
            </td></tr>"""
    post_table = ""
    if my_posts:
        post_table = f"""<div style="margin-top:32px">
            <div class="section-title" style="font-size:1rem">Bài đăng của bạn</div>
            <div class="table-wrapper"><table>
                <thead><tr><th>Tiêu đề</th><th>Mục</th><th>Ngày tạo</th><th>Trạng thái</th><th>Hành động</th></tr></thead>
                <tbody>{rows}</tbody>
            </table></div></div>"""

    cats = "".join(f'<option value="{c}">{c}</option>' for c in CATEGORIES)

    body = f"""{CREATOR_CSS}
    <main>
    <div class="form-container wide">
        <h2>&#9997; Tạo bài đăng mới</h2>
        <form method="POST" onsubmit="return serializeModules()">
            <div class="form-group"><label>Tiêu đề</label><input type="text" name="title" required placeholder="Nhập tiêu đề bài viết"></div>
            <div class="form-group">
                <label>Miêu tả <span style="font-weight:400;color:#888">(Giới hạn 500 ký tự)</span></label>
                <textarea name="description" id="desc_input" maxlength="500" placeholder="Nhập miêu tả bài viết..." style="min-height:80px" oninput="descCounter()"></textarea>
                <div class="desc-counter" id="desc_counter">0/500</div>
            </div>
            <div class="form-group"><label>Mục</label><select name="category">{cats}</select></div>

            <div class="section-title" style="font-size:1rem;margin-top:24px">Nội dung bài đăng</div>
            <div class="builder-toolbar">
                <button type="button" class="btn-add" onclick="openAddModal()">&#43; Add</button>
            </div>

            <div id="modulesList"></div>

            <input type="hidden" name="content_modules" id="content_modules_input" value="[]">
            <input type="hidden" name="content" id="content_input" value="">

            <div class="form-group"><label class="cb-label"><input type="checkbox" name="is_published" value="1" checked> Xuất bản ngay</label></div>
            <button type="submit" class="btn btn-full">Đăng bài</button>
        </form>
        {post_table}
    </div></main>

    <div class="add-modal-overlay" id="addModalOverlay" onclick="if(event.target===this)closeAddModal()">
        <div class="add-modal">
            <h3>Chọn loại nội dung</h3>
            <div class="module-options">
                <div class="module-option" onclick="addModule('text')">
                    <div class="illust"><div class="illust-lines"><div></div><div></div><div></div></div></div>
                    <span>Nội dung</span>
                </div>
                <div class="module-option" onclick="addModule('image')">
                    <div class="illust"><div class="illust-img">&#128247;</div></div>
                    <span>Hình ảnh</span>
                </div>
                <div class="module-option" onclick="addModule('image_left_text')">
                    <div class="illust"><div class="illust-row"><div class="illust-box" style="width:30px;height:40px">&#128247;</div><div class="illust-lines-sm" style="flex:1;padding-top:4px"><div></div><div></div><div></div></div></div></div>
                    <span>Hình trái<br>Nội dung phải</span>
                </div>
                <div class="module-option" onclick="addModule('image_right_text')">
                    <div class="illust"><div class="illust-row"><div class="illust-lines-sm" style="flex:1;padding-top:4px"><div></div><div></div><div></div></div><div class="illust-box" style="width:30px;height:40px">&#128247;</div></div></div>
                    <span>Nội dung trái<br>Hình phải</span>
                </div>
                <div class="module-option" onclick="addModule('double_image')">
                    <div class="illust"><div class="illust-row"><div class="illust-box" style="width:30px;height:35px">&#128247;</div><div class="illust-box" style="width:30px;height:35px">&#128247;</div></div></div>
                    <span>Hình ảnh đôi</span>
                </div>
                <div class="module-option" onclick="addModule('triple_image')">
                    <div class="illust"><div class="illust-row"><div class="illust-box" style="width:22px;height:30px">&#128247;</div><div class="illust-box" style="width:22px;height:30px">&#128247;</div><div class="illust-box" style="width:22px;height:30px">&#128247;</div></div></div>
                    <span>Hình ảnh tam</span>
                </div>
                <div class="module-option" onclick="addModule('quad_image')">
                    <div class="illust"><div style="display:grid;grid-template-columns:1fr 1fr;gap:3px"><div class="illust-box" style="width:22px;height:20px">&#128247;</div><div class="illust-box" style="width:22px;height:20px">&#128247;</div><div class="illust-box" style="width:22px;height:20px">&#128247;</div><div class="illust-box" style="width:22px;height:20px">&#128247;</div></div></div>
                    <span>Hình ảnh tứ</span>
                </div>
                <div class="module-option" onclick="addModule('link_preview')">
                    <div class="illust"><div class="illust-link"><div></div><div></div></div></div>
                    <span>Trang khác</span>
                </div>
            </div>
            <div style="text-align:center;margin-top:20px">
                <button type="button" class="btn btn-outline" onclick="closeAddModal()">Đóng</button>
            </div>
        </div>
    </div>
    {CREATOR_JS}"""
    return render_page("Tạo bài đăng", body)


@app.route("/creator/edit/<int:post_id>", methods=["GET", "POST"])
@creator_required
def edit_post(post_id):
    db = get_baidang_db()
    post = db.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()
    if not post:
        abort(404)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()[:500]
        content = request.form.get("content", "").strip()
        content_modules = request.form.get("content_modules", "[]")
        category = request.form.get("category", "Tin tức")
        is_published = 1 if request.form.get("is_published") else 0
        db.execute(
            "UPDATE posts SET title=?,description=?,content=?,content_modules=?,category=?,is_published=?,updated_at=datetime('now') WHERE id=?",
            (title, description, content, content_modules, category, is_published, post_id),
        )
        db.commit()
        flash("Cập nhật thành công!", "success")
        return redirect(url_for("creator"))

    cats = "".join(
        f'<option value="{c}" {"selected" if post["category"]==c else ""}>{c}</option>'
        for c in CATEGORIES
    )
    checked = "checked" if post["is_published"] else ""
    desc_val = str(escape(post["description"])) if post["description"] else ""
    modules_json = post["content_modules"] if post["content_modules"] else "[]"
    modules_escaped = str(escape(modules_json))

    body = f"""{CREATOR_CSS}
    <main>
    <div class="form-container wide">
        <h2>&#9997; Chỉnh sửa bài đăng</h2>
        <form method="POST" onsubmit="return serializeModules()">
            <div class="form-group"><label>Tiêu đề</label><input type="text" name="title" required value="{escape(post['title'])}"></div>
            <div class="form-group">
                <label>Miêu tả <span style="font-weight:400;color:#888">(Giới hạn 500 ký tự)</span></label>
                <textarea name="description" id="desc_input" maxlength="500" style="min-height:80px" oninput="descCounter()">{desc_val}</textarea>
                <div class="desc-counter" id="desc_counter">{len(post['description'] or '')}/500</div>
            </div>
            <div class="form-group"><label>Mục</label><select name="category">{cats}</select></div>

            <div class="section-title" style="font-size:1rem;margin-top:24px">Nội dung bài đăng</div>
            <div class="builder-toolbar">
                <button type="button" class="btn-add" onclick="openAddModal()">&#43; Add</button>
            </div>
            <div id="modulesList"></div>
            <input type="hidden" name="content_modules" id="content_modules_input" value="">
            <input type="hidden" name="content" id="content_input" value="{escape(post['content'])}">

            <div class="form-group"><label class="cb-label"><input type="checkbox" name="is_published" value="1" {checked}> Xuất bản</label></div>
            <button type="submit" class="btn btn-full">Cập nhật</button>
        </form>
    </div></main>

    <div class="add-modal-overlay" id="addModalOverlay" onclick="if(event.target===this)closeAddModal()">
        <div class="add-modal">
            <h3>Chọn loại nội dung</h3>
            <div class="module-options">
                <div class="module-option" onclick="addModule('text')"><div class="illust"><div class="illust-lines"><div></div><div></div><div></div></div></div><span>Nội dung</span></div>
                <div class="module-option" onclick="addModule('image')"><div class="illust"><div class="illust-img">&#128247;</div></div><span>Hình ảnh</span></div>
                <div class="module-option" onclick="addModule('image_left_text')"><div class="illust"><div class="illust-row"><div class="illust-box" style="width:30px;height:40px">&#128247;</div><div class="illust-lines-sm" style="flex:1;padding-top:4px"><div></div><div></div><div></div></div></div></div><span>Hình trái + Nội dung phải</span></div>
                <div class="module-option" onclick="addModule('image_right_text')"><div class="illust"><div class="illust-row"><div class="illust-lines-sm" style="flex:1;padding-top:4px"><div></div><div></div><div></div></div><div class="illust-box" style="width:30px;height:40px">&#128247;</div></div></div><span>Nội dung trái + Hình phải</span></div>
                <div class="module-option" onclick="addModule('double_image')"><div class="illust"><div class="illust-row"><div class="illust-box" style="width:30px;height:35px">&#128247;</div><div class="illust-box" style="width:30px;height:35px">&#128247;</div></div></div><span>Hình ảnh đôi</span></div>
                <div class="module-option" onclick="addModule('triple_image')"><div class="illust"><div class="illust-row"><div class="illust-box" style="width:22px;height:30px">&#128247;</div><div class="illust-box" style="width:22px;height:30px">&#128247;</div><div class="illust-box" style="width:22px;height:30px">&#128247;</div></div></div><span>Hình ảnh tam</span></div>
                <div class="module-option" onclick="addModule('quad_image')"><div class="illust"><div style="display:grid;grid-template-columns:1fr 1fr;gap:3px"><div class="illust-box" style="width:22px;height:20px">&#128247;</div><div class="illust-box" style="width:22px;height:20px">&#128247;</div><div class="illust-box" style="width:22px;height:20px">&#128247;</div><div class="illust-box" style="width:22px;height:20px">&#128247;</div></div></div><span>Hình ảnh tứ</span></div>
                <div class="module-option" onclick="addModule('link_preview')"><div class="illust"><div class="illust-link"><div></div><div></div></div></div><span>Trang khác</span></div>
            </div>
            <div style="text-align:center;margin-top:20px"><button type="button" class="btn btn-outline" onclick="closeAddModal()">Đóng</button></div>
        </div>
    </div>
    {CREATOR_JS}
    <script>initModules({modules_escaped!r});</script>"""
    return render_page("Sửa bài đăng", body)


@app.route("/creator/delete/<int:post_id>", methods=["POST"])
@creator_required
def delete_post(post_id):
    db = get_baidang_db()
    db.execute("DELETE FROM posts WHERE id=?", (post_id,))
    db.commit()
    flash("Đã xóa bài viết.", "success")
    return redirect(url_for("creator"))


# ═══════════════════════════════════════════════════════════════════════════
# API - Image Upload
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/api/upload-image", methods=["POST"])
@login_required
def upload_image():
    if "image" not in request.files:
        return jsonify({"error": "Không có file"}), 400
    f = request.files["image"]
    if f.filename == "":
        return jsonify({"error": "Không có file"}), 400
    ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "Chỉ hỗ trợ JPG, PNG, WebP"}), 400
    filename = f"{uuid.uuid4().hex}.{ext}"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filepath = os.path.join(UPLOAD_DIR, filename)
    f.save(filepath)
    rel_path = f"Hinhanh/baidang/{filename}"
    return jsonify({"path": rel_path, "filename": filename})


@app.route("/Hinhanh/<path:filename>")
def serve_image(filename):
    return send_from_directory(os.path.join(BASE_DIR, "Hinhanh"), filename)


# ═══════════════════════════════════════════════════════════════════════════
# API - Link Preview
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/api/link-preview")
@login_required
def link_preview():
    url = request.args.get("url", "")
    if not url:
        return jsonify({"title": "", "description": ""})
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 HNPP Bot"})
        with urlopen(req, timeout=5) as resp:
            html = resp.read(50000).decode("utf-8", errors="ignore")
        title = ""
        desc = ""
        tm = re.search(r"<title[^>]*>([^<]+)</title>", html, re.I)
        if tm:
            title = tm.group(1).strip()
        dm = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)', html, re.I)
        if not dm:
            dm = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']description["\']', html, re.I)
        if dm:
            desc = dm.group(1).strip()
        return jsonify({"title": title, "description": desc, "url": url})
    except Exception:
        return jsonify({"title": url, "description": "", "url": url})


# ═══════════════════════════════════════════════════════════════════════════
# 5. BAI DANG
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/baidang")
def list_posts():
    db = get_baidang_db()
    cat = request.args.get("cat")
    if cat:
        posts = db.execute(
            "SELECT * FROM posts WHERE is_published=1 AND category=? ORDER BY created_at DESC",
            (cat,),
        ).fetchall()
    else:
        posts = db.execute(
            "SELECT * FROM posts WHERE is_published=1 ORDER BY created_at DESC"
        ).fetchall()

    cards = ""
    for p in posts:
        raw = p["description"] or p["content"]
        snippet = str(escape(raw[:200])) + ("..." if len(raw) > 200 else "")
        cards += f"""<div class="card">
            <h3><a href="{url_for('view_post', slug=p['slug'])}">{escape(p['title'])}</a></h3>
            <p>{snippet}</p>
            <div class="meta"><span class="badge badge-user">{p['category']}</span> &bull; {p['created_at'][:16]}</div>
        </div>"""
    if not posts:
        cards = '<div class="page-content"><p>Chưa có bài đăng nào.</p></div>'

    cat_links = "".join(f'<li><a href="?cat={c}">{c}</a></li>' for c in CATEGORIES)

    body = f"""
    <div class="banner" style="padding:32px 16px 28px">
        <h1>Bài đăng</h1>
        <p>Tất cả bài viết và tin tức từ HNPP</p>
    </div>
    <main>
        <div class="two-col">
            <div>
                <div class="card-grid" style="grid-template-columns:1fr">{cards}</div>
            </div>
            <div class="sidebar">
                <div class="widget">
                    <h4>Mục</h4>
                    <ul>{cat_links}</ul>
                </div>
            </div>
        </div>
    </main>"""
    return render_page("Bài đăng", body)


@app.route("/baidang/<slug>")
def view_post(slug):
    db = get_baidang_db()
    post = db.execute(
        "SELECT * FROM posts WHERE slug=? AND is_published=1", (slug,)
    ).fetchone()
    if not post:
        abort(404)
    author = get_account_db().execute(
        "SELECT * FROM users WHERE id=?", (post["author_id"],)
    ).fetchone()
    author_name = author["display_name"] if author else "N/A"

    # Render content: prefer modules, fall back to content field
    modules_html = render_modules_html(post["content_modules"])
    if not modules_html:
        content_html = render_text_with_links(post["content"]) if post["content"] else ""
    else:
        content_html = modules_html

    desc_html = ""
    if post["description"]:
        desc_html = f'<div class="post-desc">{escape(post["description"])}</div>'

    body = f"""<main>
    <div class="page-content" style="max-width:860px;margin:24px auto">
        <div class="post-header">
            <h1>{escape(post['title'])}</h1>
            <div class="post-meta">
                <span class="badge badge-user">{post['category']}</span>
                &bull; Đăng ngày {post['created_at'][:16]}
                &bull; Tác giả: {author_name}
            </div>
        </div>
        {desc_html}
        <hr style="border:none;border-top:2px solid var(--accent);margin:16px 0">
        <div class="post-body">{content_html}</div>
        <hr style="border:none;border-top:1px solid #eee;margin:24px 0">
        <a href="{{{{URL_POSTS}}}}" class="btn btn-outline">&larr; Quay lại danh sách</a>
    </div></main>"""
    return render_page(str(escape(post["title"])), body)


# ═══════════════════════════════════════════════════════════════════════════
# 6. PASSWORD PAGE (Headadmins only)
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/password/")
def password_page():
    key = request.args.get("key", "")
    passw = request.args.get("pass", "")
    if key != PASSWORD_PAGE_KEY or passw != PASSWORD_PAGE_PASS:
        abort(404)

    user = get_current_user()
    if not user or user["role"] != "headadmin":
        abort(404)

    db = get_account_db()
    users = db.execute(
        "SELECT * FROM users WHERE role != 'headadmin' ORDER BY id"
    ).fetchall()

    rows = ""
    for u in users:
        try:
            pw = decrypt_password(u["password_enc"])
        except Exception:
            pw = "[Không thể giải mã]"
        badge_cls = f"badge-{u['role']}"
        label = ROLE_LABELS.get(u["role"], u["role"])
        rows += f"""<tr>
            <td>{u['id']}</td>
            <td>{escape(u['username'])}</td>
            <td>{escape(u['display_name'])}</td>
            <td><span class="badge {badge_cls}">{label}</span></td>
            <td><code>{escape(pw)}</code></td>
            <td>{u['created_at'][:16]}</td>
        </tr>"""

    body = f"""<main>
    <div class="page-content" style="max-width:960px;margin:24px auto">
        <h1>&#128274; Quản lý mật khẩu</h1>
        <p style="color:#888;margin-bottom:20px">Chỉ Headadmins mới có quyền xem trang này. Không hiển thị tài khoản Headadmin.</p>
        <div class="table-wrapper"><table>
            <thead><tr><th>ID</th><th>Username</th><th>Tên</th><th>Quyền</th><th>Mật khẩu</th><th>Ngày tạo</th></tr></thead>
            <tbody>{rows}</tbody>
        </table></div>
    </div></main>"""
    return render_page("Quản lý mật khẩu", body)


# ═══════════════════════════════════════════════════════════════════════════
# 7. TOS
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/tos")
def tos():
    body = """<main>
    <div class="page-content" style="max-width:860px;margin:24px auto">
        <h1>Điều khoản sử dụng</h1>
        <h2>1. Giới thiệu</h2>
        <p>Chào mừng bạn đến với Cổng thông tin HNPP - Hanoi Academy People's Police. Bằng việc truy cập và sử dụng website này, bạn đồng ý tuân thủ các điều khoản và điều kiện sau đây.</p>
        <h2>2. Quyền và nghĩa vụ của người dùng</h2>
        <ul>
            <li>Người dùng phải cung cấp thông tin chính xác khi đăng ký tài khoản.</li>
            <li>Không sử dụng website cho mục đích bất hợp pháp.</li>
            <li>Không chia sẻ tài khoản với người khác.</li>
            <li>Tuân thủ mọi quy định và luật lệ của HNPP.</li>
        </ul>
        <h2>3. Quyền sở hữu trí tuệ</h2>
        <p>Tất cả nội dung trên website bao gồm văn bản, hình ảnh, logo, thiết kế đều thuộc quyền sở hữu của HNPP. Nghiêm cấm sao chép, phân phối mà không có sự cho phép bằng văn bản.</p>
        <h2>4. Giới hạn trách nhiệm</h2>
        <p>HNPP không chịu trách nhiệm cho bất kỳ thiệt hại trực tiếp hoặc gián tiếp nào phát sinh từ việc sử dụng hoặc không thể sử dụng dịch vụ.</p>
        <h2>5. Thay đổi điều khoản</h2>
        <p>HNPP có quyền thay đổi các điều khoản này bất kỳ lúc nào. Các thay đổi sẽ có hiệu lực ngay khi được đăng trên website.</p>
        <h2>6. Liên hệ</h2>
        <p>Nếu bạn có bất kỳ câu hỏi nào về Điều khoản sử dụng, vui lòng liên hệ qua trang <a href="{{URL_SUPPORT}}">Hỗ trợ</a>.</p>
    </div></main>"""
    return render_page("Điều khoản sử dụng", body)


# ═══════════════════════════════════════════════════════════════════════════
# 8. CHINH SACH
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/chinh-sach")
def chinh_sach():
    body = """<main>
    <div class="page-content" style="max-width:860px;margin:24px auto">
        <h1>Chính sách bảo mật</h1>
        <h2>1. Thu thập thông tin</h2>
        <p>Chúng tôi thu thập thông tin cá nhân khi bạn đăng ký tài khoản, bao gồm: tên đăng nhập, tên hiển thị. Chúng tôi cam kết bảo vệ thông tin của bạn.</p>
        <h2>2. Sử dụng thông tin</h2>
        <ul>
            <li>Xác thực và quản lý tài khoản người dùng.</li>
            <li>Cải thiện chất lượng dịch vụ.</li>
            <li>Gửi thông báo quan trọng liên quan đến hệ thống.</li>
        </ul>
        <h2>3. Bảo mật thông tin</h2>
        <p>Chúng tôi áp dụng các biện pháp bảo mật hợp lý để bảo vệ thông tin cá nhân của bạn khỏi truy cập trái phép, sử dụng sai mục đích hoặc tiết lộ. Mật khẩu được mã hóa một chiều, không thể giải mã ngược.</p>
        <h2>4. Chia sẻ thông tin</h2>
        <p>Chúng tôi không chia sẻ thông tin cá nhân của bạn với bên thứ ba, trừ khi được yêu cầu bởi pháp luật hoặc được sự đồng ý của bạn.</p>
        <h2>5. Cookie</h2>
        <p>Website sử dụng cookie phiên (session) để duy trì trạng thái đăng nhập. Bạn có thể tắt cookie trong trình duyệt nhưng điều này có thể ảnh hưởng đến trải nghiệm sử dụng.</p>
        <h2>6. Cập nhật chính sách</h2>
        <p>Chính sách bảo mật có thể được cập nhật theo thời gian. Mọi thay đổi sẽ được thông báo trên website.</p>
    </div></main>"""
    return render_page("Chính sách bảo mật", body)


# ═══════════════════════════════════════════════════════════════════════════
# 9. BAN QUYEN
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/ban-quyen")
def ban_quyen():
    year = datetime.now(timezone.utc).year
    body = f"""<main>
    <div class="page-content" style="max-width:860px;margin:24px auto">
        <h1>Bản quyền</h1>
        <h2>Quyền sở hữu</h2>
        <p>Tất cả nội dung, hình ảnh, thiết kế, mã nguồn và tài liệu trên website HNPP đều thuộc quyền sở hữu trí tuệ của <strong>Hanoi Academy People's Police (HNPP)</strong>.</p>
        <h2>Quy định sử dụng</h2>
        <ul>
            <li>Nghiêm cấm sao chép, tái sử dụng hoặc phân phối nội dung mà không có sự cho phép bằng văn bản.</li>
            <li>Việc trích dẫn nội dung phải ghi rõ nguồn và liên kết đến trang gốc.</li>
            <li>Sử dụng logo, thương hiệu HNPP cho mục đích thương mại là vi phạm pháp luật.</li>
        </ul>
        <h2>Báo cáo vi phạm</h2>
        <p>Nếu bạn phát hiện nội dung vi phạm bản quyền, vui lòng liên hệ qua trang <a href="{{{{URL_SUPPORT}}}}">Hỗ trợ</a> để chúng tôi xử lý kịp thời.</p>
        <div style="background:#fff8e1;padding:20px;border-radius:8px;border-left:4px solid var(--accent);margin-top:24px">
            <strong>&copy; {year} HNPP - Hanoi Academy People's Police.</strong><br>
            Mọi quyền được bảo lưu theo quy định pháp luật Việt Nam.
        </div>
    </div></main>"""
    return render_page("Bản quyền", body)


# ═══════════════════════════════════════════════════════════════════════════
# 10. LUAT HNPP
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/luat-hnpp")
def luat_hnpp():
    body = """
    <div class="banner" style="padding:32px 16px 28px">
        <h1>&#9878; Luật HNPP</h1>
        <p>Các quy định và luật lệ chính thức của Hanoi Academy People's Police</p>
    </div>
    <main>
    <div class="page-content" style="max-width:860px;margin:24px auto">
        <h2>CHƯƠNG I: QUY ĐỊNH CHUNG</h2>
        <h3>Điều 1. Phạm vi điều chỉnh</h3>
        <p>Luật này quy định về tổ chức, hoạt động, quyền hạn và trách nhiệm của các thành viên trong hệ thống HNPP - Hanoi Academy People's Police.</p>
        <h3>Điều 2. Đối tượng áp dụng</h3>
        <p>Luật áp dụng cho tất cả thành viên, quản trị viên và người dùng tham gia vào hệ thống HNPP.</p>
        <h3>Điều 3. Nguyên tắc hoạt động</h3>
        <ol>
            <li>Tuân thủ pháp luật Việt Nam và quy định nội bộ của HNPP.</li>
            <li>Hoạt động minh bạch, công bằng và dân chủ.</li>
            <li>Tôn trọng quyền và lợi ích hợp pháp của mọi thành viên.</li>
            <li>Bảo vệ thông tin cá nhân và dữ liệu của hệ thống.</li>
        </ol>
        <h2>CHƯƠNG II: QUYỀN VÀ NGHĨA VỤ</h2>
        <h3>Điều 4. Quyền của thành viên</h3>
        <ol>
            <li>Được truy cập và sử dụng các tính năng của hệ thống theo quyền hạn được cấp.</li>
            <li>Được bảo vệ thông tin cá nhân theo Chính sách bảo mật.</li>
            <li>Được đóng góp ý kiến, phản hồi để cải thiện hệ thống.</li>
            <li>Được tham gia các hoạt động, sự kiện do HNPP tổ chức.</li>
        </ol>
        <h3>Điều 5. Nghĩa vụ của thành viên</h3>
        <ol>
            <li>Tuân thủ Điều khoản sử dụng và các quy định của HNPP.</li>
            <li>Không gây rối, phá hoại hoặc làm ảnh hưởng đến hoạt động bình thường của hệ thống.</li>
            <li>Không tuyên truyền, phát tán thông tin sai lệch hoặc gây hại.</li>
            <li>Bảo mật tài khoản cá nhân, không chia sẻ thông tin đăng nhập.</li>
        </ol>
        <h2>CHƯƠNG III: XỬ LÝ VI PHẠM</h2>
        <h3>Điều 6. Các hành vi vi phạm</h3>
        <ol>
            <li>Vi phạm Điều khoản sử dụng hoặc Chính sách bảo mật.</li>
            <li>Gây rối, spam, quấy rối thành viên khác.</li>
            <li>Sử dụng phần mềm, công cụ gây hại cho hệ thống.</li>
            <li>Giả mạo thông tin hoặc danh tính.</li>
        </ol>
        <h3>Điều 7. Hình thức xử lý</h3>
        <ol>
            <li><strong>Cảnh cáo:</strong> Áp dụng cho lần vi phạm đầu tiên với mức độ nhẹ.</li>
            <li><strong>Tạm khóa tài khoản:</strong> Từ 1-30 ngày tùy mức độ vi phạm.</li>
            <li><strong>Khóa vĩnh viễn:</strong> Áp dụng cho vi phạm nghiêm trọng hoặc tái phạm nhiều lần.</li>
        </ol>
        <h2>CHƯƠNG IV: ĐIỀU KHOẢN THI HÀNH</h2>
        <h3>Điều 8. Hiệu lực</h3>
        <p>Luật này có hiệu lực kể từ ngày ban hành. Mọi thay đổi sẽ được thông báo trên website chính thức.</p>
        <h3>Điều 9. Sửa đổi, bổ sung</h3>
        <p>Ban quản trị HNPP có quyền sửa đổi, bổ sung Luật này khi cần thiết. Các phiên bản cập nhật sẽ được đăng tải công khai.</p>
    </div></main>"""
    return render_page("Luật HNPP", body)


# ═══════════════════════════════════════════════════════════════════════════
# 11. SUPPORT
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/support")
def support():
    body = """<main>
    <div class="page-content" style="max-width:860px;margin:24px auto">
        <h1>&#128172; Hỗ trợ</h1>
        <p>Nếu bạn cần hỗ trợ hoặc có câu hỏi, vui lòng sử dụng các kênh liên hệ sau:</p>
        <div class="card-grid" style="margin-top:24px">
            <div class="card" style="text-align:center"><div style="font-size:2.5rem">&#128231;</div><h3>Email</h3><p>support@hnpp.vn</p></div>
            <div class="card" style="text-align:center"><div style="font-size:2.5rem">&#128222;</div><h3>Hotline</h3><p>1900-HNPP (24/7)</p></div>
            <div class="card" style="text-align:center"><div style="font-size:2.5rem">&#127760;</div><h3>Website</h3><p>www.hnpp.vn</p></div>
        </div>
        <h2 style="margin-top:32px">Câu hỏi thường gặp (FAQ)</h2>
        <div style="margin-top:16px">
            <details><summary>Làm thế nào để đăng nhập?</summary><p style="margin-top:8px">Bạn cần có tài khoản được tạo sẵn bởi quản trị viên. Liên hệ Admin để được cấp tài khoản.</p></details>
            <details><summary>Tôi quên mật khẩu, phải làm sao?</summary><p style="margin-top:8px">Vui lòng liên hệ quản trị viên để được đặt lại mật khẩu.</p></details>
            <details><summary>Làm sao để đăng bài viết?</summary><p style="margin-top:8px">Tài khoản có quyền Creators trở lên mới có quyền đăng bài. Truy cập trang Tạo bài đăng để bắt đầu.</p></details>
            <details><summary>Website có hỗ trợ mobile không?</summary><p style="margin-top:8px">Có! Website được thiết kế responsive, tương thích với tất cả thiết bị di động.</p></details>
        </div>
    </div></main>"""
    return render_page("Hỗ trợ", body)


# ═══════════════════════════════════════════════════════════════════════════
# 12. ADMIN
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/admin")
@admin_required
def admin_panel():
    db = get_baidang_db()
    pc = db.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    uc = get_account_db().execute("SELECT COUNT(*) FROM users").fetchone()[0]
    pub = db.execute("SELECT COUNT(*) FROM posts WHERE is_published=1").fetchone()[0]
    draft = db.execute("SELECT COUNT(*) FROM posts WHERE is_published=0").fetchone()[0]
    all_posts = db.execute(
        "SELECT * FROM posts ORDER BY created_at DESC"
    ).fetchall()

    rows = ""
    acc_db = get_account_db()
    for p in all_posts:
        author = acc_db.execute(
            "SELECT display_name FROM users WHERE id=?", (p["author_id"],)
        ).fetchone()
        author_name = author["display_name"] if author else "N/A"
        status = "Xuất bản" if p["is_published"] else "Nháp"
        rows += f"""<tr>
            <td>{p['id']}</td>
            <td><a href="{url_for('view_post', slug=p['slug'])}">{escape(p['title'])}</a></td>
            <td>{p['category']}</td><td>{author_name}</td>
            <td>{p['created_at'][:16]}</td><td>{status}</td></tr>"""

    body = f"""<main>
    <div class="page-content" style="max-width:960px;margin:24px auto">
        <h1>&#128736; Bảng điều khiển Admin</h1>
        <div class="stats-bar">
            <div class="stat-item"><div class="num">{pc}</div><div class="label">Bài đăng</div></div>
            <div class="stat-item"><div class="num">{uc}</div><div class="label">Tài khoản</div></div>
            <div class="stat-item"><div class="num">{pub}</div><div class="label">Đã xuất bản</div></div>
            <div class="stat-item"><div class="num">{draft}</div><div class="label">Nháp</div></div>
        </div>
        <div class="card-grid" style="margin-top:24px">
            <div class="card"><h3>Tạo bài đăng</h3><p>Viết và xuất bản bài viết mới trên website.</p>
                <a href="{{{{URL_CREATOR}}}}" class="btn btn-sm" style="margin-top:12px">Tạo bài &rarr;</a></div>
            <div class="card"><h3>Quản lý bài đăng</h3><p>Xem, sửa, xóa tất cả bài viết trên hệ thống.</p>
                <a href="{{{{URL_CREATOR}}}}" class="btn btn-sm btn-outline" style="margin-top:12px">Quản lý &rarr;</a></div>
        </div>
        <div style="margin-top:32px">
            <div class="section-title">Tất cả bài đăng</div>
            <div class="table-wrapper"><table>
                <thead><tr><th>ID</th><th>Tiêu đề</th><th>Mục</th><th>Tác giả</th><th>Ngày tạo</th><th>Trạng thái</th></tr></thead>
                <tbody>{rows}</tbody>
            </table></div>
        </div>
    </div></main>"""
    return render_page("Admin", body)


# ═══════════════════════════════════════════════════════════════════════════
# 13. GROUP GAME
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/group-game")
def group_game():
    db = get_baidang_db()
    game_posts = db.execute(
        "SELECT * FROM posts WHERE is_published=1 AND category='Group Game' ORDER BY created_at DESC"
    ).fetchall()

    post_cards = ""
    if game_posts:
        for p in game_posts:
            snippet = str(escape(p["content"][:150])) + ("..." if len(p["content"]) > 150 else "")
            post_cards += f"""<div class="card">
                <h3><a href="{url_for('view_post', slug=p['slug'])}">{escape(p['title'])}</a></h3>
                <p>{snippet}</p>
                <div class="meta">{p['created_at'][:16]}</div>
            </div>"""
    else:
        post_cards = '<p style="color:#888">Chưa có bài viết nào trong mục Group Game.</p>'

    body = f"""
    <div class="banner" style="padding:32px 16px 28px">
        <h1>&#127918; Group Game</h1>
        <p>Cộng đồng game và giải trí của HNPP</p>
    </div>
    <main>
    <div class="page-content" style="max-width:960px;margin:24px auto">
        <h2>Chào mừng đến với Group Game HNPP!</h2>
        <p>Đây là không gian giải trí dành cho các thành viên của Hanoi Academy People's Police. Cùng nhau chơi game, kết nối và xây dựng cộng đồng!</p>
        <div class="card-grid" style="margin-top:24px">
            <div class="card" style="text-align:center;border-left-color:var(--accent)"><div style="font-size:3rem">&#9876;</div><h3>Roleplay</h3><p>Tham gia các sự kiện roleplay hấp dẫn cùng cộng đồng HNPP.</p></div>
            <div class="card" style="text-align:center;border-left-color:#1565c0"><div style="font-size:3rem">&#127942;</div><h3>Giải đấu</h3><p>Các giải đấu game theo mùa với phần thưởng hấp dẫn.</p></div>
            <div class="card" style="text-align:center;border-left-color:#2e7d32"><div style="font-size:3rem">&#129309;</div><h3>Kết nối</h3><p>Gặp gỡ và kết bạn với các thành viên khác trong cộng đồng.</p></div>
            <div class="card" style="text-align:center;border-left-color:#e65100"><div style="font-size:3rem">&#128302;</div><h3>Mini Game</h3><p>Các trò chơi nhỏ giải trí trong lúc nghỉ ngơi.</p></div>
        </div>
        <div style="margin-top:32px">
            <div class="section-title">Quy định Group Game</div>
            <ol style="margin-left:20px">
                <li>Tôn trọng lẫn nhau, không gây gổ hoặc xúc phạm.</li>
                <li>Không sử dụng hack, cheat hoặc bất kỳ phần mềm gian lận nào.</li>
                <li>Tuân thủ quy định của từng game và sự kiện.</li>
                <li>Báo cáo vi phạm cho Admin thông qua trang <a href="{{{{URL_SUPPORT}}}}">Hỗ trợ</a>.</li>
                <li>Có tinh thần thể thao, fair play trong mọi hoạt động.</li>
            </ol>
        </div>
        <div style="margin-top:32px">
            <div class="section-title">Bài viết về Game</div>
            <div class="card-grid" style="grid-template-columns:1fr">{post_cards}</div>
        </div>
    </div></main>"""
    return render_page("Group Game", body)


# ═══════════════════════════════════════════════════════════════════════════
# ERROR HANDLERS
# ═══════════════════════════════════════════════════════════════════════════

@app.errorhandler(404)
def page_not_found(e):
    body = """<main>
    <div class="page-content" style="max-width:600px;margin:60px auto;text-align:center">
        <div style="font-size:5rem;color:var(--primary)">404</div>
        <h1>Không tìm thấy trang</h1>
        <p style="margin-top:16px;color:#888">Trang bạn đang tìm kiếm không tồn tại hoặc đã bị xóa.</p>
        <a href="{{URL_HOME}}" class="btn" style="margin-top:24px">Về trang chủ</a>
    </div></main>"""
    return render_page("404", body, 404)


@app.errorhandler(403)
def forbidden(e):
    body = """<main>
    <div class="page-content" style="max-width:600px;margin:60px auto;text-align:center">
        <div style="font-size:5rem;color:var(--primary)">403</div>
        <h1>Truy cập bị từ chối</h1>
        <p style="margin-top:16px;color:#888">Bạn không có quyền truy cập trang này.</p>
        <a href="{{URL_HOME}}" class="btn" style="margin-top:24px">Về trang chủ</a>
    </div></main>"""
    return render_page("403", body, 403)


@app.errorhandler(500)
def internal_error(e):
    body = """<main>
    <div class="page-content" style="max-width:600px;margin:60px auto;text-align:center">
        <div style="font-size:5rem;color:var(--primary)">500</div>
        <h1>Lỗi máy chủ</h1>
        <p style="margin-top:16px;color:#888">Đã xảy ra lỗi. Vui lòng thử lại sau.</p>
        <a href="{{URL_HOME}}" class="btn" style="margin-top:24px">Về trang chủ</a>
    </div></main>"""
    return render_page("500", body, 500)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
