import streamlit as st
import os, zipfile, tempfile, json

# ---------------------------
# 1. Entity Parser
# ---------------------------
def parse_entities(prompt):
    # Simple demo parser — replace with NLP model for production
    # Example: "Inventory app with products (name, price) and suppliers (name, contact)"
    entities = {}
    parts = prompt.split(" and ")
    for p in parts:
        if "(" in p:
            name, fields = p.split("(")
            name = name.strip().split()[-1].lower()
            fields = [f.strip().lower() for f in fields.strip(")").split(",")]
            entities[name] = fields
    return entities

# ---------------------------
# 2. Backend Generators
# ---------------------------
def generate_backend(language, entities):
    if language == "python":
        return generate_python_fastapi(entities)
    elif language == "node":
        return generate_node_express(entities)
    else:
        return "# Backend generator not implemented"

def generate_python_fastapi(entities):
    code = ["from fastapi import FastAPI\napp = FastAPI()\n"]
    db = {e: [] for e in entities}
    code.append(f"db = {json.dumps(db)}\n")
    for e, fields in entities.items():
        code.append(f"@app.get('/{e}')\ndef get_{e}():\n    return db['{e}']\n")
        code.append(f"@app.post('/{e}')\ndef add_{e}(item: dict):\n    db['{e}'].append(item)\n    return item\n")
    return "\n".join(code)

def generate_node_express(entities):
    code = ["const express = require('express');\nconst app = express();\napp.use(express.json());\n"]
    code.append(f"let db = {json.dumps({e: [] for e in entities})};\n")
    for e in entities:
        code.append(f"app.get('/{e}', (req,res) => res.json(db['{e}']));\n")
        code.append(f"app.post('/{e}', (req,res) => {{ db['{e}'].push(req.body); res.json(req.body); }});\n")
    code.append("app.listen(3000, () => console.log('Server running'));\n")
    return "\n".join(code)

# ---------------------------
# 3. Frontend Generators
# ---------------------------
def generate_frontend(framework, app_name, entities, api_base):
    if framework == "react":
        return react_stub(app_name, entities, api_base)
    elif framework == "vue":
        return vue_stub(app_name, entities, api_base)
    elif framework == "svelte":
        return svelte_stub(app_name, entities, api_base)
    else:
        return "// Frontend generator not implemented"

# React Stub
def react_stub(app_name, entities, api_base):
    components = []
    for entity, fields in entities.items():
        inputs = "\n".join(
            [f'<input placeholder="{f}" value={{form.{f} || ""}} onChange={{e => setForm({{...form, {f}: e.target.value}})}} />' for f in fields]
        )
        components.append(f"""
function {entity.capitalize()}Manager() {{
  const [items, setItems] = React.useState([]);
  const [form, setForm] = React.useState({{}});
  React.useEffect(() => {{ load(); }}, []);
  async function load() {{
    const res = await fetch("{api_base}/{entity}");
    setItems(await res.json());
  }}
  async function add() {{
    await fetch("{api_base}/{entity}", {{
      method: "POST",
      headers: {{ "Content-Type": "application/json" }},
      body: JSON.stringify(form)
    }});
    setForm({{}});
    load();
  }}
  return (<div>
    <h2>{entity.capitalize()}</h2>
    {inputs}
    <button onClick={{add}}>Add</button>
    <ul>{{items.map((i, idx) => <li key={idx}>{{JSON.stringify(i)}}</li>)}}</ul>
  </div>);
}}
""")
    return f"""import React from 'react';
export default function App() {{
  return (<div>
    <h1>{app_name}</h1>
    {''.join([f"<{e.capitalize()}Manager />" for e in entities])}
  </div>);
}}
{''.join(components)}
"""

# Vue Stub
def vue_stub(app_name, entities, api_base):
    components = []
    for entity, fields in entities.items():
        inputs = "\n".join([f'<input placeholder="{f}" v-model="{entity}.{f}" />' for f in fields])
        components.append(f"""
<template>
  <div>
    <h2>{entity.capitalize()}</h2>
    {inputs}
    <button @click="add">Add</button>
    <ul><li v-for="(i, idx) in items" :key="idx">{{{{ i }}}}</li></ul>
  </div>
</template>
<script>
export default {{
  data() {{
    return {{ items: [], {entity}: {{}} }};
  }},
  mounted() {{ this.load(); }},
  methods: {{
    async load() {{
      const res = await fetch("{api_base}/{entity}");
      this.items = await res.json();
    }},
    async add() {{
      await fetch("{api_base}/{entity}", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify(this.{entity})
      }});
      this.{entity} = {{}};
      this.load();
    }}
  }}
}}
</script>
""")
    return "\n".join(components)

# Svelte Stub
def svelte_stub(app_name, entities, api_base):
    components = []
    for entity, fields in entities.items():
        inputs = "\n".join([f'<input placeholder="{f}" bind:value={f} />' for f in fields])
        components.append(f"""
<script>
  import {{ onMount }} from 'svelte';
  let items = [];
  let {', '.join(fields)} = "";
  async function load() {{
    const res = await fetch("{api_base}/{entity}");
    items = await res.json();
  }}
  async function add() {{
    await fetch("{api_base}/{entity}", {{
      method: "POST",
      headers: {{ "Content-Type": "application/json" }},
      body: JSON.stringify({{{', '.join(fields)}}})
    }});
    { ' = '.join(fields) } = "";
    load();
  }}
  onMount(load);
</script>
<h2>{entity.capitalize()}</h2>
{inputs}
<button on:click={{add}}>Add</button>
<ul>
  {{#each items as i}}
    <li>{{{{ JSON.stringify(i) }}}}</li>
  {{/each}}
</ul>
""")
    return "\n".join(components)

# ---------------------------
# 4. Export Logic
# ---------------------------
def export_zip(backend_code, frontend_code, backend_lang, frontend_fw):
    tmpdir = tempfile.mkdtemp()
    os.makedirs(os.path.join(tmpdir, "backend"), exist_ok=True)
    os.makedirs(os.path.join(tmpdir, "frontend"), exist_ok=True)
    backend_file = "main.py" if backend_lang == "python" else "server.js"
    with open(os.path.join(tmpdir, "backend", backend_file), "w") as f:
        f.write(backend_code)
    with open(os.path.join(tmpdir, "frontend", f"App.{ 'jsx' if frontend_fw=='react' else 'vue' if frontend_fw=='vue' else 'svelte'}"), "w") as f:
        f.write(frontend_code)
    zip_path = os.path.join(tmpdir, "app_bundle.zip")
    with zipfile.ZipFile(zip_path, "w") as z:
        for root, _, files in os.walk(tmpdir):
            for file in files:
                if file != "app_bundle.zip":
                    z.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), tmpdir))
    return zip_path

# ---------------------------
# 5. Streamlit UI
# ---------------------------
st.title("Universal AI App Builder")
prompt = st.text_area("Describe your app")
backend_lang = st.selectbox("Backend Language", ["python", "node"])
frontend_fw = st.selectbox("Frontend Framework", ["react", "vue", "svelte"])
api_base = st.text_input("API Base URL", "http://localhost:8000")

if st.button("Generate & Export"):
    entities = parse_entities(prompt)
    backend_code = generate_backend(backend_lang, entities)
    frontend_code = generate_frontend(front
