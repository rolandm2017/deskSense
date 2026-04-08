from sqlalchemy import inspect, text

from activitytracker.db.models import Base


def _all_table_names():
    return [table.name for table in Base.metadata.sorted_tables]


_cached_truncation_sql = None


def _truncate_existing_tables(executor, bind):
    global _cached_truncation_sql

    if _cached_truncation_sql is None:
        table_names = _all_table_names()
        if not table_names:
            return False

        inspector = inspect(bind)
        existing_table_names = set(inspector.get_table_names(schema="public"))
        truncation_targets = [
            f'public."{table_name}"'
            for table_name in table_names
            if table_name in existing_table_names
        ]
        if not truncation_targets:
            return False

        _cached_truncation_sql = f"TRUNCATE {', '.join(truncation_targets)} RESTART IDENTITY CASCADE"

    executor(text(_cached_truncation_sql))
    return True


def truncate_all_tables_via_session(regular_session_maker):
    """Truncate every mapped table in the test database."""
    with regular_session_maker() as session:
        did_truncate = _truncate_existing_tables(session.execute, session.bind)
        if did_truncate:
            session.commit()
            print("Super truncated all tables")


def truncate_all_tables_via_engine(engine):
    """Truncate every mapped table in the test database."""
    with engine.begin() as conn:
        did_truncate = _truncate_existing_tables(conn.execute, conn)
        if did_truncate:
            print("Super truncated all tables")


def truncate_summaries_and_logs_tables_via_session(regular_session_maker):
    """Truncate all test tables directly"""
    # NOTE: IF you run the tests in a broken manner,
    # ####  the first run AFTER fixing the break
    # ####  MAY still look broken.
    # ####  Because the truncation happens *at the end of* a test.

    truncate_all_tables_via_session(regular_session_maker)


def truncate_summaries_and_logs_tables_via_engine(engine):
    """Truncate all test tables directly"""
    # NOTE: IF you run the tests in a broken manner,
    # ####  the first run AFTER fixing the break
    # ####  MAY still look broken.
    # ####  Because the truncation happens *at the end of* a test.

    truncate_all_tables_via_engine(engine)


def truncate_logs_tables_via_engine(engine):
    """Truncate all test tables directly"""
    # NOTE: IF you run the tests in a broken manner,
    # ####  the first run AFTER fixing the break
    # ####  MAY still look broken.
    # ####  Because the truncation happens *at the end of* a test.

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE program_logs RESTART IDENTITY CASCADE"))
        conn.execute(text("TRUNCATE domain_logs RESTART IDENTITY CASCADE"))
        conn.execute(text("TRUNCATE system_status RESTART IDENTITY CASCADE"))
        print("Tables truncated")
