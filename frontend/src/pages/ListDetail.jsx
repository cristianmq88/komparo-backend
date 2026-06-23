import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { api } from "../api/client";
import PriceBars from "../components/PriceBars.jsx";
import Spinner from "../components/Spinner.jsx";

export default function ListDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [list, setList] = useState(null);
  const [error, setError] = useState("");
  const [itemName, setItemName] = useState("");
  const [qty, setQty] = useState(1);
  const [adding, setAdding] = useState(false);

  const [comparison, setComparison] = useState(null);
  const [comparing, setComparing] = useState(false);

  async function load() {
    try {
      // El backend no expone GET /lists/{id}, así que filtramos de /lists.
      const lists = await api.getLists();
      const found = lists.find((l) => l.id === id);
      if (!found) {
        setError("Cesta no encontrada");
        setList(false);
        return;
      }
      setList(found);
    } catch (err) {
      setError(err.message || "No se pudo cargar la cesta");
      setList(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function handleAdd(e) {
    e.preventDefault();
    if (!itemName.trim()) return;
    setAdding(true);
    setError("");
    try {
      await api.addItem(id, { name: itemName.trim(), quantity: Number(qty) || 1 });
      setItemName("");
      setQty(1);
      setComparison(null);
      await load();
    } catch (err) {
      setError(err.message || "No se pudo añadir el producto");
    } finally {
      setAdding(false);
    }
  }

  async function handleRemove(itemId) {
    try {
      await api.removeItem(id, itemId);
      setComparison(null);
      await load();
    } catch (err) {
      setError(err.message || "No se pudo quitar el producto");
    }
  }

  async function handleCompare() {
    setComparing(true);
    setError("");
    try {
      const data = await api.compareList(id);
      setComparison(data);
    } catch (err) {
      setError(err.message || "No se pudo comparar");
    } finally {
      setComparing(false);
    }
  }

  if (list === null) return <Spinner full />;
  if (list === false) {
    return (
      <div className="empty">
        <div className="empty-emoji">🤔</div>
        <p>{error || "Cesta no encontrada"}</p>
        <Link to="/lists" className="btn btn-ghost" style={{ marginTop: 12 }}>
          Volver a mis cestas
        </Link>
      </div>
    );
  }

  const rows =
    comparison?.ranking?.map((r) => ({
      id: r.supermarket,
      name: r.name,
      color: r.color,
      price: r.total,
    })) || [];

  return (
    <div>
      <div className="page-head">
        <div>
          <Link to="/lists" className="subtle">
            ← Mis cestas
          </Link>
          <h1 style={{ marginTop: 6 }}>
            {list.emoji} {list.name}
          </h1>
          <p className="subtle">
            {list.items.length} {list.items.length === 1 ? "producto" : "productos"}
          </p>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <form className="card" style={{ padding: 16, marginBottom: 20 }} onSubmit={handleAdd}>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <input
            className="input"
            style={{ flex: 3, minWidth: 180 }}
            value={itemName}
            onChange={(e) => setItemName(e.target.value)}
            placeholder="Añadir producto (ej: leche, pan…)"
          />
          <input
            className="input"
            style={{ flex: 1, minWidth: 80 }}
            type="number"
            min="1"
            value={qty}
            onChange={(e) => setQty(e.target.value)}
          />
          <button className="btn btn-primary" disabled={adding}>
            Añadir
          </button>
        </div>
      </form>

      {list.items.length === 0 ? (
        <div className="empty">
          <div className="empty-emoji">📝</div>
          <p>Añade productos a tu cesta para poder compararla.</p>
        </div>
      ) : (
        <>
          <div className="card" style={{ marginBottom: 20 }}>
            {list.items.map((item) => (
              <div className="row" key={item.id}>
                <div className="row-main">
                  <div className="row-title">{item.name}</div>
                  {item.notes && <div className="subtle">{item.notes}</div>}
                </div>
                <span className="badge badge-tag">x{item.quantity}</span>
                <button className="btn btn-danger btn-sm" onClick={() => handleRemove(item.id)}>
                  Quitar
                </button>
              </div>
            ))}
          </div>

          <button className="btn btn-primary btn-block" onClick={handleCompare} disabled={comparing}>
            {comparing ? "Comparando…" : "💰 Comparar en todos los súper"}
          </button>
        </>
      )}

      {comparison && (
        <div style={{ marginTop: 22 }}>
          {comparison.cheapest && (
            <div className="savings-banner">
              <div>El más barato es</div>
              <div className="big">
                {comparison.cheapest.name} · {comparison.cheapest.total.toFixed(2)} €
              </div>
              {comparison.savings > 0 && (
                <div style={{ marginTop: 6 }}>
                  Ahorras hasta <strong>{comparison.savings.toFixed(2)} €</strong> frente al más caro
                </div>
              )}
            </div>
          )}
          <div className="card" style={{ padding: 18 }}>
            <h3 style={{ margin: "0 0 12px" }}>Comparativa de la cesta</h3>
            <PriceBars rows={rows} />
          </div>
        </div>
      )}
    </div>
  );
}
