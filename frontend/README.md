# Frontend

This directory now contains the real Vite + React + TypeScript frontend shell for DLE-SaaS.

## Structure

- `index.html`
  - Vite HTML entrypoint
- `src/main.tsx`
  - browser bootstrap
- `src/app/`
  - router, providers, layout, and shared app wiring
- `src/shared/`
  - owned utilities and shadcn-style UI primitives
- `src/features/`
  - feature-owned screens and components

## Baseline Libraries

- React Router 7
- TanStack Query v5
- React Hook Form 7
- Zod 4
- Tailwind CSS 4 via `@tailwindcss/vite`
- shadcn/ui-style ownership under `src/shared/ui/`

## Commands

```bash
npm --prefix frontend run dev
npm --prefix frontend run build
npm --prefix frontend run test
```
