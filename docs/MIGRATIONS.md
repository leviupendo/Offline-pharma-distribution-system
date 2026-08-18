# Database Migrations

Development currently creates the schema from SQLAlchemy metadata. For controlled production releases, use a versioned migration system such as Alembic.

Production rule:
- never silently modify schema on application startup;
- every schema change gets a migration ID;
- migration is tested against a backup copy;
- migration is included in release/change-control evidence;
- rollback strategy is documented before deployment.
