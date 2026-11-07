// Live registered-users table. Polls the server; admins also get Approve/Block/Delete buttons.
(function () {
  const tbody = document.querySelector('#users tbody');
  const admHead = document.querySelector('#users th.adm');
  const stamp = document.getElementById('stamp');

  function cell(tr, text) {
    const td = document.createElement('td');
    td.textContent = text;
    tr.appendChild(td);
    return td;
  }

  function btn(label, cls, onClick) {
    const b = document.createElement('button');
    b.className = 'link ' + cls;
    b.textContent = label;
    b.addEventListener('click', onClick);
    return b;
  }

  async function act(id, action) {
    if (action === 'delete' && !confirm('Delete this user permanently?')) return;
    await fetch('/admin/user/' + id + '/' + action, { method: 'POST' });
    load();
  }

  async function load() {
    let data;
    try {
      data = await (await fetch('/api/users', { cache: 'no-store' })).json();
    } catch (e) { return; }
    admHead.hidden = !data.admin;
    tbody.replaceChildren();
    if (!data.users.length) {
      const tr = document.createElement('tr');
      const td = cell(tr, 'No registrations yet.');
      td.colSpan = 6;
      td.className = 'muted';
      tbody.appendChild(tr);
    }
    for (const u of data.users) {
      const tr = document.createElement('tr');
      cell(tr, u.role); cell(tr, u.uid); cell(tr, u.name); cell(tr, u.info);
      const st = cell(tr, u.status);
      st.className = 'pill ' + u.status.toLowerCase();
      st.textContent = u.status;
      if (data.admin) {
        const td = document.createElement('td');
        td.className = 'nowrap';
        if (u.status !== 'Approved') td.appendChild(btn('Approve', 'ok', () => act(u.id, 'approve')));
        if (u.status !== 'Blocked') td.appendChild(btn('Block', 'warn', () => act(u.id, 'block')));
        td.appendChild(btn('Delete', 'danger', () => act(u.id, 'delete')));
        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    }
    if (stamp) stamp.textContent = '(live, updated ' + new Date().toLocaleTimeString() + ')';
  }

  load();
  setInterval(() => { if (!document.hidden) load(); }, 5000);
})();
