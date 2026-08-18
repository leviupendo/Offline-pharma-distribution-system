# Changelog

## v0.3.5
- **Fixed: `pip install -r requirements.txt` failed entirely on newer
  Python versions (confirmed on Windows + Python 3.14) because of an
  exact pin on `psycopg[binary]==3.2.9`.** psycopg only ships prebuilt
  wheels for a given Python version as of a certain release — 3.2.9
  has no wheel for Python 3.14, only 3.2.10+. An exact pin doesn't
  degrade gracefully in that situation; pip aborts the *entire*
  install, so `sqlalchemy` and every other dependency never got
  installed either, even though they were otherwise fine. Changed to
  `psycopg[binary]>=3.2.9` (a floor, not an exact pin) so pip can pick
  a version with an available wheel. Verified this still resolves and
  installs cleanly, and the full test suite still passes against
  SQLite (which doesn't use psycopg at all — it's only needed for the
  optional Postgres/Docker path).

## v0.3.4
- **Fixed: the login endpoint crashed with a 500 on the very next
  attempt after an account got locked out.** Same root cause as the
  v0.3.2 audit-chain bug: SQLite drops the tz offset on
  `DateTime(timezone=True)` columns across a round trip, so a
  `locked_until` value written as timezone-aware UTC came back naive
  on the next request, and comparing it against
  `datetime.now(timezone.utc)` raised `TypeError: can't compare
  offset-naive and offset-aware datetimes` instead of returning a
  clean 423. In other words: the account-lockout feature worked for
  exactly one request per lockout before breaking the whole login
  endpoint for that user. Fixed with the same UTC-normalization
  approach as the audit chain fix; verified the full cycle (lock after
  5 failures → blocked with 423, not a crash → unlocks cleanly after
  expiry). Added a regression test.
- Reviewed `app/api/users.py` (create/disable/list) and confirmed it's
  correct as written: disabling a user immediately revokes access even
  with a still-valid, unexpired JWT (every request re-checks
  `is_active` from the database), an admin can't disable their own
  account, and role/permission checks on all three endpoints hold up
  under test.

## v0.3.3
- **Fixed: every single write endpoint in the API silently returned an
  empty `{}` body on success.** `POST`/create endpoints did `db.commit();
  return obj` where `obj` is a SQLAlchemy model instance. SQLAlchemy's
  default `expire_on_commit=True` expires all attributes right after
  commit; FastAPI then serializes the returned object via
  `jsonable_encoder`'s `vars(obj)` fallback, which reflects whatever is
  currently in `__dict__` rather than triggering a lazy reload — so it
  found nothing and returned `{}`. The write itself succeeded (a
  follow-up `GET` showed correct data), but the response gave the
  caller no way to learn the new resource's `id`, meaning a client
  couldn't actually chain a create call into the next request without
  a separate list-and-search round trip. This affected every create/
  update endpoint: products, customers, batches, QC decisions,
  packaging, inventory adjustments, orders, order status transitions,
  proof of delivery, and recalls. Fixed by setting
  `expire_on_commit=False` on the session factory in
  `app/core/database.py`.
- **Fixed a related staleness bug this uncovered in order allocation.**
  `POST /api/orders/{id}/allocate` created `OrderAllocation` rows via
  `db.add(OrderAllocation(order_line_id=line.id, ...))` rather than
  `line.allocations.append(...)`, so the already-loaded `allocations`
  collection on each order line never picked up the new rows in
  memory. Once the `{}`-body bug above was fixed, this became visible
  as the allocate response showing an empty `allocations` list even
  though allocation had genuinely succeeded. Fixed by expiring and
  re-touching the collection before returning.
- Added `tests/test_write_endpoint_responses.py` covering both of the
  above so this class of bug can't silently regress.
