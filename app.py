import os
from flask import Flask, request, redirect, session, jsonify
import json

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret")
PASSWORD    = os.getenv("DASHBOARD_PASSWORD", "admin")
CONFIG_FILE = "config.json"
WL_FILE     = "whitelist.json"

print("Flask app created", flush=True)

DEFAULT_CONFIG = {
    "prefix": "!",
    "admin_role": "Admin",
    "whitelist_role": "whitelisted",
    "auto_kick": False,
    "embed": {
        "title": "You've been whitelisted!",
        "description": "Welcome! You now have access to the server.",
        "color": "#57F287",
        "image_url": "",
        "footer": "Whitelisted"
    }
}

def load_cfg():
    if not os.path.exists(CONFIG_FILE):
        save_cfg(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    with open(CONFIG_FILE) as f:
        return json.load(f)

def save_cfg(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_wl():
    if not os.path.exists(WL_FILE):
        return {}
    with open(WL_FILE) as f:
        return json.load(f)

def save_wl(data):
    with open(WL_FILE, "w") as f:
        json.dump(data, f, indent=2)


@app.route("/")
def index():
    if not session.get("auth"):
        return redirect("/login")
    cfg = load_cfg()
    wl  = load_wl()
    embed = cfg.get("embed", {})
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Whitelist Dashboard</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',sans-serif;background:#1e1f22;color:#dbdee1;min-height:100vh;display:flex}}
.sidebar{{width:200px;background:#2b2d31;padding:20px 0;display:flex;flex-direction:column;flex-shrink:0}}
.sidebar-logo{{padding:0 16px 20px;font-size:16px;font-weight:700;color:#fff;border-bottom:1px solid #3f4046}}
.sidebar-logo span{{color:#5865f2}}
.nav-item{{padding:10px 16px;cursor:pointer;border-radius:4px;margin:2px 8px;font-size:14px;color:#949ba4;transition:.15s;display:block}}
.nav-item:hover{{background:#35373c;color:#dbdee1}}
.nav-item.active{{background:#404249;color:#fff}}
.main{{flex:1;padding:32px;overflow-y:auto}}
.page{{display:none}}.page.active{{display:block}}
h1{{font-size:22px;font-weight:700;color:#fff;margin-bottom:6px}}
.sub{{color:#949ba4;font-size:14px;margin-bottom:28px}}
.card{{background:#2b2d31;border-radius:8px;padding:24px;margin-bottom:20px}}
.card h2{{font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;color:#949ba4;margin-bottom:16px}}
label{{font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;color:#b5bac1;display:block;margin-bottom:6px}}
input[type=text],textarea{{background:#1e1f22;border:1px solid #3f4046;border-radius:4px;padding:10px 12px;color:#dbdee1;font-size:14px;width:100%;outline:none;margin-bottom:14px;font-family:inherit}}
textarea{{resize:vertical;min-height:70px}}
input[type=color]{{width:50px;height:36px;border:none;border-radius:4px;cursor:pointer;background:none;padding:0;margin-bottom:14px}}
.row{{display:flex;gap:16px;flex-wrap:wrap}}
.col{{flex:1;min-width:160px}}
.btn{{padding:10px 20px;border:none;border-radius:4px;cursor:pointer;font-size:14px;font-weight:600;transition:.15s}}
.btn-p{{background:#5865f2;color:#fff}}.btn-p:hover{{background:#4752c4}}
.btn-d{{background:#ed4245;color:#fff;padding:6px 12px;font-size:12px}}.btn-d:hover{{background:#c03537}}
.ok{{color:#3ba55d;font-size:13px;display:none;margin-left:10px}}
.toggle-row{{display:flex;align-items:center;justify-content:space-between;padding:12px 0;border-bottom:1px solid #3f4046}}
.toggle-row:last-child{{border-bottom:none}}
.toggle-info .tl{{font-size:14px}}.toggle-info .td{{font-size:12px;color:#949ba4;margin-top:2px}}
.toggle{{position:relative;width:40px;height:22px;flex-shrink:0}}
.toggle input{{opacity:0;width:0;height:0}}
.slider{{position:absolute;inset:0;background:#4e5058;border-radius:11px;cursor:pointer;transition:.2s}}
.slider:before{{content:"";position:absolute;width:16px;height:16px;left:3px;top:3px;background:#fff;border-radius:50%;transition:.2s}}
input:checked+.slider{{background:#5865f2}}
input:checked+.slider:before{{transform:translateX(18px)}}
.prev{{background:#313338;border-radius:8px;padding:16px}}
.prev-label{{font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:#949ba4;margin-bottom:12px}}
.dembed{{display:flex;border-radius:4px;overflow:hidden;max-width:440px}}
.dembed-bar{{width:4px;flex-shrink:0}}
.dembed-body{{background:#2b2d31;padding:12px 16px;flex:1}}
.dembed-title{{font-weight:700;font-size:15px;color:#fff;margin-bottom:6px}}
.dembed-desc{{font-size:14px;color:#dbdee1;line-height:1.5}}
.dembed-img{{width:100%;border-radius:4px;margin-top:10px}}
.dembed-footer{{font-size:12px;color:#949ba4;margin-top:10px;padding-top:8px;border-top:1px solid #3f4046}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;padding:10px 12px;font-size:12px;text-transform:uppercase;letter-spacing:.5px;color:#949ba4;border-bottom:1px solid #3f4046}}
td{{padding:10px 12px;font-size:14px;border-bottom:1px solid #26272b}}
tr:last-child td{{border-bottom:none}}
tr:hover td{{background:#35373c}}
.empty{{text-align:center;padding:40px;color:#949ba4;font-size:14px}}
.badge{{background:#3ba55d;color:#fff;font-size:11px;padding:2px 8px;border-radius:10px}}
a{{color:inherit;text-decoration:none}}
</style>
</head>
<body>
<div class="sidebar">
  <div class="sidebar-logo">&#9889; <span>Whitelist</span> Bot</div>
  <div style="padding:12px 8px 4px;font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:#5c5f66;padding-left:16px">Config</div>
  <a class="nav-item active" onclick="show('embed',this)" href="#">&#127912; Embed</a>
  <a class="nav-item" onclick="show('settings',this)" href="#">&#9881; Settings</a>
  <a class="nav-item" onclick="show('whitelist',this)" href="#">&#128203; Whitelist</a>
  <div style="margin-top:auto;padding:12px 8px">
    <a href="/logout" class="nav-item" style="color:#ed4245">&#128682; Logout</a>
  </div>
</div>
<div class="main">

  <div class="page active" id="p-embed">
    <h1>Embed Settings</h1>
    <div class="sub">Message shown when someone types <strong>wl</strong></div>
    <div class="row">
      <div style="flex:1;min-width:280px">
        <div class="card">
          <h2>Content</h2>
          <label>Title</label>
          <input type="text" id="e-title" value="{embed.get('title','')}">
          <label>Description</label>
          <textarea id="e-desc">{embed.get('description','')}</textarea>
          <div class="row">
            <div class="col"><label>Color</label><input type="color" id="e-color" value="{embed.get('color','#57F287')}" oninput="updatePrev()"></div>
            <div class="col"><label>Footer</label><input type="text" id="e-footer" value="{embed.get('footer','')}"></div>
          </div>
          <label>Banner Image URL</label>
          <input type="text" id="e-img" value="{embed.get('image_url','')}">
          <button class="btn btn-p" onclick="saveEmbed()">Save Changes</button>
          <span class="ok" id="e-ok">Saved!</span>
        </div>
      </div>
      <div style="flex:1;min-width:260px">
        <div class="card">
          <h2>Live Preview</h2>
          <div class="prev">
            <div class="prev-label">Discord Preview</div>
            <div class="dembed">
              <div class="dembed-bar" id="prev-bar" style="background:{embed.get('color','#57F287')}"></div>
              <div class="dembed-body">
                <div class="dembed-title" id="prev-title">{embed.get('title','')}</div>
                <div class="dembed-desc" id="prev-desc">{embed.get('description','')}</div>
                {'<img class="dembed-img" id="prev-img" src="' + embed.get('image_url','') + '">' if embed.get('image_url') else '<img class="dembed-img" id="prev-img" src="" style="display:none">'}
                {'<div class="dembed-footer" id="prev-footer">' + embed.get('footer','') + '</div>' if embed.get('footer') else '<div class="dembed-footer" id="prev-footer" style="display:none"></div>'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="page" id="p-settings">
    <h1>Bot Settings</h1>
    <div class="sub">Configure roles, prefix, and behavior</div>
    <div class="card">
      <h2>Roles &amp; Prefix</h2>
      <div class="row">
        <div class="col"><label>Prefix</label><input type="text" id="s-prefix" value="{cfg.get('prefix','!')}"></div>
        <div class="col"><label>Admin Role</label><input type="text" id="s-admin" value="{cfg.get('admin_role','Admin')}"></div>
        <div class="col"><label>Whitelist Role</label><input type="text" id="s-wlrole" value="{cfg.get('whitelist_role','whitelisted')}"></div>
      </div>
    </div>
    <div class="card">
      <h2>Behavior</h2>
      <div class="toggle-row">
        <div class="toggle-info">
          <div class="tl">Auto-Kick on Join</div>
          <div class="td">Kick members who join but are not whitelisted</div>
        </div>
        <label class="toggle">
          <input type="checkbox" id="s-kick" {'checked' if cfg.get('auto_kick') else ''}>
          <span class="slider"></span>
        </label>
      </div>
    </div>
    <button class="btn btn-p" onclick="saveSettings()">Save Changes</button>
    <span class="ok" id="s-ok">Saved!</span>
  </div>

  <div class="page" id="p-whitelist">
    <h1>Whitelist</h1>
    <div class="sub">View and manage whitelisted users</div>
    <div class="card">
      <h2>Users <span class="badge">{len(wl)}</span></h2>
      {'<table><thead><tr><th>User</th><th>Added By</th><th>Action</th></tr></thead><tbody>' +
       ''.join(f'<tr><td><strong>{v.get("tag",k)}</strong><br><small style="color:#949ba4">{k}</small></td><td>{v.get("by","?")}</td><td><form method="POST" action="/remove/{k}"><button class="btn btn-d">Remove</button></form></td></tr>' for k,v in wl.items()) +
       '</tbody></table>' if wl else '<div class="empty">No whitelisted users yet.</div>'}
    </div>
  </div>

</div>
<script>
function show(name, el) {{
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('p-' + name).classList.add('active');
  el.classList.add('active');
}}
function updatePrev() {{
  const c = document.getElementById('e-color').value;
  document.getElementById('prev-bar').style.background = c;
  document.getElementById('prev-title').textContent = document.getElementById('e-title').value;
  document.getElementById('prev-desc').textContent  = document.getElementById('e-desc').value;
  const fi = document.getElementById('prev-footer');
  const fv = document.getElementById('e-footer').value;
  fi.textContent = fv; fi.style.display = fv ? 'block' : 'none';
  const ii = document.getElementById('prev-img');
  const iv = document.getElementById('e-img').value;
  ii.src = iv; ii.style.display = iv ? 'block' : 'none';
}}
document.getElementById('e-title').oninput = updatePrev;
document.getElementById('e-desc').oninput  = updatePrev;
document.getElementById('e-footer').oninput = updatePrev;
document.getElementById('e-img').oninput   = updatePrev;
function flash(id) {{ const el = document.getElementById(id); el.style.display='inline'; setTimeout(()=>el.style.display='none',2000); }}
function saveEmbed() {{
  fetch('/api/embed', {{method:'POST',headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{title:document.getElementById('e-title').value,description:document.getElementById('e-desc').value,
    color:document.getElementById('e-color').value,footer:document.getElementById('e-footer').value,image_url:document.getElementById('e-img').value}})
  }}).then(()=>flash('e-ok'));
}}
function saveSettings() {{
  fetch('/api/settings', {{method:'POST',headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{prefix:document.getElementById('s-prefix').value,admin_role:document.getElementById('s-admin').value,
    whitelist_role:document.getElementById('s-wlrole').value,auto_kick:document.getElementById('s-kick').checked}})
  }}).then(()=>flash('s-ok'));
}}
</script>
</body></html>"""


@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        if request.form.get("password") == PASSWORD:
            session["auth"] = True
            return redirect("/")
        error = "Wrong password."
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>Login</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:'Segoe UI',sans-serif;background:#1e1f22;color:#dbdee1;display:flex;align-items:center;justify-content:center;min-height:100vh}}
.box{{background:#2b2d31;border-radius:8px;padding:40px;width:340px}}h1{{font-size:20px;text-align:center;margin-bottom:6px;color:#fff}}
p{{color:#949ba4;font-size:14px;text-align:center;margin-bottom:24px}}.err{{color:#ed4245;font-size:13px;margin-bottom:12px;text-align:center}}
label{{font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;color:#b5bac1;display:block;margin-bottom:6px}}
input{{background:#1e1f22;border:1px solid #3f4046;border-radius:4px;padding:10px 12px;color:#dbdee1;font-size:14px;width:100%;outline:none;margin-bottom:16px}}
button{{background:#5865f2;color:#fff;border:none;border-radius:4px;padding:10px;width:100%;font-size:14px;font-weight:600;cursor:pointer}}
button:hover{{background:#4752c4}}</style></head>
<body><div class="box"><h1>&#9889; Whitelist Bot</h1><p>Enter your password to continue</p>
{'<div class="err">' + error + '</div>' if error else ''}
<form method="POST"><label>Password</label><input type="password" name="password" placeholder="Enter password">
<button type="submit">Login</button></form></div></body></html>"""


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/remove/<uid>", methods=["POST"])
def remove_user(uid):
    if not session.get("auth"):
        return redirect("/login")
    wl = load_wl()
    wl.pop(uid, None)
    save_wl(wl)
    return redirect("/")

@app.route("/api/embed", methods=["POST"])
def api_embed():
    if not session.get("auth"):
        return jsonify({}), 401
    cfg = load_cfg()
    cfg["embed"] = request.json
    save_cfg(cfg)
    return jsonify({"ok": True})

@app.route("/api/settings", methods=["POST"])
def api_settings():
    if not session.get("auth"):
        return jsonify({}), 401
    cfg = load_cfg()
    d = request.json
    cfg["prefix"]         = d.get("prefix", "!")
    cfg["admin_role"]     = d.get("admin_role", "Admin")
    cfg["whitelist_role"] = d.get("whitelist_role", "whitelisted")
    cfg["auto_kick"]      = d.get("auto_kick", False)
    save_cfg(cfg)
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
