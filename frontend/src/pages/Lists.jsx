import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import Spinner from "../components/Spinner.jsx";

const EMOJIS = ["🛒", "🍳", "🥗", "🎉", "🏠", "🍕", "🧺", "🐶"];

export default function Lists() {
  const navigate = useNavigate();
  const [lists, setLists] = useState(null);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [emoji, setEmoji] = useState("🛒");
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      const data = await api.getLists();
      setLists(data);
    } catch (err) {
      setError(err.message || "No se pudieron cargar las cestas");
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleCreate(e) {
    e.preventDefault();
    if (!name.trim()) return;
    setBusy(true);
    try {
      const list = await api.createList(name.trim(), emoji);
      setName("");
      setEmoji("🛒");
      setCreating(false);
      navigate(`/lists/${list.id}`);
    } catch (err) {
      setError(err.message || "No se pudo crear la cesta");
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(e, id) {
    e.stopPropagation();
    if (!confirm("¿Eliminar esta cesta?")) return;
    try {
      await api.deleteList(id);
      setLists((prev) => prev.filter((l) => l.id !== id));
    } catch (err) {
      setError(err.message || "No se pudo eliminar");
    }
  }

  if (lists === null) return <Spinner full />;

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Mis cestas</h1>
          <p className="subtle">Crea listas y compáralas entre supermercados</p>
        </div>
        <button className="btn btn-primary" onClick={() => setCreating((v) => !v)}>
          {creating ? "Cancelar" : "+ Nueva cesta"}
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {creating && (
        <form className="card" style={{ padding: 18, marginBottom: 20 }} onSubmit={handleCreate}>
          <div className="field">
            <label>Nombre de la cesta</label>
            <input
              className="input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Compra semanal"
              autoFocus
            />
          </div>
          <div className="field">
            <label>Emoji</label>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {EMOJIS.map((em) => (
                <button
                  type="button"
                  key={em}
                  onClick={() => setEmoji(em)}
                  className="btn btn-ghost"
                  style={{
                    fontSize: 20,
                    padding: "6px 10px",
                    borderColor: emoji === em ? "var(--green)" : "var(--line)",
                    background: emoji === em ? "var(--green-light)" : "transparent",
                  }}
                >
                  {em}
                </button>
              ))}
            </div>
          </div>
          <button className="btn btn-primary" disabled={busy}>
            {busy ? "Creando…" : "Crear cesta"}
          </button>
        </form>
      )}

      {lists.length === 0 ? (
        <div className="empty">
          <div className="empty-emoji">🧺</div>
          <p>Aún no tienes cestas. ¡Crea la primera!</p>
        </div>
      ) : (
        <div className="grid grid-cards">
          {lists.map((l) => (
            <div className="card tile" key={l.id} onClick={() => navigate(`/lists/${l.id}`)}>
              <div className="tile-emoji">{l.emoji}</div>
              <h3 style={{ margin: "8px 0 4px" }}>{l.name}</h3>
              <p className="subtle">
                {l.items?.length || 0} {l.items?.length === 1 ? "producto" : "productos"}
              </p>
              <button
                className="btn btn-danger btn-sm"
                style={{ marginTop: 10 }}
                onClick={(e) => handleDelete(e, l.id)}
              >
                Eliminar
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