- **Fixed `docker-compose.yml` setting `SECRET_KEY`**, a variable the
  application has never actually read (it's always used `JWT_SECRET`).
  This was a pre-existing, silent misconfiguration — the container
  would start, but with the app's real secret still at its insecure
  default regardless of what `SECRET_KEY` was set to. Corrected to
  set `JWT_SECRET`, and added a comment pointing at the
  `validate_production_secrets()` startup guard.
- Updated `docs/DEPLOYMENT.md`'s production checklist to explicitly
  call out setting `APP_ENV=production` and generating real
  `JWT_SECRET`/`BACKUP_KEY` values, tying it to the startup guard
  added in v0.3.1.
- Verified (not just read) the specific claims listed in
  `docs/SECURITY_TEST_PLAN.md` — RBAC denial cases for every role,
  negative-stock rejection, batch-status gating on packaging, and
  audit tamper detection — by actually running them. All held up
  after the fixes above.

## v0.3.2
Second pass, going deeper than the config/wiring layer into the actual
domain logic — same "run it and check the output, don't just read it"
approach as v0.3.1.

- **Fixed: the audit hash-chain verification reported every legitimate,
  untampered log as INVALID on the default SQLite backend.**
  `append_audit` hashed `timestamp.isoformat()` on a fresh, tz-aware
  datetime (`...+00:00`), but SQLite silently drops the tz offset on
  round trip, so `verify_audit_chain` recomputed the hash from a naive
  timestamp (no offset) and got a different string every time. This
  is the actual compliance-critical feature the system is built
  around, and it was reporting tamper-evidence failures on data that
  was never touched. Both functions now normalize through a shared
  `_canonical_timestamp()` so the hash is backend-independent (verified
  correct behavior on both a clean chain and a deliberately tampered
  one). Added `tests/test_audit_chain.py` to prevent regression.
- **Fixed: the recall workflow crashed on every call.**
  `POST /api/recalls` set `batch.status = "RECALLED"`, but `BatchStatus`
  never defined a `RECALLED` value, so SQLAlchemy raised a `LookupError`
  on every recall attempt. Added `RECALLED` to the enum and added
  guards against recalling an already-recalled or never-released
  (rejected) batch.
- **Fixed: the recall impact report also crashed, on a different bug**,
  and — even when it didn't crash — always returned an empty `orders`
  list, which defeats the purpose of a recall report. It queried
  `Inventory.batch_id`, a column that does not exist on that model
  (`Inventory` only relates to a batch indirectly through
  `packet_production`). Rewrote it to join through `PacketProduction`
  for on-hand stock, and to actually trace
  `Order -> OrderLine -> OrderAllocation -> PacketProduction -> Batch`
  so the report shows exactly which orders (and quantities) received
  stock from the affected batch. Added regression tests covering the
  crash, the impact-report contents, and double-recall rejection.
- **Fixed: `GET /api/change-control` was a dead stub.** It contained
  unreachable code (`db.query(...) if False else []`) and always
  returned a static note instead of the change requests that had
  actually been created. It now reads them back from the audit log
  (where they're genuinely recorded) and returns them as a real list.

## v0.3.1
- **Fixed: authentication was completely non-functional.** `app/core/config.py`
  defined settings under different names than `app/api/auth.py` and
  `app/core/security.py` referenced (e.g. `access_token_minutes` vs.
  `settings.ACCESS_TOKEN_MINUTES`), so every login attempt and every
  protected-route request raised an unhandled `AttributeError`. Config
  field names now match every call site; verified end-to-end with a real
  login → token → protected-route round trip.
- **Fixed: `requirements.txt` didn't match the code's imports.** The app
  imports `jose` and `passlib`, but the file listed `PyJWT` and no
  `passlib`, so a clean `pip install -r requirements.txt` left the app
  unable to start. Corrected to `python-jose[cryptography]` and
  `passlib[argon2]`.
- **Fixed: `APP_ENV` in `.env.example` was silently ignored.** The
  `environment` setting only read `ENVIRONMENT`, not `APP_ENV`, so
  setting `APP_ENV=production` had no effect. Now aliased correctly.
- **Added: refusal to start with placeholder secrets outside development.**
  If `environment` is not `development` and `JWT_SECRET` or `BACKUP_KEY`
  are still at their placeholder values, the app now raises at startup
  instead of silently running with a guessable secret.
- **Fixed: `python scripts/seed.py` and `python scripts/verify_audit.py`
  failed with `ModuleNotFoundError: No module named 'app'`** when run
  from the repo root as the README instructs, because nothing put the
  repo root on `sys.path`. Both scripts now do this themselves.
- **Fixed: backups were never actually encrypted** despite
  `docs/BACKUP_RESTORE.md` saying so, and the `backup_key` setting was
  unused dead code. `scripts/backup.py` now encrypts with a key derived
  from `BACKUP_KEY` (via PBKDF2 + Fernet) when it's set, and falls back
  to an unencrypted backup with a visible warning when it isn't. Added
  `scripts/restore.py` to actually decrypt and restore what
  `backup.py` produces, since no restore tooling existed before.
- **Added: `tests/test_auth.py`**, which exercises `/api/auth/login` and
  a protected route through the real HTTP stack. The previous test
  suite only unit-tested `hash_password`/`verify_password` in isolation
  and never called the login endpoint, which is why the config bug
  above shipped with a fully green CI run.
- **Fixed: duplicate CI workflow files** (`test.yml` and `tests.yml`)
  that ran the identical job twice under different Python versions;
  merged into a single matrixed `test.yml`.
- Removed a committed `pharma.db` and stale `__pycache__`/`.pytest_cache`
  directories from the archive.

## v0.3.0
- Added product management API.
- Added customer management API.
- Added audit viewing and audit-chain verification.
- Added stronger authentication and lockout handling.
- Added production deployment guidance.
- Added device integration plan.
- Added security test plan.
- Added backup verification tooling.
- Expanded validation and operational documentation.

## v0.2.0
- Added batch, QC, packaging, inventory, FEFO and order workflows.
- Added dashboard and local UI.
- Added role-based access control.
- Added Docker foundation.
