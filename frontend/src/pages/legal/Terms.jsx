import { Link } from "react-router-dom";

export default function Terms() {
  return (
    <article className="legal">
      <Link to="/search" className="subtle">← Volver</Link>
      <h1>Términos y condiciones de uso</h1>
      <p className="subtle">Última actualización: 23 de junio de 2026</p>

      <div className="alert alert-info">
        Plantilla orientativa. Antes de publicarla en producción, revísala con un
        profesional y <strong>completa los datos del titular marcados entre corchetes
        [ ]</strong> en la sección «Identidad del titular».
      </div>

      <h2>Identidad del titular (aviso legal)</h2>
      <p>
        En cumplimiento del artículo 10 de la Ley 34/2002 (LSSICE), se informa de que el
        titular responsable de este servicio es:
      </p>
      <ul>
        <li><strong>Titular / razón social:</strong> [RAZÓN SOCIAL O NOMBRE Y APELLIDOS]</li>
        <li><strong>NIF / DNI:</strong> [NIF / DNI]</li>
        <li><strong>Domicilio:</strong> [DOMICILIO FISCAL]</li>
        <li><strong>Correo de contacto:</strong> [EMAIL DE CONTACTO]</li>
      </ul>

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
