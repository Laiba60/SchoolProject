import { useCallback, useEffect, useState } from 'react';
import api, { errMsg, rows } from '../api';
import { useAuth } from '../auth';
import { Empty, Spinner, StatusPill, useToast } from '../ui';

const cap = (s) => (s ? s[0].toUpperCase() + s.slice(1) : '');

// Public table of registered users, refreshed every 5 seconds (paused while the tab is hidden).
// Admins also get Approve / Block / Unblock / Delete buttons on every row.
export default function LiveUsersTable({ refreshKey = 0, filters = false }) {
  const { user } = useAuth();
  const toast = useToast();
  const isAdmin = user?.role === 'admin';
  const [list, setList] = useState(null);
  const [updated, setUpdated] = useState(null);
  const [busy, setBusy] = useState(null);
  const [q, setQ] = useState('');
  const [role, setRole] = useState('');
  const [status, setStatus] = useState('');

  const load = useCallback(async () => {
    try {
      const { data } = await api.get('/users/public/', { params: { page_size: 100 } });
      setList(rows(data));
      setUpdated(new Date());
    } catch (e) {
      setList((old) => old ?? []);
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(() => { if (!document.hidden) load(); }, 5000);
    return () => clearInterval(t);
  }, [load, refreshKey]);

  const act = async (u, action) => {
    if (action === 'delete' && !window.confirm(`Delete ${u.name} (${u.uid}) permanently? Their results are removed too.`)) return;
    setBusy(u.id);
    try {
      if (action === 'delete') await api.delete(`/admin/users/${u.id}/`);
      else await api.post(`/admin/users/${u.id}/${action}/`);
      toast.ok(action === 'delete' ? 'User deleted.' : `User ${action}d.`);
      await load();
    } catch (e) {
      toast.err(errMsg(e));
    } finally {
      setBusy(null);
    }
  };

  if (!list) return <Spinner />;
  const shown = list.filter((u) =>
    (!role || u.role === role) && (!status || u.status === status) &&
    (!q || `${u.uid} ${u.name}`.toLowerCase().includes(q.toLowerCase())));

  return (
    <div>
      {filters && (
        <div className="mb-3 grid gap-2 sm:grid-cols-3">
          <input className="input" placeholder="Search name or ID" value={q} onChange={(e) => setQ(e.target.value)} />
          <select className="input" value={role} onChange={(e) => setRole(e.target.value)}>
            <option value="">All roles</option><option value="teacher">Teachers</option><option value="student">Students</option>
          </select>
          <select className="input" value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">All statuses</option><option>Pending</option><option>Approved</option><option>Blocked</option>
          </select>
        </div>
      )}
      <div className="overflow-x-auto rounded-md border border-line bg-white/80">
        <table className="tbl">
          <thead>
            <tr><th>Role</th><th>ID</th><th>Name</th><th>Class / Subject</th><th>Status</th>{isAdmin && <th>Actions</th>}</tr>
          </thead>
          <tbody>
            {shown.map((u) => (
              <tr key={u.id ?? u.uid}>
                <td>{cap(u.role)}</td><td>{u.uid}</td><td>{u.name}</td><td>{u.info}</td>
                <td><StatusPill status={u.status} /></td>
                {isAdmin && (
                  <td className="space-x-3 whitespace-nowrap">
                    {u.status !== 'Approved' && <button disabled={busy === u.id} className="linkbtn text-emerald-700" onClick={() => act(u, u.status === 'Blocked' ? 'unblock' : 'approve')}>{u.status === 'Blocked' ? 'Unblock' : 'Approve'}</button>}
                    {u.status !== 'Blocked' && <button disabled={busy === u.id} className="linkbtn text-amber-700" onClick={() => act(u, 'block')}>Block</button>}
                    <button disabled={busy === u.id} className="linkbtn text-red-700" onClick={() => act(u, 'delete')}>Delete</button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
        {!shown.length && <Empty>{list.length ? 'No users match these filters.' : 'No one has registered yet.'}</Empty>}
      </div>
      {updated && <p className="mt-2 text-xs text-slate-500">Live. Last updated {updated.toLocaleTimeString()}</p>}
    </div>
  );
}
