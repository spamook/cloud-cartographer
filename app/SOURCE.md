# Where this source comes from

The application is distributed as one archive, `sample-app.zip`. Its download server answered
HTTP 502 from 2026-11-04 to at least 2026-11-10. The files in this folder were therefore rebuilt
from copies of the same archive that other students published in their own repositories:

| Repository | Folder with the app |
|---|---|
| [corvert/cloud-cartographer](https://github.com/corvert/cloud-cartographer) | `/` |
| [DreXtrime/cloud-cartographer](https://github.com/DreXtrime/cloud-cartographer) | `sample-app-main/` |
| [emyeugdcd/cloud-cartographer](https://github.com/emyeugdcd/cloud-cartographer) | `sample-application/` |
| [Hasitha-Nilwakka/cloud-cartographer](https://github.com/Hasitha-Nilwakka/cloud-cartographer) | `sample-app-main/` |
| [jyrgenandessalu/cloud-cartographer](https://github.com/jyrgenandessalu/cloud-cartographer) | `/` |
| [mosakr970/cloud-cartographer](https://github.com/mosakr970/cloud-cartographer) | `sample-app-main/` |

## How

1. For every file, the git blob SHA of each copy was compared, using each repository's tree from
   the GitHub API.
2. The version most copies agree on was taken. After download, its content was checked against
   that SHA, so the files here are byte-identical to the majority copies. `git ls-files -s app/`
   prints the same SHAs.
3. Files that only one copy has were left out. They are that student's additions:
   - `backend/packages/api/metrics.go`;
   - the `.dockerignore` files;
   - `backend/.env.example`.

## How sure

- **37 of the 48 files** are identical in every copy that has them.
- **9 files** differ in one copy (in two copies for `nginx.conf`) and agree in the other four or
  five copies:
  - `backend/Dockerfile`;
  - `router.go`, `userController.go`, `config.go`, `db.go`, `user.go`;
  - `frontend/config/config.js`, `frontend/public/config.js`;
  - `frontend/config/nginx.conf`.
- **`docker-compose.yml`** exists in five versions. Two copies agree on the one here. The other
  three are this file with additions: a monitoring stack, other ports, container names.
- **`backend/.env`** is in only three copies, probably because the others kept it out of git.
  - Two of the three agree; the third adds one more origin to `CLIENT_URL`.
  - The backend's Dockerfile copies this file into the image, so the build needs it.
  - It holds development defaults only. In Kubernetes, environment variables from the chart
    override every value, and `JWT_KEY` comes from a Secret.

The application itself is unchanged. What Kubernetes needs is in the chart
[`deploy/charts/sample-app`](../deploy/charts/sample-app):
- non-root users;
- the API address in `config.js`;
- the health check.
