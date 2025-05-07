# utility_dao_mixin.py

# pyright: reportAttributeAccessIssue=false


class UtilityDaoMixin:
    """
    Contains generic helper methods for DAOs that use SQLAlchemy sessions.
    Assumes self.regular_session exists and returns a SQLAlchemy sessionmaker.

    Class exists (a) to prevent WET spam of sqlalchemy library code
    and (b) to enhance testability by giving an easy place to
    substitute a mock/spy before we get into db queries.

    Remember order: Create, Read, Update, Delete
    """

    # Code	                        Returns
    # .execute().all()	            Full rows (tuples, etc.)
    # .execute().scalars().all()	Just the first column (or model object)

    def add_new_item(self, item):
        # The default behavior for PostgreSQL sequences (which typically
        # back ID columns) is to always choose the next sequential value,
        # regardless of gaps in the sequence
        with self.regular_session() as db_session:
            db_session.add(item)
            db_session.commit()
            # After commit, the item's ID will be populated
            # You don't have to use the ID, but it's there if you want it
            return item.id

    def execute_and_return_all(self, query):
        """
        Executes query and returns a list of results
        """
        # Be aware that this version is very confusable with execute(query).scalars().all()
        with self.regular_session() as db_session:
            result = db_session.execute(query)
            return list(result.scalars().all())

    def update_item(self, item):
        """Merge and commit an item to the DB"""
        with self.regular_session() as db_session:
            db_session.merge(item)
            db_session.commit()

    def execute_and_read_one_or_none(self, query):
        """Helper method to make code more testable and pleasant to read"""
        with self.regular_session() as session:
            result = session.execute(query)
            return result.scalar_one_or_none()


class AsyncUtilityDaoMixin:
    """
    Contains generic helper methods for DAOs that use SQLAlchemy sessions.
    Assumes self.regular_session exists and returns a SQLAlchemy sessionmaker.

    Class exists (a) to prevent WET spam of sqlalchemy library code
    and (b) to enhance testability by giving an easy place to
    substitute a mock/spy before we get into db queries.

    Remember order: Create, Read, Update, Delete
    """

    # Code	                        Returns
    # .execute().all()	            Full rows (tuples, etc.)
    # .execute().scalars().all()	Just the first column (or model object)

    async def add_new_item(self, item):
        with self.async_session_maker() as db_session:
            db_session.add(item)
            db_session.commit()

    async def execute_and_return_all_with_scalars(self, query):
        """
        Executes query and returns a list of results.

        """
        # Be aware that this version is very confusable with execute(query).all() down below
        with self.async_session_maker() as db_session:
            result = db_session.execute(query)
            return list(result.scalars().all())

    async def execute_and_return_all_rows(self, query):
        """
        Returns a list of Row objects. Each Row contains all columns selected in your query

        If your query selects multiple columns, you get tuples/rows with all those columns

        Useful when you need all columns from a complex query
        """
        # Be aware that this version is very confusable with execute(query).scalars().all()
        async with self.async_session_maker() as session:
            result = await session.execute(query)
            result = result.all()
            return result

    async def update_item(self, item):
        """Merge and commit an item to the DB"""
        with self.async_session_maker() as db_session:
            db_session.merge(item)
            db_session.commit()

    async def execute_and_read_one_or_none(self, query):
        """Helper method to make code more testable and pleasant to read"""
        with self.async_session_maker() as session:
            result = session.execute(query)
            return result.scalar_one_or_none()
