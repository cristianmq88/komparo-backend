import { Link } from "react-router-dom";

export default function Privacy() {
  return (
    <article className="legal">
      <Link to="/search" className="subtle">← Volver</Link>
      <h1>Política de privacidad</h1>
      <p className="subtle">Última actualización: 23 de junio de 2026</p>

      <div className="alert alert-info">
        Este documento es una plantilla orientativa conforme al RGPD (UE 2016/679) y la
        LOPDGDD. Antes de publicar en producción, revísalo con un profesional y completa los
        datos del responsable.
      </div>

      <h2>1. Responsable del tratamiento</h2>
      <p>
        Komparo (en adelante, «la App»). Para cualquier cuestión relativa a tus datos puedes
        escribir a <strong>privacidad@komparo.app</strong>.
      </p>

      <h2>2. Qué datos tratamos</h2>
      <ul>
        <li><strong>Datos de cuenta:</strong> nombre, correo electrónico y contraseña (cifrada).</li>
        <li><strong>Datos opcionales de perfil:</strong> teléfono, ciudad y código postal.</li>
        <li><strong>Datos de uso:</strong> cestas de la compra y productos que guardas.</li>
        <li><strong>Datos técnicos:</strong> los imprescindibles para mantener la sesión.</li>
      </ul>

      <h2>3. Finalidad y base jurídica</h2>
      <ul>
        <li>Prestar el servicio (gestión de cuenta, cestas y comparativa de precios): ejecución del contrato.</li>
        <li>Seguridad y prevención de abusos: interés legítimo.</li>
        <li>Comunicaciones del servicio: ejecución del contrato.</li>
      </ul>

      <h2>4. Conservación</h2>
      <p>
        Conservamos tus datos mientras tu cuenta esté activa. Si eliminas tu cuenta, borramos
        tus datos personales de forma permanente, salvo obligaciones legales de conservación.
      </p>

      <h2>5. Destinatarios</h2>
      <p>
        No vendemos tus datos. Podemos usar proveedores de alojamiento y base de datos que
        actúan como encargados del tratamiento bajo contrato y dentro del EEE o con garantías
        adecuadas.
      </p>

      <h2>6. Tus derechos</h2>
      <p>
        Puedes ejercer tus derechos de acceso, rectificación, supresión, oposición, limitación
        y portabilidad. Desde <Link to="/settings">Mi cuenta</Link> puedes editar tus datos o
        eliminar tu cuenta directamente. También puedes reclamar ante la Agencia Española de
        Protección de Datos (www.aepd.es).
      </p>

      <h2>7. Seguridad</h2>
      <p>
        Las contraseñas se almacenan cifradas (hash bcrypt) y la sesión se gestiona mediante
        tokens. Aplicamos medidas técnicas y organizativas razonables para proteger tu
        información.
      </p>
    </article>
  );
}
