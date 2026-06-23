import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext.jsx";
import Spinner from "../components/Spinner.jsx";

export default function RecipeDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [recipe, setRecipe] = useState(null);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    api
      .getRecipe(id)
      .then(setRecipe)
      .catch((err) => {
        setError(err.message || "Receta no encontrada");
        setRecipe(false);
      });
  }, [id]);

  async function handleCreateList() {
    if (!user) {
      navigate("/login", { state: { from: `/recipes/${id}` } });
      return;
    }
    setCreating(true);
    setError("");
    try {
      const list = await api.createListFromRecipe(id);
      navigate(`/lists/${list.id}`);
    } catch (err) {
      setError(err.message || "No se pudo crear la cesta");
      setCreating(false);
    }
  }

  if (recipe === null) return <Spinner full />;
  if (recipe === false) {
    return (
      <div className="empty">
        <div className="empty-emoji">🤔</div>
        <p>{error || "Receta no encontrada"}</p>
        <Link to="/recipes" className="btn btn-ghost" style={{ marginTop: 12 }}>
          Volver a recetas
        </Link>
      </div>
    );
  }

  return (
    <div>
      <Link to="/recipes" className="subtle">
        ← Recetas
      </Link>
      <div className="page-head" style={{ marginTop: 6 }}>
        <div>
          <h1>{recipe.title}</h1>
          <p className="subtle">{recipe.description}</p>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="recipe-meta" style={{ marginBottom: 20 }}>
        <span>⏱️ {recipe.time_minutes} min</span>
        <span>🍽️ {recipe.servings} personas</span>
        <span>📊 {recipe.difficulty}</span>
      </div>

      <div className="card" style={{ padding: 18, marginBottom: 20 }}>
        <h3 style={{ marginTop: 0 }}>Ingredientes</h3>
        {recipe.ingredients.map((ing, i) => (
          <div className="row" key={i}>
            <div className="row-main row-title">{ing.name}</div>
            <span className="badge badge-tag">
              {ing.quantity} {ing.unit}
            </span>
          </div>
        ))}
      </div>

      <button className="btn btn-primary btn-block" onClick={handleCreateList} disabled={creating}>
        {creating ? "Creando cesta…" : "🛒 Crear cesta con estos ingredientes"}
      </button>
      {!user && (
        <p className="subtle" style={{ textAlign: "center", marginTop: 10 }}>
          Necesitas iniciar sesión para guardar la cesta.
        </p>
      )}
    </div>
  );
}
