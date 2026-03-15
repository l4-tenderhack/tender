def test_parsing_endpoint_template(client) -> None:
    response = client.post("/api/v1/parsing/jobs", json={"source": "https://example.com"})

    assert response.status_code == 501
    assert "not implemented" in response.json()["detail"].lower()
