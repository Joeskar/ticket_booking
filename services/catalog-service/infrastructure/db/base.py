import re
from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    """Базовый класс для всех моделей SQLAlchemy в новом версий."""
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls):
        return f"{cls.camel_to_snake(cls.__name__)}s"

    @staticmethod
    def camel_to_snake(name: str) -> str:
        s1 = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name)
        s2 = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', s1)
        return s2.lower()
