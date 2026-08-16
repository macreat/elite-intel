from importlib import import_module

from sqlalchemy import create_engine, text


migration = import_module("app.db.migrations.versions.008_protect_import_confirmation")
fingerprint_migration = import_module("app.db.migrations.versions.009_unique_import_fingerprints")
identity_migration = import_module("app.db.migrations.versions.010_source_context_import_identity")


def _create_legacy_tables(connection, *, semantic_unique=False):
    semantic_constraint = ", CONSTRAINT uq_transactions_record_fingerprint UNIQUE (record_fingerprint)" if semantic_unique else ""
    connection.execute(
        text(
            f"""
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY,
                import_batch_id INTEGER,
                source_row_number INTEGER,
                record_fingerprint TEXT,
                created_at TEXT NOT NULL
                {semantic_constraint}
            )
            """
        )
    )
    connection.execute(
        text(
            """
            CREATE TABLE import_batches (
                id INTEGER PRIMARY KEY,
                records_inserted INTEGER NOT NULL
            )
            """
        )
    )
    connection.execute(
        text(
            """
            CREATE TABLE import_rows (
                id INTEGER PRIMARY KEY,
                transaction_id INTEGER
            )
            """
        )
    )


def test_upgrade_deduplicates_historical_import_transactions_and_rewires_rows(monkeypatch):
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    with engine.begin() as connection:
        _create_legacy_tables(connection)
        connection.execute(text("INSERT INTO import_batches (id, records_inserted) VALUES (7, 1), (8, 1), (9, 1)"))
        connection.execute(
            text(
                """
                INSERT INTO transactions (id, import_batch_id, source_row_number, record_fingerprint, created_at)
                VALUES
                    (10, 7, 3, 'fingerprint-a', '2026-08-12T10:00:00'),
                    (11, 7, 3, 'fingerprint-z', '2026-08-12T09:00:00'),
                    (12, 7, 4, 'fingerprint-b', '2026-08-12T11:00:00'),
                    (20, 8, 1, 'fingerprint-c', '2026-08-12T08:00:00'),
                    (21, 9, 1, 'fingerprint-c', '2026-08-12T07:00:00'),
                    (22, 8, 2, 'fingerprint-d', '2026-08-12T05:00:00'),
                    (23, 9, 2, 'fingerprint-d', '2026-08-12T05:00:00'),
                    (30, NULL, NULL, NULL, '2026-08-12T06:00:00')
                """
            )
        )
        connection.execute(
            text(
                "INSERT INTO import_rows (id, transaction_id) VALUES "
                "(100, 10), (101, 11), (102, 12), (103, 20), (104, 21), (105, 22), (106, 23)"
            )
        )

        constraint_calls = []
        monkeypatch.setattr(migration.op, "get_bind", lambda: connection)
        monkeypatch.setattr(
            migration.op,
            "create_unique_constraint",
            lambda *args, **kwargs: constraint_calls.append((args, kwargs)),
        )

        migration.upgrade()

        transactions = connection.execute(
            text("SELECT id, import_batch_id, source_row_number FROM transactions ORDER BY id")
        ).all()
        rows = connection.execute(text("SELECT id, transaction_id FROM import_rows ORDER BY id")).all()
        counters = connection.execute(text("SELECT id, records_inserted FROM import_batches ORDER BY id")).all()

    assert transactions == [
        (11, 7, 3),
        (12, 7, 4),
        (20, 8, 1),
        (21, 9, 1),
        (22, 8, 2),
        (23, 9, 2),
        (30, None, None),
    ]
    assert rows == [
        (100, 11),
        (101, 11),
        (102, 12),
        (103, 20),
        (104, 21),
        (105, 22),
        (106, 23),
    ]
    assert counters == [(7, 1), (8, 1), (9, 1)]
    assert constraint_calls == [
        (("uq_transactions_import_batch_row", "transactions", ["import_batch_id", "source_row_number"]), {}),
    ]


def test_upgrade_cleanup_is_idempotent_for_already_clean_history(monkeypatch):
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    with engine.begin() as connection:
        _create_legacy_tables(connection)
        connection.execute(
            text(
                "INSERT INTO transactions "
                "(id, import_batch_id, source_row_number, record_fingerprint, created_at) "
                "VALUES (10, 7, 3, 'fingerprint-a', '2026-08-12T09:00:00')"
            )
        )

        monkeypatch.setattr(migration.op, "get_bind", lambda: connection)
        monkeypatch.setattr(migration.op, "create_unique_constraint", lambda *args, **kwargs: None)

        migration.upgrade()
        migration._deduplicate_import_transactions(connection)

        transactions = connection.execute(text("SELECT id FROM transactions")).all()

    assert transactions == [(10,)]


