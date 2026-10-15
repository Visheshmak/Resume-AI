# Database migrations

Alembic owns schema changes for production. The SQLAlchemy models in `app/models/entities.py` are the domain source of truth; create a revision after model changes and run `alembic upgrade head` during deployment.
