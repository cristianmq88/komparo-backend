"""
Tipos de columna portables entre PostgreSQL (producción) y SQLite (local).
"""
import uuid

from sqlalchemy.types import CHAR, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


class GUID(TypeDecorator):
    """
    UUID independiente de la base de datos.

    - En PostgreSQL usa el tipo nativo UUID.
    - En el resto (SQLite, etc.) lo almacena como CHAR(36).

    Permite que los modelos de precios funcionen tanto en el Postgres de
    producción como en el SQLite que se usa para desarrollo local.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            # psycopg2 acepta UUID o str
            return str(value)
        if not isinstance(value, uuid.UUID):
            return str(uuid.UUID(str(value)))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            return uuid.UUID(str(value))
        return value
