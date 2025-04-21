# utility_dao_mixin.py


class UtilityDaoMixin:
    """
    Contains generic helper methods for DAOs that use SQLAlchemy sessions.
    Assumes self.regular_session exists and returns a SQLAlchemy sessionmaker.
    """

    def execute_and_return(self, query):
        """Executes query and returns a list of results"""
        with self.regular_session() as session:  # type: ignore[attr-defined]
            result = session.execute(query)
            return list(result.scalars().all())

    def exec_and_read_one_or_none(self, query):
        """Executes query and returns exactly one or None"""
        with self.regular_session() as session:  # type: ignore[attr-defined]
            return session.execute(query).scalar_one_or_none()

    def update_item(self, item):
        """Merge and commit an item to the DB"""
        with self.regular_session() as session:  # type: ignore[attr-defined]
            session.merge(item)
            session.commit()
