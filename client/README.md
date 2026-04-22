# BRA Tool — Client

React 18 + TypeScript + Vite + **Tailwind CSS** + **shadcn/ui**.

## 🏁 Run

```bash
npm install
cp .env.example .env
npm run dev        # http://localhost:5173
```

`/api/*` and `/ws/*` are proxied to the FastAPI server on `:8000` —
see [vite.config.ts](vite.config.ts).

## 📂 `src/` layout

```
src/
├── api/          HTTP + WS wrappers (one file per backend resource)
├── components/   Reusable presentational components + shadcn/ui (in `components/ui/`)
├── pages/        Route-level pages — one per pipeline stage
├── store/        Zustand stores (global app state)
├── hooks/        Custom React hooks
├── lib/          `utils.ts` — the `cn()` helper for Tailwind class merging
├── types/        TS types mirroring backend Pydantic schemas
└── utils/        Misc formatters / validators
```

See [src/README.md](src/README.md) for a per-file breakdown.

## 🎨 Tailwind + shadcn/ui

Tailwind is preconfigured ([tailwind.config.ts](tailwind.config.ts)) with the
shadcn design tokens. The shadcn CLI is pre-wired via
[components.json](components.json).

Add a component:

```bash
npx shadcn@latest add button
npx shadcn@latest add card input textarea dialog
```

Generated files land in `src/components/ui/`. Import with:

```tsx
import { Button } from "@/components/ui/button";
```

The `@` path alias is configured in both `tsconfig.json` and `vite.config.ts`.
