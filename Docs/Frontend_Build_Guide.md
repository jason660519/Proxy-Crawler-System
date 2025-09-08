## Frontend Build Guide (Proxy Manager UI)

### Stack
- React + TypeScript + Vite
- styled-components, React Router
- Axios client with `VITE_API_BASE_URL`, `VITE_ETL_BASE_URL`, optional `VITE_API_KEY`

### Environment
Create `frontend/.env.local`:

```
VITE_API_BASE_URL=http://localhost:8000
VITE_ETL_BASE_URL=http://localhost:8001
VITE_REQUEST_TIMEOUT=15000
# Optional when backend API key is enabled
VITE_API_KEY=
```

### Commands
```
npm run dev      # dev server
npm run build    # production build
npm run preview  # preview build
npm run lint     # lint
```

### Structure (simplified)
```
src/
  components/  pages/  hooks/  stores/  services/  types/  styles/
```

### API Client Notes
- `http.ts` injects `X-API-Key` header automatically if `VITE_API_KEY` is set.
- Errors are normalized with meaningful messages for UI surfacing.

### Deployment
- Static hosting (e.g., Nginx) or containerized; ensure `VITE_*` is baked at build time.
- CORS must include the frontend origin if backend restricts origins.


