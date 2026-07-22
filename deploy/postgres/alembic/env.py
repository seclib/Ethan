"""Alembic environment configuration for ETHAN PostgreSQL migrations.

NOTE: This is a template file. Run `alembic init` to generate the full config.
The actual context is provided by alembic at runtime.
"""

from __future__ import annotations

import os
from logging.config import fileConfig

# This is the standard alembic env.py template - alembic injects `config` at runtime
# The real imports happen when alembic loads this file

def run_migrations_online():
    """Run migrations in online mode."""
    from sqlalchemy import engine_from_config, pool
    
    # Get database URL from environment
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://ethan:ethan_dev_pass@localhost:5432/ethan"
    )
    
    connectable = engine_from_config(
        config.get_section(config.config_ini_section) | {"sqlalchemy.url": database_url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    
    with connectable.connect() as connection:
        context = config.attributes.get("connection", connection)
        context.configure(
            connection=connection,
            target_metadata=None,
            compare_type=True,
        )
        
        with context.begin_transaction():
            context.run_migrations()


def run_migrations_offline():
    """Run migrations in offline mode."""
    from sqlalchemy import engine_from_config
    
    url = os.getenv(
        "DATABASE_URL",
        "postgresql://ethan:ethan_dev_pass@localhost:5432/ethan"
    )
    
    context = config.attributes.get("connection") or None
    context.configure(
        url=url,
        target_metadata=None,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    
    with context.begin_transaction():
        context.run_migrations()


if os.getenv("ALEMBIC_OFFLINE", "false").lower() == "true":
    run_migrations_offline()
else:
    run_migrations_online()