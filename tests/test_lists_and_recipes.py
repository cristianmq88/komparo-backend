"""Tests de cestas y recetas."""
from tests.conftest import register_and_login


def test_recipes_seeded(client):
    r = client.get("/recipes").json()
    assert r["total"] >= 50


def test_recipe_categories_endpoint(client):
    r = client.get("/recipes/categories").json()
    cat_ids = {c["id"] for c in r["categories"]}
    assert "postres" in cat_ids
    assert "pescados" in cat_ids
    assert all(c["count"] > 0 for c in r["categories"])


def test_recipes_filter_by_category(client):
    r = client.get("/recipes?category=postres").json()
    assert r["total"] > 0
    assert all(rec["category"] == "postres" for rec in r["recipes"])


def test_recipe_detail(client):
    r = client.get("/recipes/recipe_1")
    assert r.status_code == 200
    assert r.json()["title"] == "Tortilla de patatas"


def test_recipe_not_found(client):
    assert client.get("/recipes/no_existe").status_code == 404


def test_create_list_from_recipe(client):
    headers, _ = register_and_login(client, "r@x.com")
    r = client.post("/recipes/recipe_3/create-list", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Paella valenciana"
    assert len(body["items"]) > 0


def test_full_list_flow(client):
    headers, _ = register_and_login(client, "list@x.com")
    # Crear cesta
    r = client.post("/lists", headers=headers, json={"name": "Cesta test"})
    assert r.status_code == 200
    lid = r.json()["id"]

    # Añadir items
    r = client.post(
        f"/lists/{lid}/items",
        headers=headers,
        json={"name": "leche", "quantity": 2},
    )
    assert r.status_code == 200
    item_id = r.json()["id"]

    # Listar cestas
    r = client.get("/lists", headers=headers).json()
    assert len(r) == 1
    assert len(r[0]["items"]) == 1

    # Comparativa
    cmp = client.get(f"/lists/{lid}/compare", headers=headers).json()
    assert cmp["items_count"] == 1
    assert cmp["cheapest"] is not None
    assert cmp["savings"] >= 0

    # Eliminar item
    r = client.delete(f"/lists/{lid}/items/{item_id}", headers=headers)
    assert r.status_code == 200

    # Eliminar cesta
    r = client.delete(f"/lists/{lid}", headers=headers)
    assert r.status_code == 200


def test_cannot_access_other_users_list(client):
    headers_a, _ = register_and_login(client, "a@list.com")
    r = client.post("/lists", headers=headers_a, json={"name": "Mía"})
    lid = r.json()["id"]

    headers_b, _ = register_and_login(client, "b@list.com")
    # B no debe poder verla, modificarla ni borrarla
    assert client.delete(f"/lists/{lid}", headers=headers_b).status_code == 404
    assert client.post(
        f"/lists/{lid}/items",
        headers=headers_b,
        json={"name": "intruso", "quantity": 1},
    ).status_code == 404


def test_item_quantity_validation(client):
    headers, _ = register_and_login(client, "q@x.com")
    r = client.post("/lists", headers=headers, json={"name": "X"})
    lid = r.json()["id"]
    # Cantidad 0 → debe rechazarse
    r = client.post(
        f"/lists/{lid}/items",
        headers=headers,
        json={"name": "x", "quantity": 0},
    )
    assert r.status_code == 422


def test_supermarkets_endpoint(client):
    r = client.get("/supermarkets").json()
    assert len(r["supermarkets"]) == 8
