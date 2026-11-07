import { useEffect, useState } from 'react';
import api from '../api';
import { Empty, num, pctText, Spinner, Stat } from '../ui';

export default function Student() {
  const [d, setD] = useState(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => { api.get('/student/me/').then((r) => setD(r.data)).catch(() => setFailed(true)); }, []);
  if (failed) return <div className="panel"><Empty>Your result could not be loaded. Try again later.</Empty></div>;
  if (!d) return <Spinner />;
  const p = d.profile || {};
  const res = d.results || [];
  return (
    <div className="space-y-5">
      <div>
        <h1>My result</h1>
        <p className="mt-1"><b>Student Name:</b> {p.full_name} &nbsp;|&nbsp; <b>Roll No:</b> {p.uid}</p>
        <p className="text-sm text-slate-600">Class {p.section}. Father: {p.father_name}{p.term ? <> &nbsp;|&nbsp; <b>Term:</b> {p.term}</> : null}</p>
      </div>
      {!res.length ? (
        <div className="panel"><Empty>No results have been uploaded for you yet.</Empty></div>
      ) : (
        <>
          <div className="overflow-x-auto rounded-md border border-line bg-white">
            <table className="tbl">
              <thead><tr><th>Subject</th><th>Total</th><th>Obtained</th><th>%</th><th>Grade</th></tr></thead>
              <tbody>{res.map((r) => <tr key={r.subject}><td>{r.subject}</td><td>{num(r.total_marks)}</td><td>{num(r.obtained_marks)}</td><td>{pctText(r.percentage)}</td><td>{r.grade}</td></tr>)}</tbody>
              <tfoot><tr className="bg-navy-soft font-bold"><td className="px-3 py-2">Total</td><td className="px-3 py-2">{num(d.total_marks)}</td><td className="px-3 py-2">{num(d.obtained_marks)}</td><td className="px-3 py-2">{pctText(d.percentage)}</td><td className="px-3 py-2">{d.grade}</td></tr></tfoot>
            </table>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Stat value={pctText(d.percentage)} label="Total percentage" />
            <Stat value={d.grade} label="Overall grade" />
          </div>
          <a className="btn-gold" href={`/api/reports/student/${encodeURIComponent(p.uid)}/pdf/?dl=1`}>Download as PDF</a>
        </>
      )}
    </div>
  );
}
