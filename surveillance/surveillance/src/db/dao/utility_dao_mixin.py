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

    def add_new_item(self, item):
        with self.regular_session() as db_session:
            db_session.add(item)
            db_session.commit()

    def find_one_or_none(self, query):
        return self.exec_and_read_one_or_none(query)

    def execute_and_return_all(self, query):
        """Executes query and returns a list of results"""
        with self.regular_session() as db_session:
            result = db_session.execute(query)
            return list(result.scalars().all())

    def update_item(self, item):
        """Merge and commit an item to the DB"""
        with self.regular_session() as db_session:
            db_session.merge(item)
            db_session.commit()

    def exec_and_read_one_or_none(self, query):
        """Helper method to make code more testable and pleasant to read"""
        with self.regular_session() as session:
            result = session.execute(query)
            return result.scalar_one_or_none()
