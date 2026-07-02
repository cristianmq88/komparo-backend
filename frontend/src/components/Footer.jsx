import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <span className="subtle">© {new Date().getFullYear()} Komparo</span>
        <nav className="footer-links">
          <Link to="/privacy">Privacidad</Link>
          <Link to="/terms">Términos</Link>
          <Link to="/cookies">Cookies</Link>
        </nav>
      </div>
    </footer>
  );
}
