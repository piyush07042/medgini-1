from sqlalchemy import create_engine, text

from app.db import session


def test_create_database_initializes_tables(monkeypatch):
    calls = {}

    class DummyEngine:
        url = "sqlite:///dummy.db"

    def fake_create_all(bind=None):
        calls["bind"] = bind

    monkeypatch.setattr(session, "engine", DummyEngine())
    monkeypatch.setattr(session.Base.metadata, "create_all", fake_create_all)

    session.create_database()

    assert calls["bind"] is session.engine


def test_create_database_adds_missing_patient_avatar_column(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")

    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE patients ("
                "id INTEGER PRIMARY KEY, "
                "doctor_id INTEGER NOT NULL, "
                "first_name VARCHAR NOT NULL, "
                "last_name VARCHAR NOT NULL, "
                "age INTEGER NOT NULL, "
                "gender VARCHAR NOT NULL, "
                "medical_history JSON, "
                "allergies JSON, "
                "current_medications JSON, "
                "created_at DATETIME"
                ")"
            )
        )

    monkeypatch.setattr(session, "engine", engine)

    session.create_database()

    with engine.connect() as connection:
        columns = [row[1] for row in connection.execute(text("PRAGMA table_info(patients)"))]

    assert "avatar_url" in columns
