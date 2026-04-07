import tests.conftest as conftest_module


class _FakeConnection:
    def __init__(self, statements):
        self._statements = statements

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, statement, params=None):
        self._statements.append(str(statement))


class _FakeEngine:
    def __init__(self, statements):
        self._statements = statements

    def connect(self):
        return _FakeConnection(self._statements)

    def dispose(self):
        pass


def test_postgres_test_db_uses_database_name_from_sync_test_db_url(monkeypatch):
    statements = []

    monkeypatch.setattr(
        conftest_module,
        "SYNC_TEST_DB_URL",
        "postgresql://postgres:postgres@localhost:5432/desksense_test_db",
    )
    monkeypatch.setattr(
        conftest_module,
        "create_engine",
        lambda *args, **kwargs: _FakeEngine(statements),
    )

    fixture_gen = conftest_module.postgres_test_db.__wrapped__()

    next(fixture_gen)
    fixture_gen.close()

    assert any("desksense_test_db" in statement for statement in statements)
