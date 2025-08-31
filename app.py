# app.py
import streamlit as st
import json
import time
import re
import io
import zipfile
from datetime import datetime

# =========================================================
# Basic configuration
# =========================================================
APP_NAME = "Universal App Builder (Single File)"
DEFAULT_ADMIN_USER = "admin"
DEFAULT_ADMIN_PASS = "admin"

# A simple, local-only “license” check (demo).
# Format expected: NAVINN-YYYY-XXXX where checksum of YYYY+XXXX must be divisible by 7
LICENSE_PREFIX = "NAVINN"

# =========================================================
# Utilities
# =========================================================
def slugify(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9\-]+", "-", name)
    name = re.sub(r"-+", "-", name).strip("-")
    return name or "my-app"

def now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def ensure_session():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "licensed" not in st.session_state:
        st.session_state.licensed = False
    if "license_key" not in st.session_state:
        st.session_state.license_key = ""
    if "project" not in st.session_state:
        st.session_state.project = new_project()
    if "selected_index" not in st.session_state:
        st.session_state.selected_index = None

def new_project():
    return {
        "name": "My Awesome App",
        "brand": "YourBrand",
        "created": now_iso(),
        "frontend": {
            "framework": "React",  # or "Vanilla"
            "themeColor": "#1273de",
            "accentColor": "#FFB703",
            "darkMode": False
        },
        "backend": {
            "type": "FastAPI"  # "Express" or "None"
        },
        "components": [
            {"type": "text", "id": "title1", "label": "Welcome to your app!"},
            {"type": "input", "id": "name", "label": "Your name", "placeholder": "Enter your name"},
            {"type": "button", "id": "cta", "label": "Submit"},
        ],
        "meta": {
            "version": "0.1.0",
            "author": "You",
        }
    }

def verify_license(key: str) -> bool:
    # Demo format: NAVINN-YYYY-XXXX
    # checksum = sum of ASCII codes of YYYY+XXXX; must be %7 == 0
    try:
        parts = key.strip().upper().split("-")
        if len(parts) != 3:
            return False
        if parts[0] != LICENSE_PREFIX:
            return False
        y, x = parts[1], parts[2]
        if not (y.isalnum() and x.isalnum()):
            return False
        checksum = sum(ord(c) for c in (y + x))
        return checksum % 7 == 0
    except Exception:
        return False

def trial_watermark():
    st.markdown(
        "<div style='color:#888;font-size:12px;margin-top:12px'>Trial mode — export will include a small watermark in README.</div>",
        unsafe_allow_html=True
    )

# =========================================================
# Component library and preview
# =========================================================
COMP_TYPES = {
    "text": {
        "fields": ["label"],
        "preview": lambda c: st.write(c.get("label", "Text")),
    },
    "input": {
        "fields": ["label", "placeholder"],
        "preview": lambda c: st.text_input(c.get("label","Input"), placeholder=c.get("placeholder","")),
    },
    "button": {
        "fields": ["label"],
        "preview": lambda c: st.button(c.get("label","Button")),
    },
    "checkbox": {
        "fields": ["label"],
        "preview": lambda c: st.checkbox(c.get("label","Checkbox")),
    },
    "select": {
        "fields": ["label", "options"],  # options as comma-separated string in editor
        "preview": lambda c: st.selectbox(
            c.get("label","Select"),
            [o.strip() for o in c.get("options","Option A,Option B").split(",") if o.strip()]
        ),
    },
    "table": {
        "fields": ["columns"],  # columns as comma-separated string
        "preview": lambda c: st.table(
            {col.strip(): [] for col in c.get("columns","Name,Value").split(",") if col.strip()}
        ),
    },
}

def new_component(c_type: str):
    base = {"type": c_type, "id": f"{c_type}_{int(time.time()*1000)}"}
    if c_type == "text":
        base.update({"label": "Sample text"})
    elif c_type == "input":
        base.update({"label": "Input", "placeholder": "Type here"})
    elif c_type == "button":
        base.update({"label": "Click me"})
    elif c_type == "checkbox":
        base.update({"label": "Enable feature"})
    elif c_type == "select":
        base.update({"label": "Choose option", "options": "Option A,Option B"})
    elif c_type == "table":
        base.update({"columns": "Name,Value"})
    return base

