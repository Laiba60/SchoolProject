import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="panel mx-auto mt-10 max-w-md text-center">
      <h1>Page not found</h1>
      <p className="my-3 text-slate-600">This address does not exist.</p>
      <Link className="btn" to="/">Back to registration</Link>
    </div>
  );
}
