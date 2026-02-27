# Presales Estimation Dashboard

Modern Next.js 15+ frontend for the GeekyAnts presales estimation engine.

## Tech Stack

- Next.js 15+ (App Router)
- TypeScript
- TailwindCSS
- React 19

## Setup

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Environment

Create `.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Structure

```
app/
├── layout.tsx       # Root layout
├── page.tsx         # Home page with form and results
└── globals.css      # Global styles

components/
├── EstimationForm.tsx    # Project input form
└── EstimationResults.tsx # Results display
```

## Usage

1. Start backend: `uvicorn app.main:app --reload` (from root)
2. Start frontend: `npm run dev` (from frontend/)
3. Open http://localhost:3000
4. Enter additional details and select what to build (mobile, web, design, backend, admin)
5. View estimation results
