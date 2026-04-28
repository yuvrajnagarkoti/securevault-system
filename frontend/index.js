/**
 * SecureVault Frontend — Premium Dark UI
 * Handles routing, auth, files, users, roles, audit, permissions.
 */
const API = 'http://localhost:8000/api';
let currentUser = null;
let activeNav = 'dashboard';

// ===== Utilities =====
function toast(msg, type = 'info') {
  const c = document.getElementById('toast-container');
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(() => t.remove(), 3200);
}

function headers(json = false) {
  const h = { 'Authorization': `Bearer ${localStorage.getItem('jwt')}` };
  if (json) h['Content-Type'] = 'application/json';
  return h;
}

async function api(path, opts = {}) {
  try {
    const r = await fetch(`${API}${path}`, opts);
    if (r.status === 401) { logout(); return null; }
    const ct = r.headers.get('content-type') || '';
    if (ct.includes('application/json')) {
      const data = await r.json();
      if (!r.ok) { toast(data.detail || 'Request failed', 'error'); return null; }
      return data;
    }
    if (!r.ok) { toast('Request failed', 'error'); return null; }
    return r;
  } catch (e) { toast('Network error: ' + e.message, 'error'); return null; }
}

function fmtSize(b) {
  if (b < 1024) return b + ' B';
  if (b < 1048576) return (b / 1024).toFixed(1) + ' KB';
  if (b < 1073741824) return (b / 1048576).toFixed(1) + ' MB';
  return (b / 1073741824).toFixed(1) + ' GB';
}

function fmtDate(d) {
  if (!d) return '—';
  try {
    // If the string doesn't have a timezone indicator, assume it's UTC if it comes from our backend
    // but the backend is now appending 'Z' so this is just a fallback.
    let dateStr = d;
    if (typeof d === 'string' && !d.includes('Z') && !d.includes('+')) {
      dateStr += 'Z';
    }
    const date = new Date(dateStr);
    if (isNaN(date)) return '—';
    return date.toLocaleString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric', 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit',
      hour12: true 
    });
  } catch(e) { return '—'; }
}

function roleBadge(role) {
  const cls = { 'Admin': 'badge-blue', 'Manager': 'badge-teal', 'Standard User': 'badge-gray' };
  const icons = { 'Admin': 'admin_panel_settings', 'Manager': 'shield_person', 'Standard User': 'person' };
  return `<span class="badge ${cls[role] || 'badge-gray'}">
    <span class="material-symbols-outlined" style="font-size:14px">${icons[role] || 'person'}</span>
    ${role}
  </span>`;
}

function initials(name) { return name.charAt(0).toUpperCase(); }

// ===== Init =====
function init() {
  if (localStorage.getItem('jwt')) { loadDashboard(); } else { showAuth(); }
}

// ===== Auth =====
function showAuth(mode = 'login') {
  document.getElementById('app').innerHTML = `
    <div class="auth-page">
      <div class="auth-card">
        <div class="logo">
          <h1><span class="material-symbols-outlined" style="font-size:32px">shield_lock</span> SecureVault</h1>
          <p>Secure Enterprise Management System</p>
        </div>
        <div id="auth-form"></div>
      </div>
    </div>`;
  mode === 'login' ? renderLogin() : renderRegister();
}

function renderLogin() {
  document.getElementById('auth-form').innerHTML = `
    <h2 style="margin-bottom:24px;font-weight:700">Access Portal</h2>
    <div id="login-error" class="field-error" style="text-align:center;margin-bottom:16px;font-size:13px"></div>
    <div class="form-group"><label>Operative ID</label><input type="text" id="username" placeholder="Username" autocomplete="username"></div>
    <div class="form-group"><label>Security Phrase</label>
      <div style="position:relative">
        <input type="password" id="password" placeholder="Password" autocomplete="current-password">
        <button type="button" onclick="togglePwd('password')" class="btn-icon" style="position:absolute;right:4px;top:50%;transform:translateY(-50%);border:none" title="Show/Hide Password">
          <span class="material-symbols-outlined" style="font-size:18px" id="pwd-eye">visibility_off</span>
        </button>
      </div>
    </div>
    <button class="btn btn-primary full glow-hover" id="login-btn" onclick="login()">Authenticate</button>
    <div class="auth-footer"><span>New operative? </span><a onclick="renderRegister()">Provision Account</a></div>`;
  document.getElementById('password').addEventListener('keydown', e => { if (e.key === 'Enter') login(); });
  document.getElementById('username').addEventListener('keydown', e => { if (e.key === 'Enter') document.getElementById('password').focus(); });
}

function togglePwd(id) {
  const inp = document.getElementById(id);
  const icon = inp.parentElement.querySelector('.material-symbols-outlined');
  if (inp.type === 'password') { inp.type = 'text'; icon.textContent = 'visibility'; }
  else { inp.type = 'password'; icon.textContent = 'visibility_off'; }
}

