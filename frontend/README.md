# Dalla Frontend

React SPA for the Dalla finance app. Uses the FastAPI backend and Cognito for auth.

## Setup

1. **Install dependencies**

   ```bash
   npm install
   ```

2. **Configure environment**

   Copy `.env.example` to `.env` and set values (use the same Cognito User Pool and App Client as the backend):

   ```bash
   cp .env.example .env
   ```

   - `VITE_API_URL` — API base URL. Use `/api` in development (Vite proxies to the backend).
   - `VITE_COGNITO_USER_POOL_ID` — Cognito User Pool ID
   - `VITE_COGNITO_APP_CLIENT_ID` — Cognito App Client ID
   - `VITE_COGNITO_REGION` — e.g. `us-east-1`

   Without these Cognito variables, the app shows “Auth not configured” and will not render the sign-in UI.

## Run

1. **Start the backend** (from repo root or `backend/`):

   ```bash
   cd backend && uvicorn app.main:app --reload
   ```

   Default: `http://localhost:8000`

2. **Start the frontend**:

   ```bash
   npm run dev
   ```

   Vite serves the app (e.g. `http://localhost:5173`) and proxies `/api` to the backend, so `VITE_API_URL=/api` works.

3. Open the app in the browser. Sign in with Cognito; the app will call `PUT /users/me` to register or update your user.

## Scripts

- `npm run dev` — Start dev server with hot reload
- `npm run build` — Production build (output in `dist/`)
- `npm run preview` — Serve the production build locally