# =========================================================
# Code generation
# =========================================================
def generate_frontend_files(project: dict):
    brand = project["brand"]
    theme = project["frontend"]
    framework = theme["framework"]
    theme_color = theme["themeColor"]
    accent_color = theme["accentColor"]
    dark = theme["darkMode"]
    comps = project["components"]

    if framework == "React":
        return gen_react(project["name"], brand, theme_color, accent_color, dark, comps)
    else:
        return gen_vanilla(project["name"], brand, theme_color, accent_color, dark, comps)

def gen_shared_styles(theme_color, accent_color, dark):
    bg = "#0f172a" if dark else "#f8fafc"
    fg = "#e2e8f0" if dark else "#0f172a"
    card = "#111827" if dark else "#ffffff"
    border = "#1f2937" if dark else "#e5e7eb"
    return f""":root {{
  --theme: {theme_color};
  --accent: {accent_color};
  --bg: {bg};
  --fg: {fg};
  --card: {card};
  --border: {border};
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; background: var(--bg); color: var(--fg);
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
}}
.container {{
  max-width: 960px; margin: 24px auto; padding: 24px;
}}
.card {{
  background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 16px; margin-bottom: 12px;
}}
.btn {{
  background: var(--theme); color: white; border: none; padding: 10px 14px; border-radius: 8px; cursor: pointer;
}}
.input {{
  width: 100%; padding: 10px; border: 1px solid var(--border); border-radius: 8px; margin: 6px 0 12px;
}}
.label {{ display: block; font-weight: 600; margin: 8px 0 6px; }}
.title {{ font-size: 28px; font-weight: 700; margin: 0 0 12px; }}
.brand {{ color: var(--accent); font-weight: 700; }}
hr {{ border: none; border-top: 1px solid var(--border); margin: 16px 0; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ border: 1px solid var(--border); padding: 8px; text-align: left; }}
"""

def react_component_jsx(comp):
    t = comp["type"]
    if t == "text":
        return f'<div className="card"><div className="title">{comp.get("label","")}</div></div>'
    if t == "input":
        lid = comp["id"]
        return f'''<div className="card">
  <label className="label" htmlFor="{lid}">{comp.get("label","Input")}</label>
  <input id="{lid}" className="input" placeholder="{comp.get("placeholder","")}" />
</div>'''
    if t == "button":
        return f'<div className="card"><button className="btn">{comp.get("label","Click")}</button></div>'
    if t == "checkbox":
        lid = comp["id"]
        return f'''<div className="card">
  <label className="label"><input type="checkbox" id="{lid}" style={{ marginRight: 8 }} /> {comp.get("label","Checkbox")}</label>
</div>'''
    if t == "select":
        options = [o.strip() for o in comp.get("options","").split(",") if o.strip()]
        opts = "\n          ".join([f'<option value="{o}">{o}</option>' for o in options]) or '<option>Option</option>'
        lid = comp["id"]
        return f'''<div className="card">
  <label className="label" htmlFor="{lid}">{comp.get("label","Select")}</label>
  <select id="{lid}" className="input">
          {opts}
  </select>
</div>'''
    if t == "table":
        columns = [c.strip() for c in comp.get("columns","").split(",") if c.strip()]
        th = "".join([f"<th>{c}</th>" for c in columns]) or "<th>Column</th>"
        return f'''<div className="card">
  <table>
    <thead><tr>{th}</tr></thead>
    <tbody><tr>{"".join(["<td></td>" for _ in columns]) or "<td></td>"}</tr></tbody>
  </table>
</div>'''
    return '<div className="card">Unknown component</div>'

def gen_react(app_name, brand, theme_color, accent_color, dark, comps):
    styles = gen_shared_styles(theme_color, accent_color, dark)
    jsx = "\n        ".join([react_component_jsx(c) for c in comps])

    app_jsx = f"""import './styles.css'

export default function App() {{
  return (
    <div className="container">
      <div className="title">{app_name} <span className="brand">{brand}</span></div>
      <hr/>
      {jsx}
    </div>
  )
}}
""".rstrip()

    main_jsx = """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
""".rstrip()

    index_html = """<!doctype html>
<html>
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>App</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
""".rstrip()

    package_json = {
        "name": slugify(app_name),
        "private": True,
        "version": "0.0.1",
        "type": "module",
        "scripts": {
            "dev": "vite",
            "build": "vite build",
            "preview": "vite preview"
        },
        "dependencies": {
            "react": "^18.3.1",
            "react-dom": "^18.3.1"
        },
        "devDependencies": {
            "vite": "^5.2.0"
        }
    }

    files = {
        "frontend/package.json": json.dumps(package_json, indent=2),
        "frontend/index.html": index_html,
        "frontend/src/App.jsx": app_jsx,
        "frontend/src/main.jsx": main_jsx,
        "frontend/src/styles.css": styles
    }
    return files

