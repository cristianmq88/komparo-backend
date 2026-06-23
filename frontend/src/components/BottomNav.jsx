import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

// Barra de navegación inferior, visible solo en móvil (ver index.css).
export default function BottomNav() {
  const { user } = useAuth();

  return (
    <nav className="bottom-nav">
      <NavLink to="/search" className="bottom-link">
        <span className="bn-icon">🔍</span>
        <span>Buscar</span>
      </NavLink>
      <NavLink to="/recipes" className="bottom-link">
        <span className="bn-icon">🍳</span>
        <span>Recetas</span>
      </NavLink>
      <NavLink to="/lists" className="bottom-link">
        <span className="bn-icon">🧺</span>
        <span>Cestas</span>
      </NavLink>
      <NavLink to={user ? "/settings" : "/login"} className="bottom-link">
        <span className="bn-icon">{user ? "👤" : "➡️"}</span>
        <span>{user ? "Cuenta" : "Entrar"}</span>
      </NavLink>
    </nav>
  );
}
