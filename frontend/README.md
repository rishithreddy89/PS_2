# LexMind AI - Frontend

Enterprise React dashboard for the Agentic Decision Intelligence Platform.

## Tech Stack

- React 19
- TypeScript
- Vite
- TailwindCSS
- shadcn/ui
- React Query
- Zustand
- React Router
- Recharts
- Lucide Icons

## Getting Started

### Install Dependencies

```bash
npm install
```

### Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
src/
├── components/       # Reusable UI components
│   ├── ui/          # Base UI components (Button, Card, etc.)
│   ├── Sidebar.tsx
│   ├── Navbar.tsx
│   ├── RecommendationCard.tsx
│   ├── PlannerVisualization.tsx
│   └── MemoryTimeline.tsx
├── pages/           # Page components
│   ├── Dashboard.tsx
│   ├── Cases.tsx
│   ├── CaseDetail.tsx
│   ├── Planner.tsx
│   ├── Memory.tsx
│   └── Settings.tsx
├── hooks/           # Custom React hooks
│   └── useApi.ts
├── services/        # API service layer
│   └── api.ts
├── store/           # Zustand state management
│   └── index.ts
├── types/           # TypeScript types
│   └── index.ts
├── lib/             # Utility functions
│   ├── api.ts
│   └── utils.ts
├── App.tsx          # Main app component
└── main.tsx         # Entry point
```

## Features

### Dashboard
- Active cases overview
- Pending recommendations
- Approved actions stats
- Recent cases
- Top recommendations
- Memory timeline

### Cases
- List all cases
- Search and filter
- Case details view
- Recommendations per case

### Planner
- Agent registry
- Agent capabilities
- Execution statistics

### Memory
- Timeline view
- Filter by type
- Memory statistics

### Settings
- User profile
- Preferences
- API configuration

## API Integration

The frontend connects to the backend API at `http://localhost:8000/api/v1`.

All API calls are handled through:
- `src/services/api.ts` - API service functions
- `src/hooks/useApi.ts` - React Query hooks
- `src/lib/api.ts` - Axios client with interceptors

## State Management

Zustand store manages:
- Selected case
- Selected recommendation
- Selected execution
- Sidebar collapse state

## Dark Mode

The app uses dark mode by default with full TailwindCSS theming support.

## Environment Variables

Create a `.env` file:

```
VITE_API_URL=http://localhost:8000
```

## Contributing

1. Follow the existing code structure
2. Use TypeScript types
3. Keep components minimal
4. Follow dark mode design system
5. Test API integrations

---

Built with ❤️ for Enterprise AI