def gen_vanilla(app_name, brand, theme_color, accent_color, dark, comps):
    styles = gen_shared_styles(theme_color, accent_color, dark)
    html_parts = []
    for c in comps:
        t = c["type"]
        if t == "text":
            html_parts.append(f'<div class="card"><div class="title">{c.get("label","")}</div></div>')
        elif t == "input":
            html_parts.append(f'''<div class="card">
  <label class="label" for="{c["id"]}">{c.get("label","Input")}</label>
  <input id="{c["id"]}" class="input" placeholder="{c.get("placeholder","")}" />
</div>''')
        elif t == "button":
            html_parts.append(f'<div class="card"><button class="btn">{c.get("label","Click")}</button></div>')
        elif t == "checkbox":
            html_parts.append(f'''<div class="card">
  <label class="label"><input type="checkbox" id="{c["id"]}" style="margin-right:8px" /> {c.get("label","Checkbox")}</label>
</div>''')
        elif t == "select":
            options = [o.strip() for o in c.get("options","").split(",") if o.strip()]
            opts = "\n      ".join([f'<option value="{o}">{o}</option>' for o in options]) or '<option>Option</option>'
            html_parts.append(f'''<div class="card">
  <label class="label" for="{c["id"]}">{c.get("label","Select")}</label>
  <select id="{c["id"]}" class="input">
      {opts}
  </select>
</div>''')
        elif t == "table":
            columns = [cl.strip() for cl in c.get("columns","").split(",") if cl.strip()]
            th = "".join([f"<th>{cl}</th>" for cl in columns]) or "<th>Column</th>"
            html_parts.append(f'''<div class="card">
  <table>
    <thead><tr>{th}</tr></thead>
    <tbody><tr>{"".join(["<td></td>" for _ in columns]) or "<td></td>"}</tr></tbody>
  </table>
</div>''')
        else:
            html_parts.append('<div class="card">Unknown component</div>')

    body_html = "\n      ".join(html_parts)
    index_html = f"""<!doctype html>
<html>
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{app_name}</title>
    <style>
{styles}
    </style>
  </head>
  <body>
    <div class="container">
      <div class="title">{app_name} <span class="brand">{brand}</span></div>
      <hr/>
      {body_html}
    </div>
  </body>
</html>
""".rstrip()

    files = {
        "frontend/index.html": index_html
    }
    return files

def generate_backend_files(project: dict):
    btype = project["backend"]["type"]
    if btype == "FastAPI":
        return gen_fastapi_backend()
    elif btype == "Express":
        return gen_express_backend()
    else:
        return {}

def gen_fastapi_backend():
    main_py = """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

@app.get("/")
def root():
    return {"status": "ok", "message": "FastAPI backend running"}

@app.post("/echo")
def echo(payload: dict):
    return {"echo": payload}
""".rstrip()

    req = "fastapi>=0.111.0\nuvicorn[standard]>=0.30.0\n"
    run_sh = "uvicorn main:app --reload --port 8000\n"
    run_bat = "uvicorn main:app --reload --port 8000\r\n"
    files = {
        "backend_fastapi/main.py": main_py,
        "backend_fastapi/requirements.txt": req,
        "backend_fastapi/run.sh": run_sh,
        "backend_fastapi/run.bat": run_bat
    }
    return files

def gen_express_backend():
    server_js = """const express = require('express')
const cors = require('cors')
const app = express()
app.use(cors())
app.use(express.json())

app.get('/', (req, res) => res.json({ status: 'ok', message: 'Express backend running' }))
app.post('/echo', (req, res) => res.json({ echo: req.body }))

const port = process.env.PORT || 8000
app.listen(port, () => console.log('Server on ' + port))
""".rstrip()

    package_json = {
        "name": "backend-express",
        "private": True,
        "version": "0.0.1",
        "scripts": {
            "dev": "node server.js"
        },
        "dependencies": {
            "express": "^4.19.2",
            "cors": "^2.8.5"
        }
    }
    run_sh = "node server.js\n"
    run_bat = "node server.js\r\n"
    files = {
        "backend_express/server.js": server_js,
        "backend_express/package.json": json.dumps(package_json, indent=2),
        "backend_express/run.sh": run_sh,
        "backend_express/run.bat": run_bat
    }
    return files

