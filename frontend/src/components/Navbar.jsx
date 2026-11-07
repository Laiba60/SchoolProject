import { Link, NavLink, useNavigate } from 'react-router-dom';
import { homeFor, useAuth } from '../auth';

export const Crest = ({ size = 40 }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" aria-hidden="true">
    <circle cx="24" cy="24" r="23" fill="#1e3a8a" />
    <circle cx="24" cy="24" r="19" fill="none" stroke="#fbbf24" strokeWidth="2" />
    <text x="24" y="30" textAnchor="middle" fontFamily="Source Serif 4, Georgia, serif" fontWeight="700" fontSize="17" fill="#fbbf24">CE</text>
  </svg>
);

const link = ({ isActive }) => `px-1 py-1 hover:underline ${isActive ? 'border-b-2 border-gold' : ''}`;

export default function Navbar() {
  const { user, logout } = useAuth();
  const nav = useNavigate();

  return (
    <header className="border-b-4 border-gold bg-navy text-white">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
        <Link to="/" className="flex items-center gap-3">
          <Crest />
          <span className="font-serif text-lg font-bold tracking-wide">Center of Excellence</span>
        </Link>
        <nav className="flex flex-wrap items-center gap-4 text-sm font-semibold">
          {user ? (
            <>
              <span className="text-gold">{user.full_name} ({user.role})</span>
              <NavLink className={link} to={homeFor(user)}>Dashboard</NavLink>
              <button className="hover:underline" onClick={async () => { await logout(); nav('/login'); }}>Log out</button>
            </>
          ) : (
            <>
              <NavLink className={link} to="/register">Register</NavLink>
              <NavLink className={link} to="/login">Log in</NavLink>
              <NavLink className={link} to="/admin/login">Admin</NavLink>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
