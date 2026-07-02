// Muestra una comparativa de precios como barras horizontales ordenadas
// de más barato a más caro. Acepta una lista de filas:
//   [{ id, name, color, price }]
export default function PriceBars({ rows }) {
  if (!rows || rows.length === 0) {
    return <p className="subtle">Sin precios disponibles.</p>;
  }

  const sorted = [...rows].sort((a, b) => a.price - b.price);
  const max = Math.max(...sorted.map((r) => r.price)) || 1;
  const cheapest = sorted[0].price;

  return (
    <div>
      {sorted.map((r, i) => {
        const isBest = r.price === cheapest;
        return (
          <div className="price-bar-row" key={r.id}>
            <div className="price-bar-label">
              <span className="dot" style={{ background: r.color || "#888" }} />
              {r.name}
            </div>
            <div className="price-bar-track">
              <div
                className="price-bar-fill"
                style={{
                  width: `${Math.max((r.price / max) * 100, 6)}%`,
                  background: isBest ? "var(--green)" : "#c3d4cc",
                }}
              />
            </div>
            <div className="price-amount">{r.price.toFixed(2)} €</div>
            {isBest && i === 0 ? (
              <span className="badge badge-best">Más barato</span>
            ) : (
              <span style={{ width: 0 }} />
            )}
          </div>
        );
      })}
    </div>
  );
}