function renderRegister() {
  document.getElementById('auth-form').innerHTML = `
    <h2 style="margin-bottom:24px;font-weight:700">Provision Account</h2>
    <div id="register-error" class="field-error" style="text-align:center;margin-bottom:16px;font-size:13px"></div>
    <div class="form-group"><label>Username</label><input type="text" id="username" placeholder="Choose a username" oninput="valUser()" autocomplete="username"><div class="field-error" id="username-error"></div></div>
    <div class="form-group"><label>Password</label>
      <div style="position:relative">
        <input type="password" id="password" placeholder="Create a password" oninput="valPass()" autocomplete="new-password">
        <button type="button" onclick="togglePwd('password')" class="btn-icon" style="position:absolute;right:4px;top:50%;transform:translateY(-50%);border:none" title="Show/Hide Password">
          <span class="material-symbols-outlined" style="font-size:18px">visibility_off</span>
        </button>
      </div>
      <div class="field-error" id="password-error"></div>
    </div>
    <button class="btn btn-primary full glow-hover" onclick="register()">Create Operative</button>
    <div class="auth-footer"><span>Already provisioned? </span><a onclick="renderLogin()">Sign in</a></div>`;
}

function valUser() {
  const u = document.getElementById('username'), e = document.getElementById('username-error');
  if (!u.value) { u.classList.remove('error'); e.textContent = ''; return false; }
  if (u.value.length < 3) { u.classList.add('error'); e.textContent = 'At least 3 characters'; return false; }
  if (!/^[a-zA-Z][a-zA-Z0-9]*$/.test(u.value)) { u.classList.add('error'); e.textContent = 'Start with letter, alphanumeric only'; return false; }
  u.classList.remove('error'); e.textContent = ''; return true;
}

function valPass() {
  const p = document.getElementById('password'), e = document.getElementById('password-error');
  if (!p.value) { p.classList.remove('error'); e.textContent = ''; return false; }
  const errs = [];
  if (p.value.length < 8) errs.push('8+ chars');
  if (!/[A-Z]/.test(p.value)) errs.push('1 uppercase');
  if (!/[a-z]/.test(p.value)) errs.push('1 lowercase');
  if (!/[0-9]/.test(p.value)) errs.push('1 number');
  if (!/[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\/~`]/.test(p.value)) errs.push('1 special char');
  if (errs.length) { p.classList.add('error'); e.textContent = 'Need: ' + errs.join(', '); return false; }
  p.classList.remove('error'); e.textContent = ''; return true;
}

async function login() {
  const u = document.getElementById('username').value.trim(), p = document.getElementById('password').value;
  const errEl = document.getElementById('login-error');
  errEl.textContent = '';
  if (!u || !p) { errEl.textContent = 'Please fill in all fields.'; return; }
  const btn = document.getElementById('login-btn');
  btn.disabled = true; btn.textContent = 'Authenticating...';
  try {
    const r = await fetch(`${API}/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: u, password: p }) });
    const data = await r.json();
    btn.disabled = false; btn.textContent = 'Authenticate';
    if (r.status === 423) {
      errEl.innerHTML = `<span style="color:var(--warn)">&#128274; ${data.detail || 'Account is locked. Try again later.'}</span>`;
      return;
    }
    if (r.status === 429) {
      errEl.textContent = 'Too many login attempts. Please wait before trying again.';
      return;
    }
    if (!r.ok) {
      errEl.textContent = data.detail || 'Invalid username or password.';
      return;
    }
    localStorage.setItem('jwt', data.access_token); localStorage.setItem('user', JSON.stringify(data.user));
    toast('Welcome back, ' + data.user.username, 'success'); loadDashboard();
  } catch (e) {
    btn.disabled = false; btn.textContent = 'Authenticate';
    errEl.textContent = 'Network error. Please check your connection.';
  }
}

async function register() {
  if (!valUser() || !valPass()) { toast('Fix validation errors', 'error'); return; }
  const u = document.getElementById('username').value, p = document.getElementById('password').value;
  const data = await api('/register', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: u, password: p }) });
  if (data) { toast('Account created! Please sign in.', 'success'); renderLogin(); }
}

function logout() { localStorage.removeItem('jwt'); localStorage.removeItem('user'); currentUser = null; showAuth(); }

