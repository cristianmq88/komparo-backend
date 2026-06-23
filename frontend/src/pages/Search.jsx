import { useEffect, useState } from "react";
import { api } from "../api/client";
import PriceBars from "../components/PriceBars.jsx";
import Spinner from "../components/Spinner.jsx";

export default function Search() {
  const [query, setQuery] = useState("");
  const [supermarkets, setSupermarkets] = useState({});
  const [products, setProducts] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Cargar el catálogo de supermercados (para nombres y colores).
  useEffect(() => {
    api
      .supermarkets()
      .then((data) => {
        const map = {};
        for (const sm of data.supermarkets) map[sm.id] = sm;
        setSupermarkets(map);
      })
      .catch(() => {});
  }, []);

  async function handleSearch(e) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError("");
    try {
      const data = await api.searchProducts(query.trim());
      setProducts(data.products || []);
    } catch (err) {
      setError(err.message || "Error al buscar");
    } finally {
      setLoading(false);
    }
  }

  function toRows(prices) {
    return Object.entries(prices).map(([id, price]) => ({
      id,
      name: supermarkets[id]?.name || id,
      color: supermarkets[id]?.color,
      price,
    }));
  }

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Comparar precios</h1>
          <p className="subtle">Busca un producto y descubre dónde es más barato</p>
        </div>
      </div>

      <form onSubmit={handleSearch} style={{ display: "flex", gap: 10, marginBottom: 24 }}>
        <input
          className="input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="leche, pan, huevos, aceite…"
          autoFocus
        />
        <button className="btn btn-primary" disabled={loading}>
          Buscar
        </button>
      </form>

      {error && <div className="alert alert-error">{error}</div>}
      {loading && <Spinner full />}

      {!loading && products && products.length === 0 && (
        <div className="empty">
          <div className="empty-emoji">🔍</div>
          <p>No encontramos productos para «{query}».</p>
        </div>
      )}

      {!loading && products && products.length > 0 && (
        <div className="grid">
          {products.map((p, idx) => (
            <div className="card" key={idx} style={{ padding: 18 }}>
              <h3 style={{ margin: "0 0 12px" }}>{p.name}</h3>
              <PriceBars rows={toRows(p.prices)} />
            </div>
          ))}
        </div>
      )}

      {!loading && !products && (
        <div className="empty">
          <div className="empty-emoji">🛒</div>
          <p>Empieza buscando un producto arriba.</p>
        </div>
      )}
    </div>
  );
}
