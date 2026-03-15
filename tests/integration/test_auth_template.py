def test_auth_login_template(client) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "demo", "password": "demo-password"},
    )

    assert response.status_code == 501
    assert "jwt authentication is not implemented" in response.json()["detail"].lower()


def test_auth_me_requires_bearer_token(client) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing bearer token"


def test_auth_me_template_with_bearer_token(client) -> None:
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer stub-token"},
    )

    assert response.status_code == 501
    assert "jwt authentication is not implemented" in response.json()["detail"].lower()
