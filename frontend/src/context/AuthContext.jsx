import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Al cargar la app intentamos recuperar el perfil: la cookie HttpOnly de
  // sesión (si existe) viaja automáticamente. Si no hay sesión, /auth/me da 401.
  useEffect(() => {
    let active = true;
    async function bootstrap() {
      try {
        const me = await api.me();
        if (active) setUser(me);
      } catch {
        if (active) setUser(null);
      } finally {
        if (active) setLoading(false);
      }
    }
    bootstrap();
    return () => {
      active = false;
    };
  }, []);

  const login = useCallback(async (email, password) => {
    const data = await api.login(email, password);
    setUser(data.user);
    return data.user;
  }, []);

  const register = useCallback(async (email, password, name) => {
    const data = await api.register(email, password, name);
    setUser(data.user);
    return data.user;
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } catch {
      // aunque falle la llamada, cerramos la sesión en el cliente
    }
    setUser(null);
  }, []);

  const updateProfile = useCallback(async (data) => {
    const updated = await api.updateProfile(data);
    setUser(updated);
    return updated;
  }, []);

  const changePassword = useCallback(
    (current, next) => api.changePassword(current, next),
    []
  );

  const deleteAccount = useCallback(async (password) => {
    await api.deleteAccount(password);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        updateProfile,
        changePassword,
        deleteAccount,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de <AuthProvider>");
  return ctx;
}
