import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import PriceBars from "../components/PriceBars.jsx";
import Spinner from "../components/Spinner.jsx";

export default function Search() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [supermarkets, setSupermarkets] = useState({});
  const [products, setProducts] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

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
    if (query.trim().length < 2) return;
    setLoading(true);
    setError("");
    try {
      const data = await api.searchRealProducts(query.trim());
      setProducts(data.products || []);
    } catch (err) {
      setError(err.message || "Error al buscar");
    } finally {
      setLoading(false);
    }
  }

  function toRows(prices) {
    return prices.map((p) => ({
      id: p.supermarket,
      name: supermarkets[p.supermarket]?.name || p.supermarket,
      color: supermarkets[p.supermarket]?.color,
      price: p.price,
    }));
  }

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Comparar precios</h1>
          <p className="subtle">Precios reales de los supermercados, actualizados a diario</p>
        </div>
      </div>

      <form onSubmit={handleSearch} className="search-bar">
        <input
          className="input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="leche, pan, aceite de oliva…"
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
          <p>No encontramos «{query}» en los precios reales todavía.</p>
          <p className="subtle">
            La base de precios se va llenando con los scrapers. Prueba con otro término
            o vuelve más tarde.
          </p>
        </div>
      )}

      {!loading && products && products.length > 0 && (
        <div className="grid">
          {products.map((p) => (
            <div
              className="card product-card"
              key={p.id}
              onClick={() => navigate(`/product/${p.id}`)}
            >
              <div className="product-head">
                {p.image_url ? (
                  <img className="product-img" src={p.image_url} alt="" loading="lazy" />
                ) : (
                  <div className="product-img product-img--placeholder">🛒</div>
                )}
                <div className="row-main">
                  <div className="row-title">{p.name}</div>
                  {p.brand && <div className="subtle">{p.brand}</div>}
                  {p.cheapest_price != null && (
                    <div className="subtle">
                      Desde <strong>{p.cheapest_price.toFixed(2)} €</strong> en{" "}
                      {supermarkets[p.cheapest_supermarket]?.name || p.cheapest_supermarket}
                    </div>
                  )}
                </div>
              </div>
              {p.prices?.length > 0 && <PriceBars rows={toRows(p.prices)} />}
            </div>
          ))}
        </div>
      )}

      {!loading && !products && (
        <div className="empty">
          <div className="empty-emoji">🛒</div>
          <p>Busca un producto para ver dónde es más barato.</p>
        </div>
      )}
    </div>
  );
}
