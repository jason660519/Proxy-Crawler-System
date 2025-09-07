from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Provide sqlalchemy.url at runtime from environment
db_user = os.getenv("DB_USER", "proxyadmin")
db_pass = os.getenv("DB_PASSWORD", "secretpassword")
db_name = os.getenv("DB_NAME", "proxypool")
db_host = os.getenv("DB_HOST", os.getenv("DB_SERVICE", "localhost"))
db_port = os.getenv("DB_PORT", "5432")
config.set_main_option(
    "sqlalchemy.url",
    f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}",
)

target_metadata = None


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, literal_binds=True, dialect_opts={"paramstyle": "named"})

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()


