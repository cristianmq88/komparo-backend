import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";
import PriceBars from "../components/PriceBars.jsx";
import Spinner from "../components/Spinner.jsx";

export default function ProductDetail() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [supermarkets, setSupermarkets] = useState({});
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .supermarkets()
      .then((d) => {
        const map = {};
        for (const sm of d.supermarkets) map[sm.id] = sm;
        setSupermarkets(map);
      })
      .catch(() => {});

    api
      .productPrices(id)
      .then(setData)
      .catch((err) => {
        setError(err.message || "Producto no encontrado");
        setData(false);
      });
  }, [id]);

  if (data === null) return <Spinner full />;
  if (data === false) {
    return (
      <div className="empty">
        <div className="empty-emoji">🤔</div>
        <p>{error || "Producto no encontrado"}</p>
        <Link to="/search" className="btn btn-ghost" style={{ marginTop: 12 }}>
          Volver a buscar
        </Link>
      </div>
    );
  }

  const { product, prices } = data;
  const rows = prices.map((p) => ({
    id: p.supermarket,
    name: supermarkets[p.supermarket]?.name || p.supermarket,
    color: supermarkets[p.supermarket]?.color,
    price: p.price,
  }));

  return (
    <div>
      <Link to="/search" className="subtle">
        ← Buscar
      </Link>

      <div className="product-detail-head card">
        {product.image_url ? (
          <img className="product-img-lg" src={product.image_url} alt="" />
        ) : (
          <div className="product-img-lg product-img--placeholder">🛒</div>
        )}
        <div>
          <h1 style={{ margin: "0 0 4px" }}>{product.name}</h1>
          {product.brand && <p className="subtle" style={{ margin: 0 }}>{product.brand}</p>}
        </div>
      </div>

      <div className="card" style={{ padding: 18, marginTop: 18 }}>
        <h3 style={{ marginTop: 0 }}>Precio por supermercado</h3>
        <PriceBars rows={rows} />
      </div>

      {prices.some((p) => p.product_url) && (
        <div className="card" style={{ padding: 18, marginTop: 18 }}>
          <h3 style={{ marginTop: 0 }}>Comprar online</h3>
          {prices
            .filter((p) => p.product_url)
            .map((p) => (
              <div className="row" key={p.supermarket}>
                <div className="row-main row-title">
                  {supermarkets[p.supermarket]?.name || p.supermarket}
                </div>
                <span className="price-amount">{p.price.toFixed(2)} €</span>
                <a
                  className="btn btn-ghost btn-sm"
                  href={p.product_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Ver
                </a>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
