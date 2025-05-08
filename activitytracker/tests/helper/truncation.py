from sqlalchemy import func, select, text


def truncate_summaries_and_logs_tables_via_session(regular_session_maker):
    """Truncate all test tables directly"""
    # NOTE: IF you run the tests in a broken manner,
    # ####  the first run AFTER fixing the break
    # ####  MAY still look broken.
    # ####  Because the truncation happens *at the end of* a test.

    with regular_session_maker() as session:
        session.execute(text("TRUNCATE daily_program_summaries RESTART IDENTITY CASCADE"))
        session.execute(text("TRUNCATE daily_chrome_summaries RESTART IDENTITY CASCADE"))
        session.execute(text("TRUNCATE program_logs RESTART IDENTITY CASCADE"))
        session.execute(text("TRUNCATE domain_logs RESTART IDENTITY CASCADE"))
        session.execute(text("TRUNCATE system_status RESTART IDENTITY CASCADE"))
        session.commit()
        print("Super truncated tables")


def truncate_summaries_and_logs_tables_via_engine(engine):
    """Truncate all test tables directly"""
    # NOTE: IF you run the tests in a broken manner,
    # ####  the first run AFTER fixing the break
    # ####  MAY still look broken.
    # ####  Because the truncation happens *at the end of* a test.

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE daily_program_summaries RESTART IDENTITY CASCADE"))
        conn.execute(text("TRUNCATE daily_chrome_summaries RESTART IDENTITY CASCADE"))
        conn.execute(text("TRUNCATE program_logs RESTART IDENTITY CASCADE"))
        conn.execute(text("TRUNCATE domain_logs RESTART IDENTITY CASCADE"))
        conn.execute(text("TRUNCATE system_status RESTART IDENTITY CASCADE"))
        conn.commit()
        print("Super truncated tables")


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
