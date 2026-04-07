from tests.helper import truncation


class _FakeInspector:
    def __init__(self, table_names):
        self._table_names = table_names

    def get_table_names(self, schema=None):
        assert schema == "public"
        return self._table_names


class _FakeConnection:
    def __init__(self, statements):
        self._statements = statements

    def execute(self, statement):
        self._statements.append(str(statement))


def test_truncate_all_tables_via_engine_only_targets_existing_public_tables(monkeypatch):
    statements = []
    fake_conn = _FakeConnection(statements)

    class _FakeEngineBegin:
        def __enter__(self):
            return fake_conn

        def __exit__(self, exc_type, exc, tb):
            return False

    class _FakeEngine:
        def begin(self):
            return _FakeEngineBegin()

    monkeypatch.setattr(
        truncation,
        "inspect",
        lambda bind: _FakeInspector(["program_logs", "system_status"]),
    )

    truncation.truncate_all_tables_via_engine(_FakeEngine())

    assert statements == [
        'TRUNCATE public."program_logs", public."system_status" RESTART IDENTITY CASCADE'
    ]
