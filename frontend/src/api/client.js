// Cliente HTTP ligero para la API de Komparo.
//
// En desarrollo todas las llamadas van a /api/* y Vite las redirige al
// backend (ver vite.config.js). En producción se puede sobreescribir con
// VITE_API_BASE para apuntar directamente al backend desplegado.
const BASE = import.meta.env.VITE_API_BASE || "/api";

const TOKEN_KEY = "komparo_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request(path, { method = "GET", body, form, auth = true } = {}) {
  const headers = {};
  const token = getToken();
  if (auth && token) headers["Authorization"] = `Bearer ${token}`;

  let payload;
  if (form) {
    // OAuth2PasswordRequestForm espera application/x-www-form-urlencoded
    headers["Content-Type"] = "application/x-www-form-urlencoded";
    payload = new URLSearchParams(form).toString();
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  let res;
  try {
    res = await fetch(`${BASE}${path}`, { method, headers, body: payload });
  } catch {
    throw new ApiError("No se pudo conectar con el servidor", 0);
  }

  if (res.status === 204) return null;

  let data = null;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!res.ok) {
    const detail =
      (data && (data.detail || data.message)) ||
      (typeof data === "string" ? data : null) ||
      `Error ${res.status}`;
    throw new ApiError(
      Array.isArray(detail) ? detail.map((d) => d.msg).join(", ") : detail,
      res.status
    );
  }

  return data;
}

export const api = {
  // ── Auth ──────────────────────────────────────────────
  register: (email, password, name) =>
    request("/auth/register", { method: "POST", auth: false, body: { email, password, name } }),
  login: (email, password) =>
    request("/auth/login", { method: "POST", auth: false, form: { username: email, password } }),
  me: () => request("/auth/me"),

  // ── Datos públicos ────────────────────────────────────
  supermarkets: () => request("/supermarkets", { auth: false }),
  searchProducts: (q) =>
    request(`/products/search?q=${encodeURIComponent(q)}`, { auth: false }),

  // ── Listas / cestas ───────────────────────────────────
  getLists: () => request("/lists"),
  createList: (name, emoji) => request("/lists", { method: "POST", body: { name, emoji } }),
  deleteList: (id) => request(`/lists/${id}`, { method: "DELETE" }),
  addItem: (listId, item) =>
    request(`/lists/${listId}/items`, { method: "POST", body: item }),
  removeItem: (listId, itemId) =>
    request(`/lists/${listId}/items/${itemId}`, { method: "DELETE" }),
  compareList: (listId) => request(`/lists/${listId}/compare`),

  // ── Recetas ───────────────────────────────────────────
  getRecipes: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/recipes${qs ? `?${qs}` : ""}`, { auth: false });
  },
  getRecipe: (id) => request(`/recipes/${id}`, { auth: false }),
  createListFromRecipe: (id) =>
    request(`/recipes/${id}/create-list`, { method: "POST" }),
};

export { ApiError };
