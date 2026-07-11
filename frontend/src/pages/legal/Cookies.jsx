import { Link } from "react-router-dom";

export default function Cookies() {
  return (
    <article className="legal">
      <Link to="/search" className="subtle">← Volver</Link>
      <h1>Política de cookies y almacenamiento</h1>
      <p className="subtle">Última actualización: 23 de junio de 2026</p>

      <h2>1. Qué usamos</h2>
      <p>
        Komparo <strong>no utiliza cookies publicitarias ni de seguimiento de terceros</strong>.
        Solo empleamos almacenamiento técnico imprescindible para que la App funcione.
      </p>

      <h2>2. Almacenamiento técnico necesario</h2>
      <ul>
        <li>
          <strong>komparo_token</strong> (cookie HttpOnly): mantiene tu sesión iniciada de forma
          segura —no es accesible desde JavaScript— para que no tengas que escribir la contraseña
          en cada visita.
        </li>
        <li>
          <strong>komparo_cookie_consent</strong> (localStorage): recuerda que has visto este
          aviso para no volver a mostrarlo.
        </li>
      </ul>
      <p>
        Este almacenamiento es necesario para el servicio y está exento de consentimiento previo
        según la normativa. No se comparte con terceros.
      </p>

      <h2>3. Cómo eliminarlo</h2>
      <p>
        Puedes borrar este almacenamiento cerrando sesión o limpiando los datos del sitio desde
        la configuración de tu navegador.
      </p>

      <p>
        Consulta también nuestra <Link to="/privacy">política de privacidad</Link>.
      </p>
    </article>
  );
}
