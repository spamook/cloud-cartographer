# Sample application

The application under analysis: a React frontend, a Go backend and PostgreSQL. It is distributed
as a single `sample-app.zip`.

The server it is downloaded from answered HTTP 502 from 2026-11-04 until this was written, so the
source is not in this folder yet. Once it is here, the next steps are:

1. container images: the app's own Dockerfiles, or multi-stage Dockerfiles added here;
2. a Helm chart for frontend and backend in `deploy/charts/`, using the PostgreSQL that
   `scripts/setup.sh` already runs;
3. a Locust scenario for its API and the load test described in
   [the infrastructure analysis](../docs/1-infrastructure-analysis.md#application-under-load).
