import { useCallback, useEffect, useMemo, useState } from 'react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import api, { errMsg, GRADES, rows } from '../api';
import { useAuth } from '../auth';
import { Empty, Field, num, pctText, Spinner, Stat, Tabs, useToast } from '../ui';

function Analytics() {
  const [d, setD] = useState(null);
  useEffect(() => { api.get('/teacher/analytics/').then((r) => setD(r.data)).catch(() => setD({})); }, []);
  if (!d) return <Spinner />;
  if (!d.count) return <div className="panel"><Empty>No results yet. Upload results in the Results tab to see your analytics.</Empty></div>;
  const grades = GRADES.map((g) => ({ grade: g, students: d.grade_distribution?.[g] ?? 0 }));
  const secs = (d.section_averages || []).map((s) => ({ section: s.section, average: Number(s.average) }));
  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Stat value={pctText(d.average)} label="Average result of my subject" />
        <Stat value={d.count} label="Results entered" />
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="panel">
          <h2 className="mb-3">Grade distribution</h2>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={grades}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="grade" /><YAxis allowDecimals={false} /><Tooltip />
              <Bar dataKey="students" fill="#1e3a8a" radius={[3, 3, 0, 0]} /></BarChart>
          </ResponsiveContainer>
        </div>
        <div className="panel">
          <h2 className="mb-3">Section-wise average</h2>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={secs}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="section" /><YAxis domain={[0, 100]} unit="%" /><Tooltip formatter={(v) => `${v}%`} />
              <Bar dataKey="average" fill="#fbbf24" radius={[3, 3, 0, 0]} /></BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

function Students({ students }) {
  const [q, setQ] = useState('');
  const [sec, setSec] = useState('');
  const secs = useMemo(() => [...new Set(students.map((s) => s.section))].sort(), [students]);
  const shown = students.filter((s) => (!sec || s.section === sec) && (!q || `${s.uid} ${s.full_name}`.toLowerCase().includes(q.toLowerCase())));
  return (
    <div>
      <div className="mb-3 grid gap-2 sm:grid-cols-2">
        <input className="input" placeholder="Search name or roll no" value={q} onChange={(e) => setQ(e.target.value)} />
        <select className="input" value={sec} onChange={(e) => setSec(e.target.value)}>
          <option value="">All my sections</option>{secs.map((s) => <option key={s}>{s}</option>)}
        </select>
      </div>
      <div className="overflow-x-auto rounded-md border border-line bg-white">
        <table className="tbl">
          <thead><tr><th>Roll No</th><th>Name</th><th>Section</th><th>Father name</th></tr></thead>
          <tbody>{shown.map((s) => <tr key={s.uid}><td>{s.uid}</td><td>{s.full_name}</td><td>{s.section}</td><td>{s.father_name}</td></tr>)}</tbody>
        </table>
        {!shown.length && <Empty>{students.length ? 'No students match.' : 'No approved students in your sections yet.'}</Empty>}
      </div>
    </div>
  );
}

function Results({ students, onChanged }) {
  const toast = useToast();
  const [list, setList] = useState(null);
  const [editing, setEditing] = useState(null);
  const [roll, setRoll] = useState('');
  const [total, setTotal] = useState('');
  const [obtained, setObtained] = useState('');
  const [report, setReport] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => api.get('/teacher/results/', { params: { page_size: 500 } }).then((r) => setList(rows(r.data))).catch(() => setList([])), []);
  useEffect(() => { load(); }, [load]);

  const reset = () => { setEditing(null); setRoll(''); setTotal(''); setObtained(''); };
  const edit = (r) => { setEditing(r); setRoll(r.student_uid); setTotal(num(r.total_marks)); setObtained(num(r.obtained_marks)); window.scrollTo({ top: 0, behavior: 'smooth' }); };

  const save = async (e) => {
    e.preventDefault();
    if (Number(obtained) > Number(total)) return toast.err('Obtained marks cannot be more than total marks.');
    setBusy(true);
    try {
      const body = { student_uid: roll, total_marks: total, obtained_marks: obtained };
      if (editing) await api.put(`/teacher/results/${editing.id}/`, body); else await api.post('/teacher/results/', body);
      toast.ok('Result saved.'); reset(); await load(); onChanged();
    } catch (err) { toast.err(errMsg(err)); } finally { setBusy(false); }
  };

  const remove = async (r) => {
    if (!window.confirm(`Delete the result of ${r.student_name}?`)) return;
    try { await api.delete(`/teacher/results/${r.id}/`); toast.ok('Result deleted.'); await load(); onChanged(); } catch (err) { toast.err(errMsg(err)); }
  };

  const upload = async (e) => {
    e.preventDefault();
    const file = e.target.elements.file.files[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.xlsx')) return toast.err('Choose an .xlsx Excel file.');
    if (file.size > 5 * 1024 * 1024) return toast.err('The file is larger than 5 MB.');
    const fd = new FormData(); fd.append('file', file);
    setBusy(true); setReport(null);
    try {
      const { data } = await api.post('/teacher/results/import/', fd);
      setReport(data); toast.ok(`${data.imported ?? 0} result(s) imported.`);
      e.target.reset(); await load(); onChanged();
    } catch (err) { toast.err(errMsg(err)); } finally { setBusy(false); }
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-4 lg:grid-cols-2">
        <form onSubmit={save} className="panel space-y-3">
          <h2>{editing ? `Edit result: ${editing.student_name}` : 'Manual entry'}</h2>
          <Field label="Student">
            <select className="input" value={roll} onChange={(e) => setRoll(e.target.value)} required disabled={!!editing}>
              <option value="">Select a student…</option>
              {students.map((s) => <option key={s.uid} value={s.uid}>{s.uid} – {s.full_name} ({s.section})</option>)}
            </select>
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Total marks"><input className="input" type="number" min="1" step="1" value={total} onChange={(e) => setTotal(e.target.value)} required /></Field>
            <Field label="Obtained marks"><input className="input" type="number" min="0" step="1" value={obtained} onChange={(e) => setObtained(e.target.value)} required /></Field>
          </div>
          <div className="flex gap-2">
            <button className="btn" disabled={busy}>{editing ? 'Update result' : 'Save result'}</button>
            {editing && <button type="button" className="btn-ghost" onClick={reset}>Cancel</button>}
          </div>
        </form>

        <form onSubmit={upload} className="panel space-y-3">
          <h2>Excel upload</h2>
          <p className="text-sm text-slate-600">The template already lists your students (Student Name, Roll No, Class): just fill Total Marks and Obtained Marks. Students are matched by Roll No.</p>
          <a className="text-sm font-semibold text-navy underline" href="/api/teacher/results/template/">Download the Excel template</a>
          <input className="input" type="file" name="file" accept=".xlsx" required />
          <button className="btn" disabled={busy}>{busy ? 'Uploading…' : 'Upload results'}</button>
          {report && (
            <div className="rounded bg-navy-soft p-3 text-sm">
              <p className="font-semibold">{report.imported} imported, {report.errors?.length || 0} skipped.</p>
              {!!report.errors?.length && <ul className="mt-2 max-h-40 list-disc overflow-auto pl-5 text-red-800">{report.errors.map((x, i) => <li key={i}>{x.row ? `Row ${x.row}: ` : ''}{x.message || String(x)}</li>)}</ul>}
            </div>
          )}
        </form>
      </div>

      <div>
        <h2 className="mb-3">My uploaded results</h2>
        {!list ? <Spinner /> : (
          <div className="overflow-x-auto rounded-md border border-line bg-white">
            <table className="tbl">
              <thead><tr><th>Roll No</th><th>Name</th><th>Section</th><th>Total</th><th>Obtained</th><th>%</th><th>Grade</th><th>Actions</th></tr></thead>
              <tbody>{list.map((r) => (
                <tr key={r.id}><td>{r.student_uid}</td><td>{r.student_name}</td><td>{r.section}</td><td>{num(r.total_marks)}</td><td>{num(r.obtained_marks)}</td><td>{pctText(r.percentage)}</td><td>{r.grade}</td>
                  <td className="space-x-3 whitespace-nowrap"><button className="linkbtn text-navy" onClick={() => edit(r)}>Edit</button><button className="linkbtn text-red-700" onClick={() => remove(r)}>Delete</button></td></tr>
              ))}</tbody>
            </table>
            {!list.length && <Empty>No results uploaded yet.</Empty>}
          </div>
        )}
      </div>
    </div>
  );
}

export default function Teacher() {
  const { user } = useAuth();
  const [tab, setTab] = useState('analytics');
  const [students, setStudents] = useState([]);
  const [rev, setRev] = useState(0); // bumps to reload analytics after result changes
  useEffect(() => { api.get('/teacher/students/', { params: { page_size: 500 } }).then((r) => setStudents(rows(r.data))).catch(() => {}); }, []);
  return (
    <div className="space-y-5">
      <div>
        <h1>Teacher dashboard</h1>
        <p className="mt-1 text-slate-600">{user.full_name} ({user.uid}). Subject: <b>{user.subject}</b>. Sections: {(user.sections || []).join(', ') || 'none allotted'}</p>
      </div>
      <Tabs value={tab} onChange={setTab} tabs={[['analytics', 'Analytics'], ['students', 'Student list'], ['results', 'Results']]} />
      {tab === 'analytics' && <Analytics key={rev} />}
      {tab === 'students' && <Students students={students} />}
      {tab === 'results' && <Results students={students} onChanged={() => setRev((x) => x + 1)} />}
    </div>
  );
}