// ===== Dashboard =====
function loadDashboard() {
  currentUser = JSON.parse(localStorage.getItem('user'));
  const isPrivileged = ['Admin', 'Manager'].includes(currentUser.role);
  document.getElementById('app').innerHTML = `
    <div class="dashboard-layout">
      <aside class="sidebar">
        <div class="sidebar-logo">
          <span class="material-symbols-outlined" style="font-size:24px;color:var(--accent)">shield</span>
          <h1>SecureVault</h1>
        </div>
        <nav class="sidebar-nav">
          <div class="nav-section">Main Interface</div>
          <button class="nav-item active" data-page="dashboard" onclick="navigate('dashboard')"><span class="material-symbols-outlined">dashboard</span><span>Dashboard</span></button>
          <button class="nav-item" data-page="files" onclick="navigate('files')"><span class="material-symbols-outlined">folder_managed</span><span>Vault Explorer</span></button>
          <button class="nav-item" data-page="upload" onclick="navigate('upload')"><span class="material-symbols-outlined">cloud_upload</span><span>Secure Upload</span></button>
          ${isPrivileged ? `
          <div class="nav-section">Control Center</div>
          <button class="nav-item" data-page="users" onclick="navigate('users')"><span class="material-symbols-outlined">group</span><span>User Management</span></button>
          <button class="nav-item" data-page="roles" onclick="navigate('roles')"><span class="material-symbols-outlined">admin_panel_settings</span><span>Roles & Policies</span></button>
          <button class="nav-item" data-page="audit" onclick="navigate('audit')"><span class="material-symbols-outlined">receipt_long</span><span>Audit Logs</span></button>
          ` : ''}
        </nav>
        <div class="sidebar-footer">
          <div class="user-badge">
            <div class="user-avatar">${initials(currentUser.username)}</div>
            <div class="info"><div class="name">${currentUser.username}</div><div class="role">${currentUser.role}</div></div>
            <button class="btn-icon" onclick="logout()" title="Terminate Session"><span class="material-symbols-outlined">logout</span></button>
          </div>
        </div>
      </aside>
      <main class="main-content" id="content"></main>
    </div>`;
  navigate('dashboard');
}

function navigate(page) {
  activeNav = page;
  document.querySelectorAll('.nav-item').forEach(b => { b.classList.toggle('active', b.dataset.page === page); });
  const pages = { 
    dashboard: showDashboardOverview,
    files: showFiles, 
    upload: showUpload, 
    users: showUsers, 
    roles: showRoles, 
    audit: showAudit 
  };
  (pages[page] || showDashboardOverview)();
}

async function showDashboardOverview() {
  const content = document.getElementById('content');
  content.innerHTML = `
    <div class="page-header">
      <div>
        <h2>System Dashboard</h2>
        <p>Live security metrics and system status.</p>
      </div>
      <button class="btn btn-success glow-hover" onclick="navigate('upload')">
        <span class="material-symbols-outlined">upload</span> Secure Upload
      </button>
    </div>
    
    <div class="bento-grid">
      <div class="bento-card md-8">
        <span class="material-symbols-outlined icon-bg">data_usage</span>
        <div style="display:flex;justify-content:space-between;align-items:start">
          <div>
            <h3 style="font-size:18px;font-weight:700">Vault Capacity</h3>
            <p style="font-size:12px;color:var(--text-muted)">Encrypted volume status</p>
          </div>
          <span class="badge badge-active badge-pulse">Online</span>
        </div>
        <div class="progress-container" style="margin-top:40px">
          <div style="display:flex;justify-content:space-between;margin-bottom:8px">
            <span style="font-size:24px;font-weight:800;color:var(--accent-secondary)">84%</span>
            <span class="mono" style="font-size:12px;color:var(--text-muted)">840TB / 1PB</span>
          </div>
          <div class="progress-bar"><div class="progress-fill" style="width:84%"></div></div>
        </div>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-top:32px;padding-top:20px;border-top:1px solid var(--border-glass)">
          <div><p class="mono" style="font-size:10px;color:var(--text-muted)">DOCUMENTS</p><p style="font-weight:700">320TB</p></div>
          <div><p class="mono" style="font-size:10px;color:var(--text-muted)">SYSTEM</p><p style="font-weight:700">110TB</p></div>
          <div><p class="mono" style="font-size:10px;color:var(--text-muted)">ENCRYPTED</p><p style="font-weight:700">410TB</p></div>
        </div>
      </div>
      
      <div class="bento-card md-4" style="justify-content:center;text-align:center">
        <div style="width:64px;height:64px;background:rgba(0,223,216,0.1);border:1px solid rgba(0,223,216,0.2);border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 16px">
          <span class="material-symbols-outlined" style="font-size:32px;color:var(--accent-secondary)">verified_user</span>
        </div>
        <h3 style="font-size:20px;font-weight:800;margin-bottom:4px">System Secure</h3>
        <p style="font-size:13px;color:var(--text-muted)">Integrity Verified</p>
        <div style="margin-top:24px;display:grid;grid-template-columns:1fr 1fr;gap:12px">
          <button class="btn btn-secondary" onclick="navigate('files')" style="padding:10px"><span class="material-symbols-outlined" style="font-size:18px">folder</span> Explorer</button>
          <button class="btn btn-secondary" onclick="navigate('audit')" style="padding:10px"><span class="material-symbols-outlined" style="font-size:18px">history</span> Logs</button>
        </div>
      </div>
      
      <div class="bento-card md-12">
        <h3 style="font-size:18px;font-weight:700;margin-bottom:20px">Security Overview</h3>
        <div class="stats-grid" style="margin-bottom:0">
          <div class="stat-card">
            <div class="label">Total Files</div>
            <div class="value" id="stat-files">...</div>
          </div>
          <div class="stat-card">
            <div class="label">Active Operatives</div>
            <div class="value" id="stat-users">...</div>
          </div>
          <div class="stat-card">
            <div class="label">Audit Events</div>
            <div class="value" id="stat-logs">...</div>
          </div>
        </div>
      </div>
    </div>`;
  loadDashboardStats();
}

