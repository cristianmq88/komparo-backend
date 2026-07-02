import { Link } from "react-router-dom";

export default function Terms() {
  return (
    <article className="legal">
      <Link to="/search" className="subtle">← Volver</Link>
      <h1>Términos y condiciones de uso</h1>
      <p className="subtle">Última actualización: 23 de junio de 2026</p>

      <div className="alert alert-info">
        Plantilla orientativa. Revísala con un profesional antes de publicarla en producción.
      </div>

      <h2>1. Objeto</h2>
      <p>
        Komparo es una aplicación que permite buscar productos, comparar sus precios entre
        supermercados y organizar cestas de la compra. El uso de la App implica la aceptación
        de estos términos.
      </p>

      <h2>2. Cuenta de usuario</h2>
      <p>
        Eres responsable de mantener la confidencialidad de tu contraseña y de toda actividad
        realizada desde tu cuenta. Debes facilitar información veraz al registrarte.
      </p>

      <h2>3. Uso aceptable</h2>
      <ul>
        <li>No utilizar la App con fines ilícitos o que dañen el servicio.</li>
        <li>No intentar acceder a cuentas o datos de otros usuarios.</li>
        <li>No realizar un uso automatizado o masivo que comprometa el rendimiento.</li>
      </ul>

      <h2>4. Precios e información</h2>
      <p>
        Los precios mostrados se obtienen de fuentes públicas de los supermercados y pueden no
        estar siempre actualizados o ser exactos. Tienen carácter <strong>informativo</strong>;
        el precio válido es siempre el del establecimiento en el momento de la compra. Komparo no
        vende productos ni participa en las transacciones.
      </p>

      <h2>5. Marcas de terceros</h2>
      <p>
        Los nombres y marcas de los supermercados pertenecen a sus respectivos titulares. Komparo
        no está afiliada ni patrocinada por ellos.
      </p>

      <h2>6. Limitación de responsabilidad</h2>
      <p>
        La App se ofrece «tal cual». En la medida permitida por la ley, no nos hacemos
        responsables de decisiones de compra tomadas a partir de la información mostrada.
      </p>

      <h2>7. Modificaciones y cuenta</h2>
      <p>
        Podemos actualizar estos términos y el servicio. Puedes dejar de usar la App y eliminar
        tu cuenta en cualquier momento desde <Link to="/settings">Mi cuenta</Link>.
      </p>
    </article>
  );
}
