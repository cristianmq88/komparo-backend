// Cliente HTTP ligero para la API de Komparo.
//
// - En desarrollo: BASE = "/api" y Vite hace proxy al backend (vite.config.js).
// - En producción de despliegue único (FastAPI sirve la web): se compila con
//   VITE_API_BASE="" para que las llamadas vayan al mismo origen (/auth/login…).
// - Para frontend y backend separados: VITE_API_BASE = URL absoluta del backend.
const BASE = import.meta.env.VITE_API_BASE ?? "/api";

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
  updateProfile: (data) => request("/auth/me", { method: "PUT", body: data }),
  changePassword: (current_password, new_password) =>
    request("/auth/change-password", { method: "POST", body: { current_password, new_password } }),
  deleteAccount: (password) =>
    request("/auth/me", { method: "DELETE", body: { password } }),
  exportData: () => request("/auth/me/export"),

  // ── Datos públicos ────────────────────────────────────
  supermarkets: () => request("/supermarkets", { auth: false }),

  // Precios reales (poblados por los scrapers)
  searchRealProducts: (q) =>
    request(`/products/real/search?q=${encodeURIComponent(q)}`, { auth: false }),
  productPrices: (id) => request(`/products/real/${id}/prices`, { auth: false }),
  productHistory: (id, days = 30) =>
    request(`/products/real/${id}/history?days=${days}`, { auth: false }),

  // ── Listas / cestas ───────────────────────────────────
  getLists: () => request("/lists"),
  getList: (id) => request(`/lists/${id}`),
  createList: (name, emoji) => request("/lists", { method: "POST", body: { name, emoji } }),
  deleteList: (id) => request(`/lists/${id}`, { method: "DELETE" }),
  addItem: (listId, item) =>
    request(`/lists/${listId}/items`, { method: "POST", body: item }),
  removeItem: (listId, itemId) =>
    request(`/lists/${listId}/items/${itemId}`, { method: "DELETE" }),
  // Comparativa con precios reales
  compareListReal: (listId) =>
    request(`/products/real/compare-list?list_id=${encodeURIComponent(listId)}`, { method: "POST" }),

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
