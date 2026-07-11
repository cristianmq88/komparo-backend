import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/login");
  }

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <NavLink to="/search" className="brand">
          <img src="/komparo.svg" alt="" />
          Komparo
        </NavLink>

        <div className="nav-links">
          <NavLink to="/search" className="nav-link">
            Buscar
          </NavLink>
          <NavLink to="/recipes" className="nav-link">
            Recetas
          </NavLink>
          {user && (
            <NavLink to="/lists" className="nav-link">
              Mis cestas
            </NavLink>
          )}
          {user ? (
            <>
              <NavLink to="/settings" className="nav-link">
                Mi cuenta
              </NavLink>
              <button className="btn btn-ghost btn-sm" onClick={handleLogout}>
                Salir
              </button>
            </>
          ) : (
            <NavLink to="/login" className="btn btn-primary btn-sm">
              Entrar
            </NavLink>
          )}
        </div>
      </div>
    </nav>
  );
}
