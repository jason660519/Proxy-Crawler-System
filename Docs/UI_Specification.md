## UI Specification (Concise)

### Layout
- App shell: header, activity bar (left), main content, status bar
- Responsive: desktop-first with adaptive tables and panels

### Key Pages
1. Proxy Pool
   - Table: host, port, protocol, anonymity, country, score, response time, last checked
   - Filters: protocol, anonymity, country, score range, response time
   - Actions: validate, delete, export (admin requires API key)
2. Analytics
   - Charts: success rate, latency, pool distribution; trends over time
3. Tasks
   - List and status; retry/cancel (admin)
4. Settings
   - Source config, validation thresholds, UI preferences

### Components
- Reusable table, charts, filters, forms
- Theme: light/dark with CSS variables (synced to local storage)

### Accessibility & UX
- Keyboard navigation on tables and filters
- Clear error messages and empty states
- Loading skeletons for API calls

### Performance
- React.memo and code-splitting
- Virtualized lists for large datasets
- Client caching for frequent lists


