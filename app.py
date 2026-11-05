import json, os, subprocess, sys  # noqa
from flask import Flask, request, redirect, session, jsonify

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret")
PASSWORD     = os.getenv("DASHBOARD_PASSWORD", "admin")
CONFIG_FILE  = "config.json"
WL_FILE      = "whitelist.json"

DEFAULT_CONFIG = {
    "prefix": "!",
    "admin_role": "Admin",
    "whitelist_role": "whitelisted",
    "auto_kick": False,
    "embed": {
        "title": "✅ You've been whitelisted!",
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


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Whitelist Dashboard</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:#1e1f22;color:#dbdee1;min-height:100vh;display:flex}
a{color:inherit;text-decoration:none}

/* sidebar */
.sidebar{width:220px;background:#2b2d31;padding:20px 0;display:flex;flex-direction:column;flex-shrink:0}
.sidebar-logo{padding:0 16px 20px;font-size:16px;font-weight:700;color:#fff;border-bottom:1px solid #3f4046}
.sidebar-logo span{color:#5865f2}
.nav-item{padding:10px 16px;cursor:pointer;border-radius:4px;margin:2px 8px;font-size:14px;color:#949ba4;transition:.15s}
.nav-item:hover{background:#35373c;color:#dbdee1}
.nav-item.active{background:#404249;color:#fff}

/* main */
.main{flex:1;padding:32px;overflow-y:auto}
.page{display:none}
.page.active{display:block}
h1{font-size:22px;font-weight:700;color:#fff;margin-bottom:6px}
.subtitle{color:#949ba4;font-size:14px;margin-bottom:28px}

/* cards */
.card{background:#2b2d31;border-radius:8px;padding:24px;margin-bottom:20px}
.card h2{font-size:14px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;color:#949ba4;margin-bottom:16px}

/* form */
.form-row{display:flex;gap:16px;margin-bottom:16px;flex-wrap:wrap}
.form-group{display:flex;flex-direction:column;gap:6px;flex:1;min-width:180px}
label{font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;color:#b5bac1}
input[type=text],textarea{background:#1e1f22;border:1px solid #3f4046;border-radius:4px;padding:10px 12px;color:#dbdee1;font-size:14px;font-family:inherit;outline:none;transition:.15s}
input[type=text]:focus,textarea:focus{border-color:#5865f2}
textarea{resize:vertical;min-height:80px}
input[type=color]{width:50px;height:36px;border:none;border-radius:4px;cursor:pointer;background:none;padding:0}
.toggle-row{display:flex;align-items:center;justify-content:space-between;padding:12px 0;border-bottom:1px solid #3f4046}
.toggle-row:last-child{border-bottom:none}
.toggle-label{font-size:14px}
.toggle-desc{font-size:12px;color:#949ba4;margin-top:2px}
.toggle{position:relative;width:40px;height:22px;flex-shrink:0}
.toggle input{opacity:0;width:0;height:0}
.slider{position:absolute;inset:0;background:#4e5058;border-radius:11px;cursor:pointer;transition:.2s}
.slider:before{content:"";position:absolute;width:16px;height:16px;left:3px;top:3px;background:#fff;border-radius:50%;transition:.2s}
input:checked+.slider{background:#5865f2}
input:checked+.slider:before{transform:translateX(18px)}
.btn{padding:10px 20px;border:none;border-radius:4px;cursor:pointer;font-size:14px;font-weight:600;transition:.15s}
.btn-primary{background:#5865f2;color:#fff}
.btn-primary:hover{background:#4752c4}
.btn-danger{background:#ed4245;color:#fff}
.btn-danger:hover{background:#c03537}
.save-row{display:flex;align-items:center;gap:12px;margin-top:4px}
.saved-msg{color:#3ba55d;font-size:13px;display:none}

/* embed preview */
.preview-wrap{background:#313338;border-radius:8px;padding:16px}
.preview-label{font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:#949ba4;margin-bottom:12px}
.discord-embed{display:flex;border-radius:4px;overflow:hidden;max-width:440px}
.embed-bar{width:4px;flex-shrink:0;background:#57f287}
.embed-body{background:#2b2d31;padding:12px 16px;flex:1}
.embed-title{font-weight:700;font-size:15px;color:#fff;margin-bottom:6px}
.embed-desc{font-size:14px;color:#dbdee1;line-height:1.5;white-space:pre-wrap}
.embed-img{width:100%;border-radius:4px;margin-top:10px;display:none}
.embed-footer{font-size:12px;color:#949ba4;margin-top:10px;padding-top:8px;border-top:1px solid #3f4046}

/* whitelist table */
.wl-table{width:100%;border-collapse:collapse}
.wl-table th{text-align:left;padding:10px 12px;font-size:12px;text-transform:uppercase;letter-spacing:.5px;color:#949ba4;border-bottom:1px solid #3f4046}
.wl-table td{padding:10px 12px;font-size:14px;border-bottom:1px solid #26272b}
.wl-table tr:last-child td{border-bottom:none}
.wl-table tr:hover td{background:#35373c}
.empty-state{text-align:center;padding:40px;color:#949ba4;font-size:14px}
.badge{background:#3ba55d;color:#fff;font-size:11px;padding:2px 8px;border-radius:10px}

/* login */
.login-wrap{display:flex;align-items:center;justify-content:center;min-height:100vh;width:100%;background:#1e1f22}
.login-box{background:#2b2d31;border-radius:8px;padding:40px;width:360px}
.login-box h1{font-size:20px;text-align:center;margin-bottom:6px}
.login-box p{color:#949ba4;font-size:14px;text-align:center;margin-bottom:28px}
.login-box .form-group{margin-bottom:16px}
.login-box .btn{width:100%}
.error{color:#ed4245;font-size:13px;margin-bottom:12px;text-align:center}
</style>
</head>
<body>

{% if not logged_in %}
<div class="login-wrap">
  <div class="login-box">
    <h1>Whitelist Dashboard</h1>
    <p>Enter your password to continue</p>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    <form method="POST" action="/login">
      <div class="form-group">
        <label>Password</label>
        <input type="text" name="password" placeholder="Enter password" autocomplete="off">
      </div>
      <button class="btn btn-primary">Login</button>
    </form>
  </div>
</div>

{% else %}
<div class="sidebar">
  <div class="sidebar-logo">⚡ <span>Whitelist</span> Bot</div>
  <div style="padding:16px 8px 8px;font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:#5c5f66;padding-left:16px">Configuration</div>
  <div class="nav-item active" onclick="showPage('embed',this)">🎨 Embed</div>
  <div class="nav-item" onclick="showPage('settings',this)">⚙️ Settings</div>
  <div class="nav-item" onclick="showPage('whitelist',this)">📋 Whitelist</div>
  <div style="margin-top:auto;padding:16px">
    <a href="/logout"><div class="nav-item" style="margin:0;color:#ed4245">🚪 Logout</div></a>
  </div>
</div>

<div class="main">

  <!-- EMBED PAGE -->
  <div class="page active" id="page-embed">
    <h1>Embed Settings</h1>
    <div class="subtitle">Customize the message shown when someone types <strong>wl</strong></div>

    <div style="display:flex;gap:20px;flex-wrap:wrap">
      <div style="flex:1;min-width:300px">
        <div class="card">
          <h2>Embed Content</h2>
          <div class="form-group" style="margin-bottom:16px">
            <label>Title</label>
            <input type="text" id="e-title" placeholder="✅ You've been whitelisted!" oninput="updatePreview()">
          </div>
          <div class="form-group" style="margin-bottom:16px">
            <label>Description</label>
            <textarea id="e-desc" placeholder="Welcome! You now have access to the server." oninput="updatePreview()"></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Accent Color</label>
              <input type="color" id="e-color" value="#57F287" oninput="updatePreview()">
            </div>
            <div class="form-group">
              <label>Footer Text</label>
              <input type="text" id="e-footer" placeholder="Whitelisted" oninput="updatePreview()">
            </div>
          </div>
          <div class="form-group" style="margin-bottom:16px">
            <label>Banner Image URL</label>
            <input type="text" id="e-image" placeholder="https://..." oninput="updatePreview()">
          </div>
          <div class="save-row">
            <button class="btn btn-primary" onclick="saveEmbed()">Save Changes</button>
            <span class="saved-msg" id="embed-saved">✓ Saved!</span>
          </div>
        </div>
      </div>

      <div style="flex:1;min-width:280px">
        <div class="card">
          <h2>Live Preview</h2>
          <div class="preview-wrap">
            <div class="preview-label">Discord Message Preview</div>
            <div class="discord-embed">
              <div class="embed-bar" id="prev-bar"></div>
              <div class="embed-body">
                <div class="embed-title" id="prev-title"></div>
                <div class="embed-desc" id="prev-desc"></div>
                <img class="embed-img" id="prev-img" src="">
                <div class="embed-footer" id="prev-footer" style="display:none"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- SETTINGS PAGE -->
  <div class="page" id="page-settings">
    <h1>Bot Settings</h1>
    <div class="subtitle">Configure roles, prefix, and behavior</div>

    <div class="card">
      <h2>Command Settings</h2>
      <div class="form-row">
        <div class="form-group">
          <label>Command Prefix</label>
          <input type="text" id="s-prefix" placeholder="!">
        </div>
        <div class="form-group">
          <label>Admin Role Name</label>
          <input type="text" id="s-admin" placeholder="Admin">
        </div>
        <div class="form-group">
          <label>Whitelist Role Name</label>
          <input type="text" id="s-wlrole" placeholder="whitelisted">
        </div>
      </div>
    </div>

    <div class="card">
      <h2>Behavior</h2>
      <div class="toggle-row">
        <div>
          <div class="toggle-label">Auto-Kick on Join</div>
          <div class="toggle-desc">Kick members who join but aren't whitelisted</div>
        </div>
        <label class="toggle">
          <input type="checkbox" id="s-autokick">
          <span class="slider"></span>
        </label>
      </div>
    </div>

    <div class="save-row">
      <button class="btn btn-primary" onclick="saveSettings()">Save Changes</button>
      <span class="saved-msg" id="settings-saved">✓ Saved!</span>
    </div>
  </div>

  <!-- WHITELIST PAGE -->
  <div class="page" id="page-whitelist">
    <h1>Whitelist</h1>
    <div class="subtitle">View and manage whitelisted users</div>

    <div class="card">
      <h2>Whitelisted Users <span class="badge" id="wl-count">0</span></h2>
      <table class="wl-table">
        <thead>
          <tr>
            <th>User</th>
            <th>Added By</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody id="wl-body">
          <tr><td colspan="3" class="empty-state">Loading...</td></tr>
        </tbody>
      </table>
    </div>
  </div>

</div><!-- /main -->
{% endif %}

<script>
function showPage(name, el) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('page-' + name).classList.add('active');
  el.classList.add('active');
  if (name === 'whitelist') loadWhitelist();
}

function updatePreview() {
  const title = document.getElementById('e-title').value || '✅ You\'ve been whitelisted!';
  const desc  = document.getElementById('e-desc').value || 'Welcome!';
  const color = document.getElementById('e-color').value;
  const footer= document.getElementById('e-footer').value;
  const img   = document.getElementById('e-image').value;

  document.getElementById('prev-title').textContent = title;
  document.getElementById('prev-desc').textContent  = desc;
  document.getElementById('prev-bar').style.background = color;

  const imgEl = document.getElementById('prev-img');
  if (img) { imgEl.src = img; imgEl.style.display = 'block'; }
  else { imgEl.style.display = 'none'; }

  const footerEl = document.getElementById('prev-footer');
  if (footer) { footerEl.textContent = footer; footerEl.style.display = 'block'; }
  else { footerEl.style.display = 'none'; }
}

function saveEmbed() {
  const data = {
    title:     document.getElementById('e-title').value,
    description: document.getElementById('e-desc').value,
    color:     document.getElementById('e-color').value,
    footer:    document.getElementById('e-footer').value,
    image_url: document.getElementById('e-image').value
  };
  fetch('/api/embed', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)})
    .then(() => { const m = document.getElementById('embed-saved'); m.style.display='inline'; setTimeout(()=>m.style.display='none',2000); });
}

function saveSettings() {
  const data = {
    prefix:         document.getElementById('s-prefix').value,
    admin_role:     document.getElementById('s-admin').value,
    whitelist_role: document.getElementById('s-wlrole').value,
    auto_kick:      document.getElementById('s-autokick').checked
  };
  fetch('/api/settings', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)})
    .then(() => { const m = document.getElementById('settings-saved'); m.style.display='inline'; setTimeout(()=>m.style.display='none',2000); });
}

function loadWhitelist() {
  fetch('/api/whitelist').then(r=>r.json()).then(data => {
    const body = document.getElementById('wl-body');
    const keys = Object.keys(data);
    document.getElementById('wl-count').textContent = keys.length;
    if (!keys.length) {
      body.innerHTML = '<tr><td colspan="3" class="empty-state">No whitelisted users yet.</td></tr>';
      return;
    }
    body.innerHTML = keys.map(uid => `
      <tr>
        <td><strong>${data[uid].tag || uid}</strong><br><small style="color:#949ba4">${uid}</small></td>
        <td>${data[uid].by || '?'}</td>
        <td><button class="btn btn-danger" style="padding:6px 12px;font-size:12px" onclick="removeUser('${uid}')">Remove</button></td>
      </tr>`).join('');
  });
}

function removeUser(uid) {
  if (!confirm('Remove this user from the whitelist?')) return;
  fetch('/api/whitelist/' + uid, {method:'DELETE'}).then(() => loadWhitelist());
}

// load current config into forms
fetch('/api/config').then(r=>r.json()).then(cfg => {
  document.getElementById('e-title').value  = cfg.embed?.title || '';
  document.getElementById('e-desc').value   = cfg.embed?.description || '';
  document.getElementById('e-color').value  = cfg.embed?.color || '#57F287';
  document.getElementById('e-footer').value = cfg.embed?.footer || '';
  document.getElementById('e-image').value  = cfg.embed?.image_url || '';
  document.getElementById('s-prefix').value  = cfg.prefix || '!';
  document.getElementById('s-admin').value   = cfg.admin_role || 'Admin';
  document.getElementById('s-wlrole').value  = cfg.whitelist_role || 'whitelisted';
  document.getElementById('s-autokick').checked = cfg.auto_kick || false;
  updatePreview();
});
</script>

</body>
</html>"""


@app.route("/")
def index():
    if not session.get("auth"):
        return redirect("/login")
    from flask import render_template_string
    return render_template_string(DASHBOARD_HTML, logged_in=True, error=None)

@app.route("/login", methods=["GET", "POST"])
def login():
    from flask import render_template_string
    if request.method == "POST":
        if request.form.get("password") == PASSWORD:
            session["auth"] = True
            return redirect("/")
        return render_template_string(DASHBOARD_HTML, logged_in=False, error="Wrong password.")
    return render_template_string(DASHBOARD_HTML, logged_in=False, error=None)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/api/config")
def api_config():
    if not session.get("auth"):
        return jsonify({}), 401
    return jsonify(load_cfg())

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

@app.route("/api/whitelist")
def api_whitelist():
    if not session.get("auth"):
        return jsonify({}), 401
    return jsonify(load_wl())

@app.route("/api/whitelist/<uid>", methods=["DELETE"])
def api_remove(uid):
    if not session.get("auth"):
        return jsonify({}), 401
    wl = load_wl()
    wl.pop(uid, None)
    save_wl(wl)
    return jsonify({"ok": True})


if __name__ == "__main__":
    subprocess.Popen([sys.executable, "bot.py"])
    port = int(os.getenv("PORT", 5000))
    print(f"Starting Flask on port {port}")
    app.run(host="0.0.0.0", port=port)
