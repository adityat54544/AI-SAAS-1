# AutoDevOps AI Platform

AI-powered DevOps automation platform for intelligent repository analysis, CI/CD generation, and code quality insights.

## Features

- **🔍 AI-Powered Analysis**: Leverage Gemini 1.5 Flash for comprehensive repository analysis
- **🔐 GitHub Integration**: OAuth-based GitHub connection with secure token storage
- **📊 Health Scoring**: Quantified metrics for security, performance, and code quality
- **🚀 CI/CD Generation**: Automatically generate optimized CI/CD configurations
- **🔄 Real-time Updates**: Live progress updates via Supabase realtime subscriptions
- **🏗️ Multi-tenant**: Organization-based data isolation with Row-Level Security

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Next.js       │     │   FastAPI       │     │   Supabase      │
│   Frontend      │────▶│   Backend       │────▶│   PostgreSQL    │
│   (Vercel)      │     │   (Railway)     │     │   + Realtime    │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   Redis +       │
                        │   Workers       │
                        │   (Background)  │
                        └─────────────────┘
```

## Tech Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, React Query
- **Backend**: Python FastAPI, Pydantic
- **Database**: Supabase PostgreSQL with Row-Level Security
- **AI**: Google Gemini 1.5 Flash
- **Queue**: Redis with BullMQ
- **Auth**: GitHub OAuth

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- Supabase account
- GitHub OAuth App
- Google AI Studio API key

### 1. Clone and Setup

```bash
git clone <repository-url>
cd autodevops-ai-platform
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your credentials
```

### 3. Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local with your credentials
```

### 4. Database Setup

Apply Supabase migrations:

```bash
supabase db push
```

### 5. Run Development Servers

```bash
# Terminal 1: Backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Redis (Docker)
docker run -p 6379:6379 redis:7-alpine
```

## Environment Variables

### Backend (.env)

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key | Yes |
| `GITHUB_CLIENT_ID` | GitHub OAuth client ID | Yes |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth client secret | Yes |
| `GEMINI_API_KEY` | Google AI Studio API key | Yes |
| `ENCRYPTION_KEY` | 32-byte base64-encoded key | Yes |
| `REDIS_URL` | Redis connection URL | No |
| `SENTRY_DSN` | Sentry error tracking DSN | No |

### Frontend (.env.local)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend API URL |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anonymous key |

## Project Structure

```
├── app/                    # FastAPI backend
│   ├── ai/                 # AI provider abstraction
│   │   ├── provider.py     # Base provider class
│   │   ├── gemini_provider.py
│   │   ├── prompts.py      # Prompt templates
│   │   └── router.py       # Provider router
│   ├── routers/            # API endpoints
│   │   ├── auth.py         # GitHub OAuth
│   │   ├── repositories.py # Repository CRUD
│   │   ├── analysis.py     # Analysis endpoints
│   │   ├── jobs.py         # Job management
│   │   ├── webhooks.py     # GitHub webhooks
│   │   └── ci_cd.py        # CI/CD generation
│   ├── services/           # Business logic
│   │   ├── encryption_service.py
│   │   ├── github_service.py
│   │   ├── analysis_service.py
│   │   └── job_service.py
│   ├── config.py           # Settings
│   └── main.py             # FastAPI app
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/            # App router pages
│   │   ├── components/     # React components
│   │   └── lib/            # Utilities
│   ├── package.json
│   └── tailwind.config.js
├── supabase/
│   └── migrations/         # SQL migrations
└── requirements.txt        # Python dependencies
```

## API Endpoints

### Authentication
- `GET /auth/github` - Initiate GitHub OAuth
- `GET /auth/github/callback` - OAuth callback
- `GET /auth/session` - Get current session
- `POST /auth/logout` - Logout user

### Repositories
- `GET /repositories` - List connected repositories
- `GET /repositories/github` - List GitHub repos
- `POST /repositories/connect` - Connect repository
- `GET /repositories/{id}` - Get repository details
- `GET /repositories/{id}/health` - Get health score

### Analysis
- `POST /analysis` - Trigger analysis
- `GET /analysis/{id}` - Get analysis results
- `GET /analysis/{id}/recommendations` - Get recommendations

### Jobs
- `GET /jobs` - List jobs
- `GET /jobs/{id}` - Get job status
- `GET /jobs/{id}/logs` - Get job logs

### CI/CD
- `POST /ci-cd/generate` - Generate CI/CD config
- `GET /ci-cd/templates` - List templates
- `POST /ci-cd/validate` - Validate config

### Webhooks
- `POST /webhooks/github` - Handle GitHub events

## Database Schema

The platform uses Supabase PostgreSQL with the following tables:

- `users` - User accounts
- `organizations` - Multi-tenant organizations
- `repositories` - Connected GitHub repositories
- `analyses` - Analysis records
- `recommendations` - Analysis recommendations
- `jobs` - Background job queue
- `github_tokens` - Encrypted OAuth tokens
- `artifacts` - Generated CI configs

## Security

- **AES-256-GCM** encryption for GitHub tokens
- **Row-Level Security** for data isolation
- **CSRF protection** via OAuth state parameter
- **Webhook signature verification**
- **Rate limiting** on API endpoints

## Development

### Run Tests

```bash
# Backend tests
pytest tests/ -v

# Frontend tests
cd frontend && npm test
```

### Code Quality

```bash
# Python linting
ruff check app/
mypy app/

# Frontend linting
cd frontend && npm run lint
```

## Deployment

### Railway (Backend)

1. Connect repository to Railway
2. Set environment variables
3. Deploy with `railway up`

### Vercel (Frontend)

1. Connect repository to Vercel
2. Set environment variables
3. Deploy with `vercel --prod`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to the branch
5. Open a Pull Request

## License

MIT License - see LICENSE file for details.