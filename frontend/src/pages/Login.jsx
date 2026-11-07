import { useState } from 'react';
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom';
import { errMsg } from '../api';
import { homeFor, useAuth } from '../auth';
import LogoBackdrop from '../components/LogoBackdrop';
import { Field, Tabs } from '../ui';

export default function Login({ admin = false }) {
  const { user, login } = useAuth();
  const nav = useNavigate();
  const [params, setParams] = useSearchParams();
  const role = admin ? 'admin' : params.get('role') === 'student' ? 'student' : 'teacher';
  const [uid, setUid] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to={homeFor(user)} replace />;

  const label = { teacher: 'Teacher ID', student: 'Student ID / Roll No', admin: 'Admin ID' }[role];

  const submit = async (e) => {
    e.preventDefault();
    setError(''); setBusy(true);
    try {
      nav(homeFor(await login(uid.trim(), password, role)), { replace: true });
    } catch (err) {
      setError(errMsg(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-md">
      <LogoBackdrop />
      <h1 className="mb-4">{admin ? 'Admin log in' : 'Log in'}</h1>
      <div className="overflow-hidden rounded-md border border-line">
        {!admin && <Tabs value={role} onChange={(r) => { setParams({ role: r }); setError(''); }} tabs={[['teacher', 'Teacher Login'], ['student', 'Student Login']]} />}
        <form onSubmit={submit} className="space-y-4 bg-white/95 p-5">
          <Field label={label}><input className="input" value={uid} onChange={(e) => setUid(e.target.value)} required autoFocus autoComplete="username" /></Field>
          <Field label="Password"><input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password" /></Field>
          {error && <p className="rounded bg-red-50 p-3 text-sm text-red-800" role="alert">{error}</p>}
          <button className="btn w-full" disabled={busy}>{busy ? 'Logging in…' : 'Log in'}</button>
          {!admin && <p className="text-sm text-slate-600">No account yet? <Link className="font-semibold text-navy underline" to={`/register?tab=${role}`}>Register</Link></p>}
        </form>
      </div>
    </div>
  );
}
