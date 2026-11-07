import { useCallback, useEffect, useState } from 'react';
import { NavLink, useParams } from 'react-router-dom';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import api, { errMsg, GRADES, rows } from '../api';
import LiveUsersTable from '../components/LiveUsersTable';
import { Empty, Field, num, pctText, Spinner, useToast } from '../ui';
import NotFound from './NotFound';

// ---- Classes & sections -----------------------------------------------------
function Sections() {
  const toast = useToast();
  const [list, setList] = useState(null);
  const [cls, setCls] = useState('');
  const [secs, setSecs] = useState('');
  const load = useCallback(() => api.get('/sections/', { params: { page_size: 200 } }).then((r) => setList(rows(r.data))).catch(() => setList([])), []);
  useEffect(() => { load(); }, [load]);

  const create = async (e) => {
    e.preventDefault();
    const sections = secs.split(',').map((s) => s.trim().toUpperCase()).filter(Boolean);
    try {
      await api.post('/admin/sections/', { class_name: cls.trim(), sections: sections.length ? sections : [''] });
      toast.ok('Class / section saved.'); setCls(''); setSecs(''); load();
    } catch (err) { toast.err(errMsg(err)); }
  };
  const remove = async (s) => {
    if (!window.confirm(`Delete ${s.label}?`)) return;
    try { await api.delete(`/admin/sections/${s.id}/`); toast.ok('Deleted.'); load(); } catch (err) { toast.err(errMsg(err)); }
  };

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <form onSubmit={create} className="panel space-y-3">
        <h2>Create class and sections</h2>
        <Field label="Class"><input className="input" value={cls} onChange={(e) => setCls(e.target.value)} placeholder="9th" required /></Field>
        <Field label="Sections, separated by commas"><input className="input" value={secs} onChange={(e) => setSecs(e.target.value)} placeholder="A, B, C" /></Field>
        <button className="btn">Create</button>
      </form>
      <div className="panel">
        <h2 className="mb-3">Existing classes and sections</h2>
        {!list ? <Spinner /> : !list.length ? <Empty>No classes yet. Create the first one.</Empty> : (
          <div className="flex flex-wrap gap-2">
            {list.map((s) => (
              <span key={s.id} className="inline-flex items-center gap-2 rounded-full bg-navy-soft py-1 pl-3 pr-2 text-sm font-semibold">
                {s.label}
                <button className="text-red-700" aria-label={`Delete ${s.label}`} onClick={() => remove(s)}>×</button>
              </span>
            ))}
          </div>
        )}
        <p className="mt-3 text-xs text-slate-500">A section cannot be deleted while teachers or students are assigned to it.</p>
      </div>
    </div>
  );
}

