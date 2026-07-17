# TESTIMONIAL

## Overall Approach

I treated this assessment in three phases matching the assignment structure: get the project running end-to-end (Stage 1), pass system verification (Stage 2), then implement the two required features (Stage 3). Rather than guessing at fixes, I worked methodically — reading error messages and tracebacks carefully, verifying file paths and directory structures before editing anything, and testing each fix in isolation (via Swagger UI and direct `psql`/Python checks) before moving to the next step, so I always knew exactly which layer of the stack a problem lived in.

## How I Understood the Project

I started by reading the assignment brief and the project `README.md` in full before touching any code, to understand the intended setup flow and which parts were explicitly said to be complete versus intentionally incomplete. Before implementing the route logic, I read `database_setup/sqlite_ddl_description.md` closely, since it explained the graph model (stations as per-line nodes, `connections` for train edges, `interchanges` for walking-transfer edges) that the routing algorithm needed to operate on. I also reviewed the existing frontend components (`RouteSelector.jsx`, `SystemStatus.jsx`, `Dashboard.jsx`) before writing any backend response logic, since the frontend was already built and expected a specific response shape — I needed to match that contract rather than design my own.

## Bugs Encountered & How I Resolved Them

**Backend dependency & environment issues**
- `requirements.txt` was missing `sqlalchemy`, despite it being imported directly in `routes.py`. Added it to `requirements.txt` and reinstalled.
- `sqlite_client.py` computed `DB_PATH` incorrectly: `Path(__file__).resolve() / "metadatagraph.db"` treated a file as a directory and had a typo in the filename (missing underscore). Fixed to `Path(__file__).resolve().parent / "metadata_graph.db"`.
- `backend/.env` (and `.env.example`) had a malformed `DATABASE_URL`: `localhost5432` instead of `localhost:5432`. Fixed the missing colon in both files.
- Later, after switching to a local PostgreSQL instance, `.env` briefly contained a duplicated `DATABASE_URL=DATABASE_URL=...` prefix from an editor save error, which broke SQLAlchemy's URL parser — caught via `sqlalchemy.exc.ArgumentError` and fixed by rewriting the file cleanly.

**Two stubbed backend functions**
- `get_all_stations()` in `routes.py` was a bare `pass`, despite the assignment stating this endpoint was "already implemented." Implemented it as a straightforward SQLite `SELECT` returning all stations.
- `get_metro_route()` in `graph_engine.py` was also a `pass` stub. Implemented Dijkstra's algorithm over a graph built from the `stations`, `connections`, and `interchanges` tables, starting from all station-ID nodes matching the source name (to correctly handle interchange stations that exist once per line) and terminating at the closest matching destination node.

**Frontend dependency & configuration issues**
- `Dashboard.jsx` imports `lucide-react`, which wasn't listed in `frontend/package.json`. Installed it directly.
- CORS in `backend/app/main.py` only allowed `http://localhost:3000`, but Vite serves the frontend on port `5173`. Added `5173` to `allow_origins`.
- The most impactful bug: `frontend/src/services/api.js` had a fallback `baseURL` of `http://localhost:8080/api`, but the backend runs on port `8000`, and no `frontend/.env` existed to override it via `VITE_API_URL`. This silently broke every frontend API call (stations list, system status, tickets) even though every backend endpoint worked correctly when tested directly. Created `frontend/.env` with the correct URL, and added a `frontend/.env.example` (which hadn't existed before) so this can't silently recur for future setups.

**API contract mismatch**
- Once the frontend could reach the backend, `/api/route`'s response shape (`total_fare_inr`, flat `route` array) didn't match what `RouteSelector.jsx` already expected (`route_summary.*`, `ordered_itinerary` with `is_interchange`/`transfer_to` fields). Since the assignment states not to modify the API contract and the frontend was pre-built and not to be redesigned, I updated the backend's response shape to match the frontend's existing expectation — same underlying Dijkstra computation, restructured output.

**Local environment conflicts (not code bugs, but real blockers)**
- Docker Desktop's engine wasn't running initially, causing pipe-connection errors from the `docker` CLI; resolved by fully restarting Docker Desktop.
- After getting a Postgres container running in Docker, the backend still failed Postgres authentication. Diagnosis revealed a pre-existing native PostgreSQL 17 Windows service was also bound to port 5432, intercepting the connection before it reached the Docker container. Rather than fight the port conflict, I switched entirely to using the already-installed native PostgreSQL instance, which better matches the README's own instruction to use "a local PostgreSQL database server" anyway.
- `postgres_client.py` defines SQLAlchemy models but never calls `Base.metadata.create_all()`, and no migration/seed script existed outside of `database_setup/postgres_init.sql` (which the README references but I initially missed on a filename-pattern search). Running that script directly against Postgres created the schema and seeded the `system_config` key needed for verification.

## Challenges Faced

The most time-consuming challenge was diagnosing the verification flow (Stage 2), since it depended on three separate systems being correct simultaneously — PostgreSQL schema/seed data, an SQLite `vault_keys` row, and a live background heartbeat thread — and a failure in any one produced the same generic "Verification Offline" UI state, requiring me to check each dependency individually via direct database queries and isolated Python scripts rather than relying on the UI alone. The Windows-specific tooling (PowerShell syntax differences from bash, Docker Desktop/WSL2 quirks, a pre-existing native Postgres service conflicting with Docker) added friction that wasn't really about the application code itself but was necessary to work through methodically.

## Assumptions Made

- Where the assignment said certain backend functionality was "already implemented" but I found stub code, I treated this as an intentional or accidental gap to fix rather than a sign I was looking in the wrong place, since the docstrings and function signatures matched the expected behavior exactly.
- I assumed the frontend's existing API response expectations (in `RouteSelector.jsx`) represented the authoritative "existing API contract" referenced in the assignment instructions, since the frontend components were fully built and not flagged as incomplete, whereas the backend route logic was explicitly flagged as unfinished.
- I left the unused `users` table/model in place, assuming it was scaffolding for a feature outside this assessment's scope, in line with the instruction to preserve the existing database schema.

## Improvements With More Time

- Add automated tests (pytest for the Dijkstra route logic against known station pairs; React component tests for the route planner and station dropdowns).
- Add a proper Alembic migration setup for PostgreSQL instead of a manual `.sql` script, so schema changes are versioned.
- Call `Base.metadata.create_all()` (or equivalent migration step) automatically on backend startup in development, to reduce first-run setup friction.
- Extract the graph-building logic in `graph_engine.py` into a cached/reusable structure rather than querying and rebuilding the full graph on every `/api/route` request, for better performance at scale.
- Remove or properly wire up the unused `users` table if authentication is genuinely planned, rather than leaving dead schema in place.
- Add end-to-end setup validation (a single script or `make` target that checks Postgres connectivity, required tables, and SQLite file presence) to catch the kind of environment issues encountered during this assessment automatically, rather than through manual debugging.