async function loadDashboardStats() {
  const [f, u, a] = await Promise.all([
    api('/files', { headers: headers() }),
    api('/users', { headers: headers() }),
    api('/audit/statistics', { headers: headers() })
  ]);
  if (f) document.getElementById('stat-files').textContent = f.files.length;
  if (u) document.getElementById('stat-users').textContent = u.users.length;
  if (a) document.getElementById('stat-logs').textContent = a.statistics.total_logs;
}

// ===== Files =====
async function showFiles() {
  const content = document.getElementById('content');
  content.innerHTML = `
    <div class="page-header">
      <div>
        <h2>Vault Explorer</h2>
        <p>Access and manage encrypted corporate assets.</p>
      </div>
      <div class="actions">
        <button class="btn btn-secondary" onclick="showFiles()"><span class="material-symbols-outlined">refresh</span> Refresh</button>
      </div>
    </div>
    <div class="table-wrapper">
      <div id="file-list">
        <div class="skel-row"><div class="skel skel-cell" style="flex:2"></div><div class="skel skel-cell"></div><div class="skel skel-cell" style="flex:0.5"></div><div class="skel skel-cell"></div></div>
        <div class="skel-row"><div class="skel skel-cell" style="flex:2"></div><div class="skel skel-cell"></div><div class="skel skel-cell" style="flex:0.5"></div><div class="skel skel-cell"></div></div>
        <div class="skel-row"><div class="skel skel-cell" style="flex:2"></div><div class="skel skel-cell"></div><div class="skel skel-cell" style="flex:0.5"></div><div class="skel skel-cell"></div></div>
      </div>
    </div>`;
  
  const data = await api('/files', { headers: headers() });
  if (!data) return;
  const fl = document.getElementById('file-list');
  if (!data.files.length) { 
    fl.innerHTML = `
      <div class="empty-state">
        <span class="material-symbols-outlined icon" style="font-size:64px;color:var(--accent);opacity:0.2">folder_off</span>
        <h3>Vault Empty</h3>
        <p>No encrypted assets found in this sector.</p>
        <button class="btn btn-primary glow-hover" style="margin-top:24px" onclick="navigate('upload')">Initialize Upload</button>
      </div>`; 
    return; 
  }
  
  const isPriv = ['Admin', 'Manager'].includes(currentUser.role);
  fl.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Asset Specification</th>
          <th>Size</th>
          <th>Rev</th>
          <th>Timestamp</th>
          <th style="text-align:right">Command</th>
        </tr>
      </thead>
      <tbody>
        ${data.files.map(f => {
          const own = f.owner_id === currentUser.user_id;
          const canManage = isPriv || own;
          return `
            <tr>
              <td>
                <div class="operative-info">
                  <span class="material-symbols-outlined" style="color:var(--accent)">description</span>
                  <div>
                    <div style="color:var(--text-primary);font-weight:600">${f.filename}</div>
                    <div class="operative-id">SHA-256 Verified</div>
                  </div>
                </div>
              </td>
              <td class="mono" style="font-size:13px">${fmtSize(f.size)}</td>
              <td><span class="badge badge-active" style="padding:2px 8px">v${f.version}</span></td>
              <td class="mono" style="font-size:12px;color:var(--text-muted)">${fmtDate(f.created_at)}</td>
              <td>
                <div class="actions" style="justify-content:flex-end">
                  ${f.can_download ? `<button class="btn-icon" onclick="downloadFile(${f.file_id},'${f.filename}')" title="Download"><span class="material-symbols-outlined">download</span></button>` : ''}
                  ${canManage ? `
                    <button class="btn-icon" onclick="promptRename(${f.file_id},'${f.filename}')" title="Rename"><span class="material-symbols-outlined">edit</span></button>
                    <button class="btn-icon" onclick="deleteFile(${f.file_id})" title="Purge" style="color:var(--danger)"><span class="material-symbols-outlined">delete</span></button>
                  ` : ''}
                  ${isPriv ? `<button class="btn-icon" onclick="managePerms(${f.file_id},'${f.filename}')" title="Access Control"><span class="material-symbols-outlined">key</span></button>` : ''}
                </div>
              </td>
            </tr>`;
        }).join('')}
      </tbody>
    </table>`;
}

async function downloadFile(id, name) {
  const r = await fetch(`${API}/download/${id}`, { headers: headers() });
  if (r.ok) { const b = await r.blob(); const u = URL.createObjectURL(b); const a = document.createElement('a'); a.href = u; a.download = name; a.click(); toast('Download started', 'success'); }
  else toast('Download failed', 'error');
}

function promptRename(id, name) {
  document.body.insertAdjacentHTML('beforeend', `
    <div class="modal-overlay" id="rename-modal" onclick="if(event.target===this)this.remove()">
      <div class="modal"><h3>Rename File</h3>
        <div class="form-group"><label>New Filename</label><input type="text" id="new-filename" value="${name}"></div>
        <div class="modal-actions"><button class="btn btn-secondary" onclick="document.getElementById('rename-modal').remove()">Cancel</button><button class="btn btn-primary" onclick="doRename(${id})">Rename</button></div>
      </div></div>`);
  document.getElementById('new-filename').focus();
}

async function doRename(id) {
  const n = document.getElementById('new-filename').value;
  if (!n) return;
  const data = await api(`/files/${id}/rename`, { method: 'PUT', headers: headers(true), body: JSON.stringify({ new_filename: n }) });
  if (data) { document.getElementById('rename-modal').remove(); toast('File renamed', 'success'); showFiles(); }
}

async function deleteFile(id) {
  if (!confirm('Delete this file?')) return;
  const data = await api(`/files/${id}`, { method: 'DELETE', headers: headers() });
  if (data) { toast('File deleted', 'success'); showFiles(); }
}

// ===== Upload =====
function showUpload() {
  document.getElementById('content').innerHTML = `
    <div class="page-header">
      <div>
        <h2>Secure Ingestion</h2>
        <p>Inject encrypted data into the vault.</p>
      </div>
    </div>
    <div class="bento-card">
      <span class="material-symbols-outlined icon-bg">shield_upload</span>
      <div class="upload-zone vault-inset" id="drop-zone" onclick="document.getElementById('file-input').click()" ondragover="event.preventDefault();this.classList.add('dragover')" ondragleave="this.classList.remove('dragover')" ondrop="handleDrop(event)">
        <span class="material-symbols-outlined" style="font-size:64px;color:var(--accent);margin-bottom:16px">cloud_upload</span>
        <h3 style="font-size:18px;font-weight:700;margin-bottom:8px">Drop Asset Here</h3>
        <p style="color:var(--text-3)">Drag and drop files to initiate secure encryption protocol.</p>
        <button class="btn btn-secondary" style="margin-top:24px">Browse Local Drive</button>
        <input type="file" id="file-input" onchange="handleFileSelect(this)">
      </div>
      <div id="upload-preview" style="margin-top:32px"></div>
    </div>`;
}

function handleDrop(e) {
  e.preventDefault();
  document.getElementById('drop-zone').classList.remove('dragover');
  if (e.dataTransfer.files.length) previewFile(e.dataTransfer.files[0]);
}

function handleFileSelect(input) {
  if (input.files.length) previewFile(input.files[0]);
}

function previewFile(file) {
  document.getElementById('upload-preview').innerHTML = `
    <div class="glass-panel" style="display:flex;align-items:center;gap:20px;padding:24px;border-radius:var(--radius)">
      <div style="width:48px;height:48px;background:var(--accent);border-radius:12px;display:flex;align-items:center;justify-content:center">
        <span class="material-symbols-outlined" style="color:white">description</span>
      </div>
      <div style="flex:1">
        <div style="font-weight:700;color:var(--text-primary);font-size:16px">${file.name}</div>
        <div class="mono" style="font-size:12px;color:var(--text-muted)">${fmtSize(file.size)} • Ready for encryption</div>
      </div>
      <button class="btn btn-success glow-hover" onclick="doUpload()">
        <span class="material-symbols-outlined">lock</span> Finalize Upload
      </button>
    </div>`;
  window._pendingFile = file;
}

async function doUpload() {
  const file = window._pendingFile;
  if (!file) { toast('No file selected', 'error'); return; }
  const fd = new FormData(); fd.append('file', file);
  const data = await api('/upload', { method: 'POST', headers: headers(), body: fd });
  if (data) { toast('File uploaded & encrypted', 'success'); navigate('files'); }
}

// ===== Users =====
async function showUsers() {
  const content = document.getElementById('content');
  content.innerHTML = `
    <div class="page-header">
      <div>
        <h2>Operative Management</h2>
        <p>Review and manage personnel access levels.</p>
      </div>
    </div>
    <div class="table-wrapper">
      <div id="user-list">
        <div class="skel-row"><div class="skel skel-cell" style="flex:2"></div><div class="skel skel-cell"></div><div class="skel skel-cell"></div><div class="skel skel-cell"></div></div>
        <div class="skel-row"><div class="skel skel-cell" style="flex:2"></div><div class="skel skel-cell"></div><div class="skel skel-cell"></div><div class="skel skel-cell"></div></div>
        <div class="skel-row"><div class="skel skel-cell" style="flex:2"></div><div class="skel skel-cell"></div><div class="skel skel-cell"></div><div class="skel skel-cell"></div></div>
      </div>
    </div>`;
    
  const [userData, roleData] = await Promise.all([
    api('/users', { headers: headers() }),
    api('/roles', { headers: headers() })
  ]);
  if (!userData) return;
  const roles = roleData ? roleData.roles : [];
  const ul = document.getElementById('user-list');
  
  const isAdmin = currentUser.role === 'Admin';
  ul.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Operative</th>
          <th>Access Level</th>
          <th>Registry Date</th>
          <th style="text-align:right">Authorization</th>
        </tr>
      </thead>
      <tbody>
        ${userData.users.map(u => {
          let actions = '';
          if (u.user_id !== currentUser.user_id && u.role !== 'Admin') {
            if (isAdmin) {
              const opts = roles.filter(r => r.name !== 'Admin').map(r => `<option value="${r.name}" ${u.role === r.name ? 'selected' : ''}>${r.name}</option>`).join('');
              actions = `<select class="select-styled" onchange="changeRole(${u.user_id}, this.value)">${opts}</select> <button class="btn-icon" style="color:var(--danger)" onclick="deleteUser(${u.user_id},'${u.username}')" title="Revoke Access"><span class="material-symbols-outlined">person_remove</span></button>`;
            } else if (currentUser.role === 'Manager' && u.role === 'Standard User') {
              actions = `<button class="btn btn-sm btn-success" onclick="promoteUser(${u.user_id},'${u.username}')">Elevate</button> <button class="btn-icon" style="color:var(--danger)" onclick="deleteUser(${u.user_id},'${u.username}')" title="Revoke Access"><span class="material-symbols-outlined">person_remove</span></button>`;
            }
          } else if (u.role === 'Admin') { 
            actions = '<span class="badge badge-active" style="color:var(--accent)">System Protected</span>'; 
          }
          
          return `
             <tr>
               <td>
                 <div class="operative-info">
                   <div class="user-avatar" style="width:36px;height:36px">${initials(u.username)}</div>
                   <div>
                     <div style="color:var(--text-primary);font-weight:700">${u.username}</div>
                     <div class="operative-id">ID: 00${u.user_id}</div>
                   </div>
                 </div>
               </td>
               <td>${roleBadge(u.role)}</td>
               <td class="mono" style="font-size:12px;color:var(--text-muted)">${fmtDate(u.created_at)}</td>
               <td>
                 <div class="actions" style="justify-content:flex-end">
                   ${u.is_locked ? `<span class="badge badge-red" style="margin-right:8px"><span class="material-symbols-outlined" style="font-size:12px">lock</span> Locked</span>` : ''}
                   ${u.is_locked && isAdmin ? `<button class="btn btn-sm btn-success" onclick="unlockUser(${u.user_id},'${u.username}')"><span class="material-symbols-outlined" style="font-size:14px">lock_open</span> Unlock</button>` : ''}
                   ${actions}
                 </div>
               </td>
             </tr>`;
         }).join('')}
       </tbody>
     </table>`;
}

