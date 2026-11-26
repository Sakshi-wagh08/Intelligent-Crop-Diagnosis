from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.compiler import compiles
from geoalchemy2 import Geometry

Base = declarative_base()


# SQLite compatibility compiler for testing environments without SpatiaLite.
# Under PostgreSQL/PostGIS, the native PostGIS geometry(type, srid) compiler is preserved.
@compiles(Geometry, "sqlite")
def compile_geometry_sqlite(type_, compiler, **kw):
    """Compiles PostGIS Geometry column to BLOB on SQLite for test compatibility."""
    return "BLOB"
