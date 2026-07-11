import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { api } from "../api/client";

function Notice({ msg }) {
  if (!msg) return null;
  const cls = msg.type === "error" ? "alert alert-error" : "alert alert-ok";
  return <div className={cls}>{msg.text}</div>;
}

export default function Settings() {
  const { user, updateProfile, changePassword, deleteAccount, logout } = useAuth();
  const navigate = useNavigate();

  // Perfil
  const [profile, setProfile] = useState({
    name: user?.name || "",
    phone: user?.phone || "",
    city: user?.city || "",
    postal_code: user?.postal_code || "",
  });
  const [profileMsg, setProfileMsg] = useState(null);
  const [savingProfile, setSavingProfile] = useState(false);

  // Contraseña
  const [pwd, setPwd] = useState({ current: "", next: "", confirm: "" });
  const [pwdMsg, setPwdMsg] = useState(null);
  const [savingPwd, setSavingPwd] = useState(false);

  // Eliminar cuenta
  const [delConfirm, setDelConfirm] = useState(false);
  const [delPassword, setDelPassword] = useState("");
  const [delMsg, setDelMsg] = useState(null);
  const [deleting, setDeleting] = useState(false);

  // Exportar datos
  const [exporting, setExporting] = useState(false);
  const [exportMsg, setExportMsg] = useState(null);

  async function handleExport() {
    setExportMsg(null);
    setExporting(true);
    try {
      const data = await api.exportData();
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "komparo-mis-datos.json";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setExportMsg({ type: "error", text: err.message });
    } finally {
      setExporting(false);
    }
  }

  async function saveProfile(e) {
    e.preventDefault();
    setProfileMsg(null);
    setSavingProfile(true);
    try {
      await updateProfile(profile);
      setProfileMsg({ type: "ok", text: "Perfil actualizado" });
    } catch (err) {
      setProfileMsg({ type: "error", text: err.message });
    } finally {
      setSavingProfile(false);
    }
  }

  async function savePassword(e) {
    e.preventDefault();
    setPwdMsg(null);
    if (pwd.next.length < 6) {
      setPwdMsg({ type: "error", text: "La nueva contraseña debe tener al menos 6 caracteres" });
      return;
    }
    if (pwd.next !== pwd.confirm) {
      setPwdMsg({ type: "error", text: "Las contraseñas no coinciden" });
      return;
    }
    setSavingPwd(true);
    try {
      await changePassword(pwd.current, pwd.next);
      setPwd({ current: "", next: "", confirm: "" });
      setPwdMsg({ type: "ok", text: "Contraseña actualizada" });
    } catch (err) {
      setPwdMsg({ type: "error", text: err.message });
    } finally {
      setSavingPwd(false);
    }
  }

  async function handleDelete(e) {
    e.preventDefault();
    setDelMsg(null);
    setDeleting(true);
    try {
      await deleteAccount(delPassword);
      navigate("/register", { replace: true });
    } catch (err) {
      setDelMsg({ type: "error", text: err.message });
      setDeleting(false);
    }
  }

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Mi cuenta</h1>
          <p className="subtle">{user?.email}</p>
        </div>
        <button className="btn btn-ghost" onClick={async () => { await logout(); navigate("/login"); }}>
          Cerrar sesión
        </button>
      </div>

      {/* Perfil */}
      <form className="card section" onSubmit={saveProfile}>
        <h3>Datos del perfil</h3>
        <Notice msg={profileMsg} />
        <div className="field">
          <label>Nombre</label>
          <input
            className="input"
            value={profile.name}
            onChange={(e) => setProfile({ ...profile, name: e.target.value })}
            required
          />
        </div>
        <div className="grid-2">
          <div className="field">
            <label>Teléfono</label>
            <input
              className="input"
              value={profile.phone}
              onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
              placeholder="Opcional"
            />
          </div>
          <div className="field">
            <label>Código postal</label>
            <input
              className="input"
              value={profile.postal_code}
              onChange={(e) => setProfile({ ...profile, postal_code: e.target.value })}
              placeholder="28001"
            />
          </div>
        </div>
        <div className="field">
          <label>Ciudad</label>
          <input
            className="input"
            value={profile.city}
            onChange={(e) => setProfile({ ...profile, city: e.target.value })}
            placeholder="Madrid"
          />
        </div>
        <button className="btn btn-primary" disabled={savingProfile}>
          {savingProfile ? "Guardando…" : "Guardar cambios"}
        </button>
      </form>

      {/* Contraseña */}
      <form className="card section" onSubmit={savePassword}>
        <h3>Cambiar contraseña</h3>
        <Notice msg={pwdMsg} />
        <div className="field">
          <label>Contraseña actual</label>
          <input
            type="password"
            className="input"
            value={pwd.current}
            onChange={(e) => setPwd({ ...pwd, current: e.target.value })}
            required
            autoComplete="current-password"
          />
        </div>
        <div className="grid-2">
          <div className="field">
            <label>Nueva contraseña</label>
            <input
              type="password"
              className="input"
              value={pwd.next}
              onChange={(e) => setPwd({ ...pwd, next: e.target.value })}
              required
              autoComplete="new-password"
            />
          </div>
          <div className="field">
            <label>Repetir nueva contraseña</label>
            <input
              type="password"
              className="input"
              value={pwd.confirm}
              onChange={(e) => setPwd({ ...pwd, confirm: e.target.value })}
              required
              autoComplete="new-password"
            />
          </div>
        </div>
        <button className="btn btn-primary" disabled={savingPwd}>
          {savingPwd ? "Actualizando…" : "Actualizar contraseña"}
        </button>
      </form>

      {/* Descargar mis datos (portabilidad RGPD) */}
      <div className="card section">
        <h3>Descargar mis datos</h3>
        <Notice msg={exportMsg} />
        <p className="subtle">
          Descarga una copia de todos tus datos (cuenta, cestas y productos) en formato
          JSON (derecho de portabilidad, RGPD).
        </p>
        <button className="btn btn-ghost" onClick={handleExport} disabled={exporting}>
          {exporting ? "Preparando…" : "Descargar mis datos (JSON)"}
        </button>
      </div>

      {/* Zona peligrosa */}
      <div className="card section danger-zone">
        <h3>Eliminar cuenta</h3>
        <p className="subtle">
          Esta acción es permanente. Se borrarán tu cuenta, tus cestas y todos tus datos
          (derecho de supresión, RGPD). No se puede deshacer.
        </p>
        {!delConfirm ? (
          <button className="btn btn-danger" onClick={() => setDelConfirm(true)}>
            Quiero eliminar mi cuenta
          </button>
        ) : (
          <form onSubmit={handleDelete}>
            <Notice msg={delMsg} />
            <div className="field">
              <label>Confirma con tu contraseña</label>
              <input
                type="password"
                className="input"
                value={delPassword}
                onChange={(e) => setDelPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>
            <div style={{ display: "flex", gap: 10 }}>
              <button className="btn btn-danger" disabled={deleting}>
                {deleting ? "Eliminando…" : "Eliminar definitivamente"}
              </button>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => { setDelConfirm(false); setDelPassword(""); setDelMsg(null); }}
              >
                Cancelar
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