async function changeRole(uid, role) {
  const data = await api(`/users/${uid}/role`, { method: 'PUT', headers: headers(true), body: JSON.stringify({ user_id: uid, role }) });
  if (data) { toast('Role updated', 'success'); showUsers(); }
}
async function promoteUser(uid, name) {
  if (!confirm(`Promote ${name} to Manager?`)) return;
  const data = await api(`/users/${uid}/promote`, { method: 'PUT', headers: headers() });
  if (data) { toast(data.message, 'success'); showUsers(); }
}
async function deleteUser(uid, name) {
  if (!confirm(`Delete user ${name}? This cannot be undone.`)) return;
  const data = await api(`/users/${uid}`, { method: 'DELETE', headers: headers() });
  if (data) { toast(data.message, 'success'); showUsers(); }
}
async function unlockUser(uid, name) {
  if (!confirm(`Unlock account for ${name}?`)) return;
  const data = await api(`/users/${uid}/unlock`, { method: 'PUT', headers: headers() });
  if (data) { toast(data.message, 'success'); showUsers(); }
}

// ===== Roles & Policies =====
async function showRoles() {
  const content = document.getElementById('content');
  content.innerHTML = `
    <div class="page-header">
      <div>
        <h2>Access Policies</h2>
        <p>Define and enforce granular role-based permissions.</p>
      </div>
    </div>
    <div class="bento-grid">
      <div class="bento-card md-8">
        <h3 style="font-size:18px;font-weight:700;margin-bottom:24px">Provisioned Roles</h3>
        <div id="role-list" style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
          <div class="glass-panel" style="padding:20px;border-radius:var(--radius-lg)"><div class="skel" style="height:20px;width:60%;margin-bottom:12px"></div><div class="skel" style="height:14px;width:80%"></div></div>
          <div class="glass-panel" style="padding:20px;border-radius:var(--radius-lg)"><div class="skel" style="height:20px;width:50%;margin-bottom:12px"></div><div class="skel" style="height:14px;width:70%"></div></div>
        </div>
      </div>
      <div class="bento-card md-4">
        <h3 style="font-size:18px;font-weight:700;margin-bottom:24px">Policy Designer</h3>
        <div class="form-group"><label>Role Designation</label><input type="text" id="new-role-name" placeholder="e.g. Auditor, Analyst"></div>
        <label style="font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;display:block">Capability Matrix</label>
        <div class="perm-grid" id="perm-grid" style="grid-template-columns:1fr;margin-bottom:24px"></div>
        <button class="btn btn-primary glow-hover" onclick="createRole()">
          <span class="material-symbols-outlined">add_moderator</span> Commit Role
        </button>
      </div>
    </div>`;
    
  const allPerms = ['upload', 'download', 'rename', 'delete', 'view_logs', 'manage_roles'];
  const permIcons = {upload:'cloud_upload',download:'download',rename:'edit',delete:'delete',view_logs:'receipt_long',manage_roles:'admin_panel_settings'};
  document.getElementById('perm-grid').innerHTML = allPerms.map(p => `
    <div class="perm-chip" onclick="var cb=this.querySelector('input');cb.checked=!cb.checked;this.classList.toggle('selected',cb.checked)">
      <input type="checkbox" value="${p}" style="display:none"> 
      <span class="material-symbols-outlined" style="font-size:16px">${permIcons[p]||'check_circle'}</span>
      ${p.replace(/_/g, ' ')}
    </div>`).join('');
    
  const data = await api('/roles', { headers: headers() });
  if (!data) return;
  const protectedRoles = ['Admin', 'Manager', 'Standard User'];
  
  document.getElementById('role-list').innerHTML = data.roles.map(r => `
    <div class="glass-panel" style="padding:20px;border-radius:var(--radius-lg)">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
        <span style="font-weight:700;color:var(--text-1);font-size:14px">${r.name}</span>
        ${!protectedRoles.includes(r.name) ? `<button class="btn-icon" style="color:var(--danger)" onclick="deleteRole(${r.id},'${r.name}')" title="Delete Role"><span class="material-symbols-outlined" style="font-size:16px">delete</span></button>` : `<span class="badge badge-blue" style="font-size:9px">Protected</span>`}
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:5px">
        ${(r.permissions || []).map(p => `<span class="badge badge-gray" style="font-size:10px;padding:3px 8px"><span class="material-symbols-outlined" style="font-size:12px;margin-right:3px">${permIcons[p]||'check'}</span>${p.replace(/_/g,' ')}</span>`).join('')}
      </div>
    </div>`).join('');
}

