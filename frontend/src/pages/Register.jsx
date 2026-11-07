import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import api, { errMsg, fieldErrors, rows } from '../api';
import LiveUsersTable from '../components/LiveUsersTable';
import LogoBackdrop from '../components/LogoBackdrop';
import { Field, Tabs, useToast } from '../ui';

const EMPTY = { uid: '', full_name: '', subject: '', father_name: '', mobile: '', email: '', password: '', confirm_password: '', section: '', sections: [] };
const MOBILE = /^[0-9+\-\s]{7,15}$/;
const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export default function Register() {
  const [params, setParams] = useSearchParams();
  const tab = params.get('tab') === 'student' ? 'student' : 'teacher';
  const toast = useToast();
  const [sections, setSections] = useState([]);
  const [f, setF] = useState(EMPTY);
  const [errs, setErrs] = useState({});
  const [saving, setSaving] = useState(false);
  const [done, setDone] = useState(false);
  const [tick, setTick] = useState(0);
  const [subjects, setSubjects] = useState([]);

  useEffect(() => { api.get('/subjects/').then((r) => setSubjects([...new Set(Object.values(r.data).flatMap((g) => g.subjects))])).catch(() => {}); }, []);
  useEffect(() => { api.get('/sections/', { params: { page_size: 200 } }).then((r) => setSections(rows(r.data))).catch(() => {}); }, []);
  useEffect(() => { setErrs({}); setDone(false); }, [tab]);

  const set = (k) => (e) => setF((s) => ({ ...s, [k]: e.target.value }));
  const toggleSection = (id) => setF((s) => ({ ...s, sections: s.sections.includes(id) ? s.sections.filter((x) => x !== id) : [...s.sections, id] }));
  const isTeacher = tab === 'teacher';

  const validate = () => {
    const e = {};
    if (!f.uid.trim()) e.uid = 'Enter the ID given by the school.';
    if (!f.full_name.trim()) e.full_name = 'Enter your full name.';
    if (isTeacher && !f.subject.trim()) e.subject = 'Enter the subject you teach.';
    if (isTeacher && !f.sections.length) e.sections = 'Select at least one class / section.';
    if (!isTeacher && !f.father_name.trim()) e.father_name = 'Enter your father’s name.';
    if (!isTeacher && !f.section) e.section = 'Select your class / section.';
    if (!MOBILE.test(f.mobile.trim())) e.mobile = 'Enter a valid mobile number.';
    if (!EMAIL.test(f.email.trim())) e.email = 'Enter a valid email address.';
    if (f.password.length < 8) e.password = 'Use at least 8 characters.';
    if (f.password !== f.confirm_password) e.confirm_password = 'Passwords do not match.';
    return e;
  };

  const submit = async (ev) => {
    ev.preventDefault();
    const e = validate();
    setErrs(e);
    if (Object.keys(e).length) return;
    setSaving(true);
    try {
      const body = { role: tab, uid: f.uid.trim(), full_name: f.full_name.trim(), mobile: f.mobile.trim(), email: f.email.trim(), password: f.password, confirm_password: f.confirm_password };
      if (isTeacher) Object.assign(body, { subject: f.subject.trim(), sections: f.sections });
      else Object.assign(body, { father_name: f.father_name.trim(), section: Number(f.section) });
      await api.post('/auth/register/', body);
      setF(EMPTY); setDone(true); setTick((t) => t + 1);
      toast.ok('Registration submitted.');
    } catch (err) {
      const fe = fieldErrors(err);
      setErrs(fe);
      if (!Object.keys(fe).length) toast.err(errMsg(err));
    } finally {
      setSaving(false);
    }
  };

  const text = (k, label, props = {}) => (
    <Field label={label} error={errs[k]}><input className="input" value={f[k]} onChange={set(k)} {...props} /></Field>
  );

  return (
    <div className="space-y-8">
      <LogoBackdrop />
      <div>
        <h1>Register</h1>
        <p className="mt-1 text-slate-600">Create your account. The Admin must approve it before you can log in.</p>
      </div>

      <section className="overflow-hidden rounded-md border border-line bg-white/60">
        <Tabs value={tab} onChange={(t) => setParams({ tab: t })} tabs={[['teacher', 'Teacher Registration'], ['student', 'Student Registration']]} />
        {done ? (
          <div className="bg-white/75 p-6">
            <h2>Waiting for Admin approval</h2>
            <p className="mt-2 text-slate-600">Your registration was received. You can log in once the Admin approves your account. You can see its status in the table below.</p>
            <button className="btn mt-4" onClick={() => setDone(false)}>Register another account</button>
          </div>
        ) : (
          <form onSubmit={submit} noValidate className="grid gap-4 bg-white/75 p-4 sm:grid-cols-2 sm:p-6">
            {text('uid', isTeacher ? 'Teacher ID (given by school)' : 'Student ID / Roll No (given by school)', { placeholder: isTeacher ? 'T-101' : 'S-201', autoComplete: 'off' })}
            {text('full_name', 'Full name')}
            {isTeacher ? (
              <>
                {text('subject', 'Subject', { placeholder: 'English, Math…', list: 'subject-list' })}
                <datalist id="subject-list">{subjects.map((x) => <option key={x} value={x} />)}</datalist>
              </>
            ) : (
              <>
                <Field label="Class / Section" error={errs.section}>
                  <select className="input" value={f.section} onChange={set('section')}>
                    <option value="">Select…</option>
                    {sections.map((s) => <option key={s.id} value={s.id}>{s.label}</option>)}
                  </select>
                </Field>
                {text('father_name', 'Father name')}
              </>
            )}
            {text('mobile', 'Mobile number', { inputMode: 'tel', placeholder: '03001234567' })}
            {text('email', 'Email', { type: 'email' })}
            {text('password', 'Password', { type: 'password', autoComplete: 'new-password' })}
            {text('confirm_password', 'Confirm password', { type: 'password', autoComplete: 'new-password' })}
            {isTeacher && (
              <fieldset className="sm:col-span-2">
                <legend className="text-sm font-semibold">Class / Section allotted</legend>
                <div className="mt-2 flex flex-wrap gap-x-5 gap-y-2">
                  {sections.map((s) => (
                    <label key={s.id} className="flex items-center gap-2 text-sm">
                      <input type="checkbox" checked={f.sections.includes(s.id)} onChange={() => toggleSection(s.id)} /> {s.label}
                    </label>
                  ))}
                  {!sections.length && <span className="text-sm text-slate-500">No classes exist yet. Ask the Admin to create them.</span>}
                </div>
                {errs.sections && <span className="mt-1 block text-sm text-red-700">{errs.sections}</span>}
              </fieldset>
            )}
            <div className="sm:col-span-2">
              <button className="btn" disabled={saving}>{saving ? 'Submitting…' : 'Submit for approval'}</button>
            </div>
          </form>
        )}
      </section>

      <section>
        <h2 className="mb-3">Registered users</h2>
        <LiveUsersTable refreshKey={tick} />
      </section>
    </div>
  );
}
