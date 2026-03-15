from app.main import create_app


def test_create_app_smoke() -> None:
    app = create_app()

    assert app is not None
    assert app.title
