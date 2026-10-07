def register(client, email="admin@example.com", full_name="Admin User"):
    response = client.post(
        "/api/auth/register",
        json={"email": email, "full_name": full_name, "password": "StrongPass123"},
    )
    assert response.status_code == 201
    return response.json()


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_health_is_public(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_login_and_order_workflow(client):
    account = register(client)
    headers = auth_headers(account["access_token"])

    assert account["user"]["role"] == "admin"
    assert client.get("/api/dashboard", headers=headers).json()["total_clients"] == 0

    unauthenticated = client.get("/api/clients")
    assert unauthenticated.status_code == 401

    created_client = client.post(
        "/api/clients",
        headers=headers,
        json={
            "name": "Иван Петров",
            "company": "ООО Север",
            "email": "ivan@example.com",
            "phone": "+7 900 000-00-00",
        },
    )
    assert created_client.status_code == 201
    client_id = created_client.json()["id"]

    created_order = client.post(
        "/api/orders",
        headers=headers,
        json={
            "client_id": client_id,
            "title": "Сайт компании",
            "description": "Лендинг и форма заявки",
            "amount": 150000,
        },
    )
    assert created_order.status_code == 201
    order = created_order.json()
    assert order["status"] == "new"
    assert order["client_name"] == "Иван Петров"

    updated = client.patch(
        f"/api/orders/{order['id']}",
        headers=headers,
        json={"status": "in_progress"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "in_progress"

    dashboard = client.get("/api/dashboard", headers=headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["total_clients"] == 1
    assert dashboard.json()["active_orders"] == 1

    login = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "StrongPass123"},
    )
    assert login.status_code == 200
    assert login.json()["user"]["email"] == "admin@example.com"


def test_roles_and_validation(client):
    admin = register(client)
    manager = register(client, "manager@example.com", "Manager User")
    assert manager["user"]["role"] == "manager"

    client_response = client.post(
        "/api/clients",
        headers=auth_headers(admin["access_token"]),
        json={"name": "Client"},
    )
    client_id = client_response.json()["id"]

    forbidden = client.delete(
        f"/api/clients/{client_id}",
        headers=auth_headers(manager["access_token"]),
    )
    assert forbidden.status_code == 403

    invalid = client.post(
        "/api/clients",
        headers=auth_headers(admin["access_token"]),
        json={"name": "x", "email": "bad-email"},
    )
    assert invalid.status_code == 422


def test_duplicate_registration_is_rejected(client):
    register(client)

    duplicate = client.post(
        "/api/auth/register",
        json={"email": "ADMIN@example.com", "full_name": "Another User", "password": "StrongPass123"},
    )

    assert duplicate.status_code == 409
