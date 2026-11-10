# Registration and database connections

Run on 2026-11-10 20:41 UTC with `scripts/registration-leak.sh 30`.

| Moment | Backend connections to PostgreSQL |
|---|---|
| Before | 3 |
| After 30 new accounts | 32 |
| After 30 attempts with a taken e-mail | 62 |
| After a backend restart | 1 |

- Connections left open per new account: **0.97**.
- Connections left open per attempt with a taken e-mail: **1.0**.
- PostgreSQL allows **100** connections (`max_connections`).
