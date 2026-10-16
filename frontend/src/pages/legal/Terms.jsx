import { Link } from "react-router-dom";

export default function Terms() {
  return (
    <article className="legal">
      <Link to="/lists" className="subtle">← Volver</Link>
      <h1>Términos y condiciones de uso</h1>
      <p className="subtle">Última actualización: 23 de junio de 2026</p>

      <div className="alert alert-info">
        Plantilla orientativa. Revísala con un profesional antes de publicarla en producción.
      </div>

      <h2>Identidad del titular (aviso legal)</h2>
      <p>
        En cumplimiento del artículo 10 de la Ley 34/2002 (LSSICE), el titular responsable de
        este servicio es <strong>Cristian Martín Quesada</strong>. Para cualquier consulta
        puedes escribir a <strong>privacidad@komparo.app</strong>.
      </p>

      <h2>1. Objeto</h2>
      <p>
        Komparo es una aplicación para organizar tus cestas de la compra y convertir recetas
        en listas de ingredientes. El uso de la App implica la aceptación de estos términos.
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

      <h2>4. Limitación de responsabilidad</h2>
      <p>
        La App se ofrece «tal cual». En la medida permitida por la ley, no nos hacemos
        responsables de pérdidas derivadas del uso de la App o de interrupciones del servicio.
      </p>

      <h2>5. Modificaciones y cuenta</h2>
      <p>
        Podemos actualizar estos términos y el servicio. Puedes dejar de usar la App y eliminar
        tu cuenta en cualquier momento desde <Link to="/settings">Mi cuenta</Link>.
      </p>
    </article>
  );
}
