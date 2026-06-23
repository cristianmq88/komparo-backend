import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import Spinner from "../components/Spinner.jsx";

const CATEGORIES = [
  { id: "", label: "Todas" },
  { id: "platos-principales", label: "Platos principales" },
  { id: "carnes", label: "Carnes" },
  { id: "pescados", label: "Pescados" },
  { id: "postres", label: "Postres" },
];

export default function Recipes() {
  const navigate = useNavigate();
  const [recipes, setRecipes] = useState(null);
  const [category, setCategory] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    setRecipes(null);
    const params = category ? { category } : {};
    api
      .getRecipes(params)
      .then((data) => setRecipes(data.recipes || []))
      .catch((err) => setError(err.message || "No se pudieron cargar las recetas"));
  }, [category]);

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Recetas</h1>
          <p className="subtle">Convierte una receta en una cesta con un clic</p>
        </div>
      </div>

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 20 }}>
        {CATEGORIES.map((c) => (
          <button
            key={c.id}
            className="btn btn-ghost btn-sm"
            onClick={() => setCategory(c.id)}
            style={{
              borderColor: category === c.id ? "var(--green)" : "var(--line)",
              background: category === c.id ? "var(--green-light)" : "transparent",
              color: category === c.id ? "var(--green-dark)" : "var(--muted)",
            }}
          >
            {c.label}
          </button>
        ))}
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {recipes === null && <Spinner full />}

      {recipes && recipes.length === 0 && (
        <div className="empty">
          <div className="empty-emoji">🍽️</div>
          <p>No hay recetas en esta categoría.</p>
        </div>
      )}

      {recipes && recipes.length > 0 && (
        <div className="grid grid-cards">
          {recipes.map((r) => (
            <div className="card tile" key={r.id} onClick={() => navigate(`/recipes/${r.id}`)}>
              <h3 style={{ margin: "0 0 6px" }}>{r.title}</h3>
              <p className="subtle" style={{ margin: "0 0 12px" }}>
                {r.description}
              </p>
              <div className="recipe-meta">
                <span>⏱️ {r.time_minutes} min</span>
                <span>🍽️ {r.servings} pers.</span>
                <span>📊 {r.difficulty}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
