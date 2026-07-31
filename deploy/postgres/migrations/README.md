# ETHAN PostgreSQL migrations

The Compose deployment initializes a new volume with
`deploy/postgres/init.sql`. Existing volumes are upgraded with the numbered
SQL files in this directory, in order, using `psql -v ON_ERROR_STOP=1`.

The Alembic directory is retained for compatibility with an upcoming
SQLAlchemy migration workflow, but it currently contains no revision files and
is not invoked by Docker. Do not mark a schema as migrated until the SQL file
has completed successfully.
