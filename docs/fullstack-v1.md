# Full-Stack V1 Runbook

## Scope

V1 connects the existing Vue 2 + Element UI flow UI to a Flask + MySQL API while keeping the current mock data fallback. If the API is offline, the page still renders with local mock data.

## Frontend

Install and start the Vue app:

```powershell
npm install
npm run dev
```

Development config is read from `.env.dev` when using `npm run dev`.
Production-mode config is read from `.env.prod` when using `npm run dev:prod` or `npm run build`.

Optional API base URL in the selected env file:

```text
VITE_API_BASE_URL=http://127.0.0.1:5000
```

## Backend

Create a Python virtual environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Configure MySQL in `.env.dev` for development, or `.env.prod` for production:

```text
APP_ENV=dev
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your-password
MYSQL_DATABASE=internal_admin_system
DEFAULT_OPERATOR_ID=1
VITE_API_BASE_URL=http://127.0.0.1:5000
```

Initialize the database with the existing schema and seed:

```powershell
mysql -u root -p < docs\schema.sql
mysql -u root -p internal_admin_system < docs\seed.sql
mysql -u root -p internal_admin_system < backend\migrations\001_fullstack_v1.sql
```

Start Flask:

```powershell
python -m backend.app
```

The backend loads configuration in this order:

```text
ENV_FILE, if set
.env.{APP_ENV}, for example .env.dev or .env.prod
.env fallback
```

Health check:

```text
GET http://127.0.0.1:5000/api/health
```

## V1 API Surface

```text
POST /api/auth/login
GET  /api/auth/me

GET  /api/flow/templates
GET  /api/flow/templates/:id
PUT  /api/flow/templates/:id

GET  /api/flow/instances
POST /api/flow/instances
GET  /api/flow/instances/:id
PUT  /api/flow/instances/:id

POST /api/flow/instances/:id/tasks/:taskId/complete
POST /api/flow/instances/:id/steps/:stepId/complete
POST /api/flow/instances/:id/remind
GET  /api/flow/instances/:id/logs
```

## Verification

```powershell
npm test
python -m compileall backend
```

`npm test` currently checks project structure and API integration points. Full browser/build verification requires `npm` dependencies to be installed.
