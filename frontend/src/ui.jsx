import { createContext, useCallback, useContext, useState } from 'react';

export function Spinner({ label = 'Loading…' }) {
  return (
    <div className="flex items-center gap-3 p-6 text-slate-500" role="status">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-navy border-t-transparent" />
      {label}
    </div>
  );
}

export const Empty = ({ children }) => <p className="p-6 text-center text-slate-500">{children}</p>;

export function Field({ label, error, children }) {
  return (
    <label className="block text-sm font-semibold">
      {label}
      <div className="mt-1 font-normal">{children}</div>
      {error && <span className="mt-1 block text-sm font-normal text-red-700">{error}</span>}
    </label>
  );
}

const pillStyle = { Approved: 'text-emerald-700', Pending: 'text-amber-700', Blocked: 'text-red-700' };
export const StatusPill = ({ status }) => <span className={`font-semibold ${pillStyle[status] || ''}`}>{status}</span>;

export const Stat = ({ value, label }) => (
  <div className="panel text-center">
    <div className="font-serif text-4xl font-bold text-navy">{value}</div>
    <div className="mt-1 text-sm text-slate-600">{label}</div>
  </div>
);

export const pctText = (v) => (v === null || v === undefined ? '–' : `${Number(v).toFixed(1)}%`);
export const num = (v) => Number(v).toString();

// ---- toasts ---------------------------------------------------------------
const ToastCtx = createContext(null);
export const useToast = () => useContext(ToastCtx);

export function ToastProvider({ children }) {
  const [items, setItems] = useState([]);
  const push = useCallback((kind, text) => {
    const id = Math.random();
    setItems((l) => [...l, { id, kind, text }]);
    setTimeout(() => setItems((l) => l.filter((t) => t.id !== id)), 5000);
  }, []);
  const api = { ok: (t) => push('ok', t), err: (t) => push('err', t) };
  return (
    <ToastCtx.Provider value={api}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex w-[min(92vw,22rem)] flex-col gap-2" aria-live="polite">
        {items.map((t) => (
          <div key={t.id} className={`rounded border-l-4 bg-white px-4 py-3 text-sm shadow-lg ${t.kind === 'ok' ? 'border-emerald-600' : 'border-red-600'}`}>
            {t.text}
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}

export function Tabs({ tabs, value, onChange }) {
  return (
    <div className="flex border-b border-line bg-white" role="tablist">
      {tabs.map(([key, label]) => (
        <button key={key} role="tab" aria-selected={value === key} onClick={() => onChange(key)}
          className={`tab ${value === key ? 'tab-on' : ''}`}>{label}</button>
      ))}
    </div>
  );
}
