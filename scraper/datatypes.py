from sqlalchemy import TypeDecorator, DateTime
from datetime import timezone


class UTCDateTime(TypeDecorator):
    """
    Results returned as timezone aware in UTC
    """

    impl = DateTime

    def process_result_value(self, value, dialect):
        return value.replace(tzinfo=timezone.utc)