def test_revision_009_does_not_deduplicate_semantic_fingerprints(monkeypatch):
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    with engine.begin() as connection:
        _create_legacy_tables(connection)
        connection.execute(
            text(
                "INSERT INTO transactions "
                "(id, import_batch_id, source_row_number, record_fingerprint, created_at) "
                "VALUES (10, 7, 1, 'same-semantic-row', '2026-08-12T09:00:00'), "
                "(20, 8, 1, 'same-semantic-row', '2026-08-12T10:00:00')"
            )
        )

        constraint_calls = []
        monkeypatch.setattr(fingerprint_migration.op, "get_bind", lambda: connection)
        monkeypatch.setattr(
            fingerprint_migration.op,
            "create_unique_constraint",
            lambda *args, **kwargs: constraint_calls.append((args, kwargs)),
        )

        fingerprint_migration.upgrade()

        transactions = connection.execute(
            text("SELECT id, record_fingerprint FROM transactions ORDER BY id")
        ).all()

    assert transactions == [(10, "same-semantic-row"), (20, "same-semantic-row")]
    assert constraint_calls == []


def test_fresh_upgrade_preserves_repeated_semantics_until_source_identity(monkeypatch):
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    with engine.begin() as connection:
        _create_legacy_tables(connection)
        connection.execute(
            text(
                "INSERT INTO transactions "
                "(id, import_batch_id, source_row_number, record_fingerprint, created_at) "
                "VALUES (10, 7, 1, 'same-semantic-row', '2026-08-12T09:00:00'), "
                "(20, 8, 1, 'same-semantic-row', '2026-08-12T10:00:00')"
            )
        )

        monkeypatch.setattr(migration.op, "get_bind", lambda: connection)
        monkeypatch.setattr(migration.op, "create_unique_constraint", lambda *args, **kwargs: None)
        migration.upgrade()

        monkeypatch.setattr(fingerprint_migration.op, "get_bind", lambda: connection)
        fingerprint_migration.upgrade()

        monkeypatch.setattr(identity_migration.op, "get_bind", lambda: connection)
        monkeypatch.setattr(
            identity_migration.op,
            "add_column",
            lambda table_name, column: connection.execute(
                text("ALTER TABLE transactions ADD COLUMN source_fingerprint TEXT")
            ),
        )
        monkeypatch.setattr(identity_migration.op, "drop_constraint", lambda *args, **kwargs: None)
        monkeypatch.setattr(identity_migration.op, "create_unique_constraint", lambda *args, **kwargs: None)
        identity_migration.upgrade()

        transactions = connection.execute(
            text(
                "SELECT id, import_batch_id, source_row_number, source_fingerprint "
                "FROM transactions ORDER BY id"
            )
        ).all()

    assert [row[:3] for row in transactions] == [(10, 7, 1), (20, 8, 1)]
    assert transactions[0][3] != transactions[1][3]


def test_existing_revision_009_constraint_is_removed_without_semantic_cleanup(monkeypatch):
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    with engine.begin() as connection:
        _create_legacy_tables(connection, semantic_unique=True)
        connection.execute(
            text(
                "INSERT INTO transactions "
                "(id, import_batch_id, source_row_number, record_fingerprint, created_at) "
                "VALUES (10, 7, 1, 'existing-row', '2026-08-12T09:00:00')"
            )
        )

        dropped_constraints = []
        monkeypatch.setattr(identity_migration.op, "get_bind", lambda: connection)
        monkeypatch.setattr(
            identity_migration.op,
            "drop_constraint",
            lambda *args, **kwargs: dropped_constraints.append((args, kwargs)),
        )
        monkeypatch.setattr(
            identity_migration.op,
            "add_column",
            lambda table_name, column: connection.execute(
                text("ALTER TABLE transactions ADD COLUMN source_fingerprint TEXT")
            ),
        )
        monkeypatch.setattr(identity_migration.op, "create_unique_constraint", lambda *args, **kwargs: None)

        identity_migration.upgrade()

    assert dropped_constraints == [
        (("uq_transactions_record_fingerprint", "transactions"), {"type_": "unique"})
    ]
