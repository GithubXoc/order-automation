This is a order automation application prototype

## Database setup

The backend uses synchronous SQLAlchemy sessions with PostgreSQL. Alembic manages
the schema; starting FastAPI does not create or update tables.

Run these commands from the `backend` directory:

```sh
uv sync
```

Set `DATABASE_URL` and `VERIFY_TOKEN` in your environment or in a local `.env`
file (do not commit credentials). For example, using placeholder values:

```dotenv
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@localhost:5432/order_automation
VERIFY_TOKEN=your-webhook-verification-token
```

Create the PostgreSQL database and user beforehand. A `postgresql://` URL also
uses psycopg2; `postgresql+psycopg://` is supported as well. Do not use the
async-only `postgresql+asyncpg://` driver with this synchronous setup.
The SQLite `database.db` file is not used by this PostgreSQL configuration.

Both the application and Alembic read `database_url` from `core/config.py`.
The placeholder `sqlalchemy.url` in `alembic.ini` is not used. The `.env` path
is relative to the working directory, so run the following from `backend`:

```sh
uv run alembic current
uv run alembic upgrade head
uv run alembic current
uv run fastapi dev main.py
```

`upgrade head` applies pending migrations, including creation of `messages`.
For future model changes, generate a migration with
`uv run alembic revision --autogenerate -m "describe change"`, review the
generated migration, then run `uv run alembic upgrade head`.

`database/database.py` is the only engine/session setup. Routes can use
`Depends(get_db)` to get a session that is closed after the request. Writes
must explicitly commit; closing the session does not commit them.
The webhook processes customer messages across all entries and messaging events
in each payload. Echoes and non-message events are skipped.
Repeated deliveries with the same non-null `mid` are acknowledged without
inserting another row or changing the original message. Other database failures
return HTTP 500 so they are not mistaken for invalid JSON.

Run the focused database tests without connecting to PostgreSQL:

```sh
uv run python -m unittest discover -s tests
```

To also run PostgreSQL persistence tests, set `TEST_DATABASE_URL` to a PostgreSQL
test database URL with migrations applied. These tests use a temporary `messages` table on an isolated
connection; they do not change the application's message rows.
