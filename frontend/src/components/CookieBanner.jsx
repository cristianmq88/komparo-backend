import { useState } from "react";
import { Link } from "react-router-dom";

const KEY = "komparo_cookie_consent";

export default function CookieBanner() {
  const [visible, setVisible] = useState(() => !localStorage.getItem(KEY));

  if (!visible) return null;

  function accept() {
    localStorage.setItem(KEY, "1");
    setVisible(false);
  }

  return (
    <div className="cookie-banner" role="dialog" aria-label="Aviso de cookies">
      <p className="cookie-text">
        Komparo solo usa almacenamiento técnico necesario para funcionar (sesión y este aviso).
        No usamos cookies de seguimiento. Más info en{" "}
        <Link to="/cookies">cookies</Link> y <Link to="/privacy">privacidad</Link>.
      </p>
      <button className="btn btn-primary btn-sm" onClick={accept}>
        Entendido
      </button>
    </div>
  );
}