def generate_readme(project: dict, licensed: bool):
    lines = []
    lines.append(f"# {project['name']}")
    lines.append("")
    lines.append(f"Generated with Universal App Builder — Brand: {project['brand']}")
    lines.append("")
    lines.append("## Project structure")
    lines.append("- frontend/")
    if project["backend"]["type"] == "FastAPI":
        lines.append("- backend_fastapi/")
    elif project["backend"]["type"] == "Express":
        lines.append("- backend_express/")
    lines.append("")
    lines.append("## Frontend")
    if project["frontend"]["framework"] == "React":
        lines.append("1. cd frontend")
        lines.append("2. npm install")
        lines.append("3. npm run dev")
    else:
        lines.append("Open frontend/index.html in a browser or serve with any static server.")
    lines.append("")
    lines.append("## Backend")
    b = project["backend"]["type"]
    if b == "FastAPI":
        lines.append("1. cd backend_fastapi")
        lines.append("2. pip install -r requirements.txt")
        lines.append("3. sh run.sh  # or run.bat on Windows")
    elif b == "Express":
        lines.append("1. cd backend_express")
        lines.append("2. npm install")
        lines.append("3. sh run.sh  # or run.bat on Windows")
    else:
        lines.append("No backend selected.")
    lines.append("")
    if not licensed:
        lines.append("---")
        lines.append("Trial build — Created with Universal App Builder (Single File).")
    return "\n".join(lines)

def build_zip(project: dict, licensed: bool) -> bytes:
    frontend_files = generate_frontend_files(project)
    backend_files = generate_backend_files(project)
    readme = generate_readme(project, licensed)

    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        # frontend
        for path, content in frontend_files.items():
            z.writestr(path, content)
        # backend
        for path, content in backend_files.items():
            z.writestr(path, content)
        # README
        z.writestr("README.md", readme)
    mem.seek(0)
    return mem.read()

# =========================================================
# UI sections
# =========================================================
def ui_sidebar(project):
    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Go to",
            options=["Login", "License", "Builder", "Export", "Settings"],
            index=2 if st.session_state.logged_in else 0,
            label_visibility="collapsed"
        )
        st.divider()
        st.caption("Session")
        if st.button("Reset project"):
            st.session_state.project = new_project()
            st.session_state.selected_index = None
            st.rerun()
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()
    return page

def ui_login():
    st.title(APP_NAME)
    st.write("Sign in to continue.")
    u = st.text_input("Username", value="", key="login_user")
    p = st.text_input("Password", value="", type="password", key="login_pass")
    if st.button("Login"):
        if u == DEFAULT_ADMIN_USER and p == DEFAULT_ADMIN_PASS:
            st.session_state.logged_in = True
            st.success("Logged in")
            st.rerun()
        else:
            st.error("Invalid credentials")

def ui_license():
    st.title("License")
    st.write("Enter your license key to remove trial watermark in exports.")
    key = st.text_input("License key", value=st.session_state.license_key)
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("Validate"):
            st.session_state.license_key = key.strip()
            st.session_state.licensed = verify_license(st.session_state.license_key)
            if st.session_state.licensed:
                st.success("License valid. Thank you!")
            else:
                st.error("Invalid license key")
    with col2:
        st.write("")
        st.caption("Format: NAVINN-YYYY-XXXX (demo)")
    if not st.session_state.licensed:
        trial_watermark()

def ui_settings(project):
    st.title("Settings")
    st.write("Project-level settings.")
    project["name"] = st.text_input("App name", project["name"])
    project["brand"] = st.text_input("Brand", project["brand"])
    st.write("Frontend theme")
    project["frontend"]["framework"] = st.selectbox(
        "Framework", ["React", "Vanilla"], index=0 if project["frontend"]["framework"]=="React" else 1
    )
    project["frontend"]["themeColor"] = st.color_picker("Theme color", project["frontend"]["themeColor"])
    project["frontend"]["accentColor"] = st.color_picker("Accent color", project["frontend"]["accentColor"])
    project["frontend"]["darkMode"] = st.toggle("Dark mode", project["frontend"]["darkMode"])
    st.write("Backend")
    project["backend"]["type"] = st.selectbox(
        "Backend type", ["FastAPI", "Express", "None"],
        index={"FastAPI":0,"Express":1,"None":2}[project["backend"]["type"]]
    )
    st.success("Settings updated.")

