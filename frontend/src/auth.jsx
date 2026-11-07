import { createContext, useContext, useEffect, useState } from 'react';
import api from './api';

const Ctx = createContext(null);
export const useAuth = () => useContext(Ctx);

export const homeFor = (u) =>
  !u ? '/login' : u.role === 'admin' ? '/admin/users' : u.role === 'teacher' ? '/teacher' : '/student';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        await api.get('/auth/csrf/'); // sets the csrftoken cookie
        setUser((await api.get('/auth/me/')).data);
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const login = async (uid, password, role) => {
    const { data } = await api.post('/auth/login/', { uid, password, role });
    setUser(data);
    return data;
  };

  const logout = async () => {
    try { await api.post('/auth/logout/'); } catch { /* session already gone */ }
    setUser(null);
    api.get('/auth/csrf/').catch(() => {});
  };

  return <Ctx.Provider value={{ user, loading, login, logout }}>{children}</Ctx.Provider>;
}