// ---- Overall results by teacher ----------------------------------------------
function Overview() {
  const [list, setList] = useState(null);
  const [teacher, setTeacher] = useState('');
  useEffect(() => { api.get('/admin/results/overview/', { params: { page_size: 200 } }).then((r) => setList(rows(r.data))).catch(() => setList([])); }, []);
  if (!list) return <Spinner />;
  if (!list.length) return <div className="panel"><Empty>No teachers or results yet.</Empty></div>;
  const shown = list.filter((t) => !teacher || t.teacher_uid === teacher);
  const chart = list.filter((t) => t.average !== null && t.average !== undefined).map((t) => ({ name: `${t.teacher_name} (${t.subject})`, average: Number(t.average) }));
  return (
    <div className="space-y-4">
      {!!chart.length && (
        <div className="panel">
          <h2 className="mb-3">Average result by teacher</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={chart}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="name" tick={{ fontSize: 12 }} /><YAxis domain={[0, 100]} unit="%" /><Tooltip formatter={(v) => `${v}%`} />
              <Bar dataKey="average" fill="#1e3a8a" radius={[3, 3, 0, 0]} /></BarChart>
          </ResponsiveContainer>
        </div>
      )}
      <select className="input max-w-xs" value={teacher} onChange={(e) => setTeacher(e.target.value)}>
        <option value="">All teachers</option>
        {list.map((t) => <option key={t.teacher_uid} value={t.teacher_uid}>{t.teacher_name} ({t.teacher_uid})</option>)}
      </select>
      <div className="grid gap-4 md:grid-cols-2">
        {shown.map((t) => (
          <div key={t.teacher_uid} className="panel">
            <h3 className="text-lg font-semibold">{t.teacher_name} <span className="text-sm font-normal text-slate-500">{t.teacher_uid} · {t.subject}</span></h3>
            <p className="mt-2 text-sm">Results entered: <b>{t.count}</b>. Average: <b>{pctText(t.average)}</b></p>
            <p className="mt-2 text-sm">Grades: {GRADES.map((g) => `${g} ${t.grade_distribution?.[g] ?? 0}`).join(', ')}</p>
            <p className="mt-1 text-sm">Sections: {(t.section_averages || []).map((s) => `${s.section} ${pctText(s.average)}`).join(', ') || 'no results yet'}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

// ---- Manage results ------------------------------------------------------------
const BLANK = { student_uid: '', subject: '', total_marks: '', obtained_marks: '' };

function Results() {
  const toast = useToast();
  const [list, setList] = useState(null);
  const [sections, setSections] = useState([]);
  const [fl, setFl] = useState({ search: '', section: '', subject: '', teacher: '' });
  const [form, setForm] = useState(BLANK);
  const [editId, setEditId] = useState(null);
  const [subjects, setSubjects] = useState([]);

  useEffect(() => { api.get('/subjects/').then((r) => setSubjects([...new Set(Object.values(r.data).flatMap((g) => g.subjects))])).catch(() => {}); }, []);
  useEffect(() => { api.get('/sections/', { params: { page_size: 200 } }).then((r) => setSections(rows(r.data))).catch(() => {}); }, []);
  const load = useCallback(() => {
    const params = Object.fromEntries(Object.entries(fl).filter(([, v]) => v));
    return api.get('/admin/results/', { params: { ...params, page_size: 200 } }).then((r) => setList(rows(r.data))).catch(() => setList([]));
  }, [fl]);
  useEffect(() => { const t = setTimeout(load, 250); return () => clearTimeout(t); }, [load]);

  const f = (k) => (e) => setFl((s) => ({ ...s, [k]: e.target.value }));
  const g = (k) => (e) => setForm((s) => ({ ...s, [k]: e.target.value }));
  const edit = (r) => { setEditId(r.id); setForm({ student_uid: r.student_uid, subject: r.subject, total_marks: num(r.total_marks), obtained_marks: num(r.obtained_marks) }); window.scrollTo({ top: 0, behavior: 'smooth' }); };
  const reset = () => { setEditId(null); setForm(BLANK); };

  const save = async (e) => {
    e.preventDefault();
    if (Number(form.obtained_marks) > Number(form.total_marks)) return toast.err('Obtained marks cannot be more than total marks.');
    try {
      if (editId) await api.put(`/admin/results/${editId}/`, form); else await api.post('/admin/results/', form);
      toast.ok('Result saved.'); reset(); load();
    } catch (err) { toast.err(errMsg(err)); }
  };
  const remove = async (r) => {
    if (!window.confirm(`Delete ${r.subject} result of ${r.student_name}?`)) return;
    try { await api.delete(`/admin/results/${r.id}/`); toast.ok('Result deleted.'); load(); } catch (err) { toast.err(errMsg(err)); }
  };

  return (
    <div className="space-y-5">
      <form onSubmit={save} className="panel space-y-3">
        <h2>{editId ? 'Edit result' : 'Add a result'}</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="Student roll no"><input className="input" value={form.student_uid} onChange={g('student_uid')} required disabled={!!editId} /></Field>
          <Field label="Subject">
            <input className="input" list="card-subjects" value={form.subject} onChange={g('subject')} required disabled={!!editId} />
            <datalist id="card-subjects">{subjects.map((x) => <option key={x} value={x} />)}</datalist>
          </Field>
          <Field label="Total marks"><input className="input" type="number" min="1" step="1" value={form.total_marks} onChange={g('total_marks')} required /></Field>
          <Field label="Obtained marks"><input className="input" type="number" min="0" step="1" value={form.obtained_marks} onChange={g('obtained_marks')} required /></Field>
        </div>
        <div className="flex gap-2"><button className="btn">{editId ? 'Update result' : 'Add result'}</button>{editId && <button type="button" className="btn-ghost" onClick={reset}>Cancel</button>}</div>
      </form>

      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        <input className="input" placeholder="Search student name or roll no" value={fl.search} onChange={f('search')} />
        <select className="input" value={fl.section} onChange={f('section')}><option value="">All sections</option>{sections.map((s) => <option key={s.id} value={s.label}>{s.label}</option>)}</select>
        <input className="input" placeholder="Subject" value={fl.subject} onChange={f('subject')} />
        <input className="input" placeholder="Teacher name or ID" value={fl.teacher} onChange={f('teacher')} />
      </div>

      {!list ? <Spinner /> : (
        <div className="overflow-x-auto rounded-md border border-line bg-white">
          <table className="tbl">
            <thead><tr><th>Roll No</th><th>Student</th><th>Section</th><th>Subject</th><th>Teacher</th><th>Marks</th><th>%</th><th>Grade</th><th>Actions</th></tr></thead>
            <tbody>{list.map((r) => (
              <tr key={r.id}><td>{r.student_uid}</td><td>{r.student_name}</td><td>{r.section}</td><td>{r.subject}</td><td>{r.teacher_name || '–'}</td>
                <td>{num(r.obtained_marks)}/{num(r.total_marks)}</td><td>{pctText(r.percentage)}</td><td>{r.grade}</td>
                <td className="space-x-3 whitespace-nowrap">
                  <button className="linkbtn text-navy" onClick={() => edit(r)}>Edit</button>
                  <a className="linkbtn text-navy" href={`/api/reports/student/${encodeURIComponent(r.student_uid)}/pdf/?dl=1`}>PDF</a>
                  <button className="linkbtn text-red-700" onClick={() => remove(r)}>Delete</button>
                </td></tr>
            ))}</tbody>
          </table>
          {!list.length && <Empty>No results match these filters.</Empty>}
        </div>
      )}
    </div>
  );
}

// ---- Branding ---------------------------------------------------------------------
function Branding() {
  const toast = useToast();
  const [b, setB] = useState(null);
  const [name, setName] = useState('');
  const load = useCallback(() => api.get('/admin/branding/').then((r) => { setB(r.data); setName(r.data.school_name || ''); }).catch(() => setB({})), []);
  useEffect(() => { load(); }, [load]);

  const save = async (e) => {
    e.preventDefault();
    const file = e.target.elements.logo.files[0];
    if (file && file.size > 2 * 1024 * 1024) return toast.err('The logo must be smaller than 2 MB.');
    const fd = new FormData();
    fd.append('school_name', name);
    if (file) fd.append('logo', file);
    try { await api.post('/admin/branding/', fd); toast.ok('Branding saved.'); e.target.reset(); load(); } catch (err) { toast.err(errMsg(err)); }
  };
  if (!b) return <Spinner />;
  return (
    <form onSubmit={save} className="panel max-w-xl space-y-4">
      <h2>School logo and name</h2>
      <p className="text-sm text-slate-600">The logo appears in the header and as the watermark on every PDF report card.</p>
      {b.logo_url && <img src={b.logo_url} alt="Current school logo" className="h-24 w-24 object-contain" />}
      <Field label="School name"><input className="input" value={name} onChange={(e) => setName(e.target.value)} required /></Field>
      <Field label="New logo (PNG with transparent background works best)"><input className="input" type="file" name="logo" accept="image/png,image/jpeg" /></Field>
      <button className="btn">Save branding</button>
    </form>
  );
}

const PAGES = {
  users: ['Users', () => <LiveUsersTable filters />],
  sections: ['Classes & sections', Sections],
  overview: ['Overall results', Overview],
  results: ['Manage results', Results],
  branding: ['Logo & branding', Branding],
};

export default function Admin() {
  const { page } = useParams();
  const entry = PAGES[page];
  if (!entry) return <NotFound />;
  const [title, View] = entry;
  return (
    <div className="space-y-5">
      <h1>Admin panel</h1>
      <nav className="flex flex-wrap gap-1 border-b border-line">
        {Object.entries(PAGES).map(([key, [label]]) => (
          <NavLink key={key} to={`/admin/${key}`} className={({ isActive }) => `tab flex-none ${isActive ? 'tab-on' : ''}`}>{label}</NavLink>
        ))}
      </nav>
      <h2>{title}</h2>
      <View />
    </div>
  );
}
