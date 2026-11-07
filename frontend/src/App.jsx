import { Navigate, Route, Routes } from 'react-router-dom';
import { homeFor, useAuth } from './auth';
import Navbar from './components/Navbar';
import { Spinner } from './ui';
import Register from './pages/Register';
import Login from './pages/Login';
import Teacher from './pages/Teacher';
import Student from './pages/Student';
import Admin from './pages/Admin';
import NotFound from './pages/NotFound';

// Blocks a page unless the signed-in user has the given role. The server enforces this too.
function Protected({ role, children }) {
  const { user, loading } = useAuth();
  if (loading) return <Spinner />;
  if (!user) return <Navigate to={role === 'admin' ? '/admin/login' : '/login'} replace />;
  if (user.role !== role) return <Navigate to={homeFor(user)} replace />;
  return children;
}

export default function App() {
  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Routes>
          <Route path="/" element={<Register />} />
          <Route path="/register" element={<Register />} />
          <Route path="/login" element={<Login />} />
          <Route path="/admin/login" element={<Login admin />} />
          <Route path="/teacher" element={<Protected role="teacher"><Teacher /></Protected>} />
          <Route path="/student" element={<Protected role="student"><Student /></Protected>} />
          <Route path="/admin" element={<Navigate to="/admin/users" replace />} />
          <Route path="/admin/:page" element={<Protected role="admin"><Admin /></Protected>} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
    </>
  );
}
