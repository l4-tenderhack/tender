def test_swagger_docs_endpoint(client) -> None:
    response = client.get("/docs")

    assert response.status_code == 200
    assert "swagger ui" in response.text.lower()


def test_openapi_schema_endpoint(client) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    payload = response.json()

    assert payload["info"]["title"] == "TenderHack Backend"
    assert "/api/v1/auth/login" in payload["paths"]
    assert "/api/v1/parsing/jobs" in payload["paths"]
    assert "/api/v1/parsing/jobs" in payload["paths"]
