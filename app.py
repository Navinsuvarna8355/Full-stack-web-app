import streamlit as st
import json, time, re, io, zipfile, base64
from datetime import datetime

APP_NAME = "Universal App Builder — Single File Pro"
DEFAULT_ADMIN_USER = "admin"
DEFAULT_ADMIN_PASS = "admin"
LICENSE_PREFIX = "NAVINN"

# ------------------ Utilities ------------------
def slugify(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9\-]+", "-", name)
    name = re.sub(r"-+", "-", name).strip("-")
    return name or "my-app"

def now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def ensure_session():
    defaults = {
        "logged_in": False,
        "licensed": False,
        "license_key": "",
        "project": new_project()
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def new_project():
    return {
        "name": "My Awesome App",
        "brand": "YourBrand",
        "created": now_iso(),
        "frontend": {"framework": "React", "themeColor": "#1273de", "accentColor": "#FFB703", "darkMode": False},
        "backend": {"type": "FastAPI"},
        "components": [],
        "meta": {"version": "0.1.0", "author": "You"}
    }

def verify_license(key: str) -> bool:
    try:
        parts = key.strip().upper().split("-")
        if len(parts) != 3 or parts[0] != LICENSE_PREFIX:
            return False
        y, x = parts[1], parts[2]
        if not (y.isalnum() and x.isalnum()):
            return False
        checksum = sum(ord(c) for c in (y + x))
        return checksum % 7 == 0
    except Exception:
        return False

def trial_watermark():
    st.caption("Trial mode — export will include a watermark in README.")

# ------------------ Component Library ------------------
COMP_TYPES = {
    "text": {"fields": ["label"], "preview": lambda c: st.write(c.get("label", "Text"))},
    "input": {"fields": ["label", "placeholder"], "preview": lambda c: st.text_input(c.get("label","Input"), placeholder=c.get("placeholder",""))},
    "button": {"fields": ["label"], "preview": lambda c: st.button(c.get("label","Button"))},
}

def new_component(c_type: str):
    base = {"type": c_type, "id": f"{c_type}_{int(time.time()*1000)}", "x": 0, "y": 0}
    if c_type == "text":
        base.update({"label": "Sample text"})
    elif c_type == "input":
        base.update({"label": "Input", "placeholder": "Type here"})
    elif c_type == "button":
        base.update({"label": "Click me"})
    return base

# ------------------ Code Generation ------------------
def generate_frontend_files(project: dict):
    fw = project["frontend"]["framework"]
    if fw == "React":
        return {"frontend/index.html": f"<h1>{project['name']} (React)</h1>"}
    elif fw == "Vue":
        return {"frontend/index.html": f"<h1>{project['name']} (Vue)</h1>"}
    else:
        return {"frontend/index.html": f"<h1>{project['name']} (Vanilla)</h1>"}

def generate_backend_files(project: dict):
    bt = project["backend"]["type"]
    if bt == "FastAPI":
        return {"backend/main.py": "from fastapi import FastAPI\napp = FastAPI()"}
    elif bt == "Express":
        return {"backend/server.js": "const express=require('express');const app=express();"}
    elif bt == "Flask":
        return {"backend/app.py": "from flask import Flask\napp = Flask(__name__)"}
    elif bt == "NodeHTTP":
        return {"backend/server.js": "const http=require('http');http.createServer((req,res)=>res.end('OK')).listen(3000);"}
    else:
        return {}

def generate_readme(project: dict, licensed: bool):
    lines = [f"# {project['name']}", "", f"Brand: {project['brand']}"]
    if not licensed:
        lines.append("---\nTrial build — Created with Universal App Builder")
    return "\n".join(lines)

def build_zip(project: dict, licensed: bool) -> bytes:
    frontend_files = generate_frontend_files(project)
    backend_files = generate_backend_files(project)
    readme = generate_readme(project, licensed)
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        for path, content in {**frontend_files, **backend_files, "README.md": readme}.items():
            z.writestr(path, content)
    mem.seek(0)
    return mem.read()

# ------------------ UI Sections ------------------
def ui_sidebar(project):
    with st.sidebar:
        page = st.radio("Go to", ["Login", "License", "Builder", "Export", "Settings"], index=2 if st.session_state.logged_in else 0)
        if st.button("Reset project"):
            st.session_state.project = new_project()
            st.rerun()
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()
    return page

def ui_login():
    st.title(APP_NAME)
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u == DEFAULT_ADMIN_USER and p == DEFAULT_ADMIN_PASS:
            st.session_state.logged_in = True
            st.success("Logged in")
            st.rerun()
        else:
            st.error("Invalid credentials")

def ui_license():
    st.title("License")
    key = st.text_input("License key", value=st.session_state.license_key)
    if st.button("Validate"):
        st.session_state.license_key = key.strip()
        st.session_state.licensed = verify_license(st.session_state.license_key)
        st.success("License valid" if st.session_state.licensed else "Invalid license key")
    if not st.session_state.licensed:
        trial_watermark()

def ui_settings(project):
    st.title("Settings")
    project["name"] = st.text_input("App name", project["name"])
    project["brand"] = st.text_input("Brand", project["brand"])
    project["frontend"]["framework"] = st.selectbox("Framework", ["React", "Vue", "Vanilla"])
    project["backend"]["type"] = st.selectbox("Backend type", ["FastAPI", "Express", "Flask", "NodeHTTP", "None"])

def edit_component(c, idx):
    st.subheader(f"{idx+1}. {c['type']}")
    for field in COMP_TYPES[c["type"]]["fields"]:
        c[field] = st.text_input(field.capitalize(), c.get(field,""), key=f"{field}_{idx}")

def ui_builder(project):
    st.title("Builder")
    c_type = st.selectbox("Component type", list(COMP_TYPES.keys()))
    if st.button("Add"):
        project["components"].append(new_component(c_type))
        st.rerun()
    for i, comp in enumerate(project["components"]):
        edit_component(comp, i)
    st.subheader("Preview")
    for comp in project["components"]:
        COMP_TYPES[comp["type"]]["preview"](comp)

def ui_export(project):
    st.title("Export")
    if not st.session_state.licensed:
        trial_watermark()
    if st.button("Build ZIP"):
        blob = build_zip(project, st.session_state.licensed)
        st.download_button("Download ZIP", data=blob, file_name=f"{slugify(project['name'])}.zip", mime="application/zip")

# ------------------ Entry ------------------
def main():
    st.set_page_config(page_title=APP_NAME, layout="wide")
    ensure_session()
    project = st.session_state.project
    page = ui_sidebar(project)  # ✅ fixed

    if page == "Login":
        ui_login()
    elif