def edit_component(c, idx):
    st.subheader(f"{idx+1}. {c['type']} — {c['id']}")
    cols = st.columns([0.15,0.15,0.15,0.55])
    with cols[0]:
        if st.button("▲", key=f"up_{idx}", help="Move up") and idx > 0:
            st.session_state.project["components"][idx-1], st.session_state.project["components"][idx] = \
                st.session_state.project["components"][idx], st.session_state.project["components"][idx-1]
            st.rerun()
    with cols[1]:
        if st.button("▼", key=f"down_{idx}", help="Move down") and idx < len(st.session_state.project["components"])-1:
            st.session_state.project["components"][idx+1], st.session_state.project["components"][idx] = \
                st.session_state.project["components"][idx], st.session_state.project["components"][idx+1]
            st.rerun()
    with cols[2]:
        if st.button("🗑️", key=f"del_{idx}", help="Delete component"):
            st.session_state.project["components"].pop(idx)
            st.rerun()
    st.divider()

    fields = COMP_TYPES[c["type"]]["fields"]
    if "label" in fields:
        c["label"] = st.text_input("Label", c.get("label",""), key=f"label_{idx}")
    if "placeholder" in fields:
        c["placeholder"] = st.text_input("Placeholder", c.get("placeholder",""), key=f"ph_{idx}")
    if "options" in fields:
        c["options"] = st.text_input("Options (comma-separated)", c.get("options","Option A,Option B"), key=f"opts_{idx}")
    if "columns" in fields:
        c["columns"] = st.text_input("Columns (comma-separated)", c.get("columns","Name,Value"), key=f"cols_{idx}")
    c["id"] = st.text_input("ID", c["id"], key=f"id_{idx}")

def ui_builder(project):
    st.title("Builder")
    st.write("Add components, edit properties, and preview.")

    with st.expander("Add component", expanded=True):
        c_type = st.selectbox("Component type", list(COMP_TYPES.keys()))
        if st.button("Add"):
            st.session_state.project["components"].append(new_component(c_type))
            st.success(f"Added {c_type}")
            st.rerun()

    st.subheader("Components")
    if not project["components"]:
        st.info("No components yet. Add one above.")
    for i, comp in enumerate(project["components"]):
        with st.container(border=True):
            edit_component(comp, i)

    st.subheader("Live preview")
    st.caption("Preview approximates look and layout.")
    for comp in project["components"]:
        COMP_TYPES[comp["type"]]["preview"](comp)

    st.divider()
    col1, col2 = st.columns([1,1])
    with col1:
        proj_json = json.dumps(project, indent=2)
        st.download_button("Download project JSON", data=proj_json, file_name=f"{slugify(project['name'])}.json", mime="application/json")
    with col2:
        uploaded = st.file_uploader("Load project JSON", type=["json"])
        if uploaded is not None:
            try:
                data = json.loads(uploaded.read().decode("utf-8"))
                st.session_state.project = data
                st.success("Project loaded.")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to load: {e}")

def ui_export(project):
    st.title("Export")
    st.write("Generate a runnable project as a ZIP.")
    col = st.columns([1,1,1])
    with col[0]:
        st.metric("Frontend", project["frontend"]["framework"])
    with col[1]:
        st.metric("Backend", project["backend"]["type"])
    with col[2]:
        st.metric("Components", len(project["components"]))

    if not st.session_state.licensed:
        trial_watermark()

    if st.button("Build ZIP"):
        try:
            blob = build_zip(project, st.session_state.licensed)
            st.success("Build complete.")
            st.download_button(
                "Download ZIP",
                data=blob,
                file_name=f"{slugify(project['name'])}.zip",
                mime="application/zip"
            )
        except Exception as e:
            st.error(f"Build failed: {e}")

# =========================================================
# App entry
# =========================================================
def main():
    st.set_page_config(page_title=APP_NAME, layout="wide")
    ensure_session()

    project = st.session_state.project
    page =