async function createRole() {
  const name = document.getElementById('new-role-name').value.trim();
  if (!name) { toast('Enter a role name', 'error'); return; }
  if (name.length < 2) { toast('Role name must be at least 2 characters', 'error'); return; }
  const perms = Array.from(document.querySelectorAll('#perm-grid input:checked')).map(i => i.value);
  if (!perms.length) { toast('Select at least one permission', 'error'); return; }
  const data = await api('/roles', { method: 'POST', headers: headers(true), body: JSON.stringify({ name, permissions: perms }) });
  if (data) { toast('Role "' + name + '" created!', 'success'); showRoles(); }
}

async function deleteRole(roleId, roleName) {
  if (!confirm(`Delete role "${roleName}"? Users with this role will need reassignment.`)) return;
  const data = await api(`/roles/${roleId}`, { method: 'DELETE', headers: headers() });
  if (data) { toast('Role deleted', 'success'); showRoles(); }
  else { toast('Cannot delete protected or in-use roles', 'error'); }
}

// ===== Audit Logs =====
async function showAudit() {
  const content = document.getElementById('content');
  content.innerHTML = `
    <div class="page-header">
      <div>
        <h2>Security Audit Logs</h2>
        <p>Immutable ledger of all tactical operations.</p>
      </div>
      <div class="actions">
        <button class="btn btn-secondary" onclick="exportLogs('json')"><span class="material-symbols-outlined">download</span> JSON</button>
        <button class="btn btn-secondary" onclick="exportLogs('csv')"><span class="material-symbols-outlined">download</span> CSV</button>
      </div>
    </div>
    <div class="table-wrapper">
      <div id="audit-list">
        <div class="skel-row"><div class="skel skel-cell"></div><div class="skel skel-cell"></div><div class="skel skel-cell"></div><div class="skel skel-cell"></div><div class="skel skel-cell"></div></div>
        <div class="skel-row"><div class="skel skel-cell"></div><div class="skel skel-cell"></div><div class="skel skel-cell"></div><div class="skel skel-cell"></div><div class="skel skel-cell"></div></div>
        <div class="skel-row"><div class="skel skel-cell"></div><div class="skel skel-cell"></div><div class="skel skel-cell"></div><div class="skel skel-cell"></div><div class="skel skel-cell"></div></div>
      </div>
    </div>`;
    
  const data = await api('/audit/logs', { headers: headers() });
  if (!data) return;
  const al = document.getElementById('audit-list');
  if (!data.logs.length) { 
    al.innerHTML = '<div class="empty-state"><span class="material-symbols-outlined">history</span><h3>No Logs Recorded</h3><p>System activities will appear here.</p></div>'; 
    return; 
  }
  // Sort latest first
  const logs = data.logs.sort((a,b) => new Date(b.timestamp) - new Date(a.timestamp));
  
  al.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Operative</th>
          <th>Action</th>
          <th>Resource</th>
          <th>Source IP</th>
          <th style="text-align:right">Timestamp</th>
        </tr>
      </thead>
      <tbody>
        ${logs.map(l => `
          <tr>
            <td>
              <div class="cell-info">
                <div class="user-avatar" style="width:28px;height:28px;font-size:10px">${initials(l.username)}</div>
                <div style="color:var(--text-1);font-weight:600;font-size:13px">${l.username}</div>
              </div>
            </td>
            <td><span class="badge badge-blue">${l.action}</span></td>
            <td><div class="cell-sub">${l.filename || '—'}</div></td>
            <td class="mono" style="font-size:12px">${l.ip_address}</td>
            <td class="mono" style="text-align:right;font-size:11px;color:var(--text-3)">${fmtDate(l.timestamp)}</td>
          </tr>`).join('')}
      </tbody>
    </table>`;
}

async function exportLogs(fmt) {
  const r = await fetch(`${API}/audit/export/${fmt}`, { headers: headers() });
  if (r.ok) { const b = await r.blob(); const u = URL.createObjectURL(b); const a = document.createElement('a'); a.href = u; a.download = `audit_logs.${fmt}`; a.click(); toast('Export downloaded', 'success'); }
}

// ===== File Permissions =====
async function managePerms(fileId, filename) {
  const content = document.getElementById('content');
  content.innerHTML = `
    <div class="page-header">
      <div>
        <h2>Access Control List</h2>
        <p>Configuring permissions for asset: <span style="color:var(--accent)">${filename}</span></p>
      </div>
      <button class="btn btn-secondary" onclick="showFiles()"><span class="material-symbols-outlined">arrow_back</span> Return</button>
    </div>
    <div class="table-wrapper">
      <div id="perm-list">
        <div style="padding:40px;text-align:center;color:var(--text-muted)">
          <span class="material-symbols-outlined" style="font-size:48px;margin-bottom:16px">key</span>
          <p>Querying access matrix...</p>
        </div>
      </div>
    </div>`;
    
  const [usersData, permsData] = await Promise.all([
    api('/users', { headers: headers() }),
    api(`/files/permissions/${fileId}`, { headers: headers() })
  ]);
  if (!usersData || !permsData) return;
  
  const stdUsers = usersData.users.filter(u => u.role === 'Standard User');
  const permMap = {};
  permsData.permissions.forEach(p => permMap[p.user_id] = p);
  const pl = document.getElementById('perm-list');
  
  if (!stdUsers.length) { 
    pl.innerHTML = '<div class="empty-state"><h3>No Standard Operatives</h3><p>Permissions can only be assigned to standard accounts.</p></div>'; 
    return; 
  }
  
  pl.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Operative</th>
          <th>Read Access</th>
          <th>Write/Down Access</th>
          <th style="text-align:right">Command</th>
        </tr>
      </thead>
      <tbody>
        ${stdUsers.map(u => {
          const p = permMap[u.user_id];
          return `
            <tr>
              <td>
                <div class="operative-info">
                  <div class="user-avatar" style="width:28px;height:28px;font-size:10px">${initials(u.username)}</div>
                  <div style="color:var(--text-primary);font-weight:600;font-size:13px">${u.username}</div>
                </div>
              </td>
              <td><input type="checkbox" id="v-${u.user_id}" ${p && p.can_view ? 'checked' : ''} style="accent-color:var(--accent);width:18px;height:18px"></td>
              <td><input type="checkbox" id="d-${u.user_id}" ${p && p.can_download ? 'checked' : ''} style="accent-color:var(--accent);width:18px;height:18px"></td>
              <td>
                <div class="actions" style="justify-content:flex-end">
                  <button class="btn btn-sm btn-success" onclick="savePerm(${fileId},${u.user_id})">Authorize</button>
                  ${p ? `<button class="btn-icon" style="color:var(--danger)" onclick="revokePerm(${fileId},${u.user_id},'${filename}')" title="Revoke All"><span class="material-symbols-outlined">block</span></button>` : ''}
                </div>
              </td>
            </tr>`;
        }).join('')}
      </tbody>
    </table>`;
}

async function savePerm(fid, uid) {
  const cv = document.getElementById('v-' + uid).checked, cd = document.getElementById('d-' + uid).checked;
  const data = await api('/files/permissions', { method: 'POST', headers: headers(true), body: JSON.stringify({ file_id: fid, user_id: uid, can_view: cv, can_download: cd }) });
  if (data) toast('Permission saved', 'success');
}

async function revokePerm(fid, uid, fname) {
  if (!confirm('Revoke all permissions for this user?')) return;
  const data = await api(`/files/permissions/${fid}/${uid}`, { method: 'DELETE', headers: headers() });
  if (data) { toast('Permission revoked', 'success'); managePerms(fid, fname); }
}

window.onload = init;
