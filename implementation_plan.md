# Implementation Plan

## [Overview]

Build a complete AI-powered DevOps automation platform named autodevops-ai-platform that combines a Next.js TypeScript frontend with an existing Python FastAPI backend, integrating Gemini 1.5 Flash AI for intelligent repository analysis, GitHub OAuth integration, and real-time dashboard updates through Supabase.

The platform enables development teams to connect their GitHub repositories, receive AI-powered analysis of code quality, security vulnerabilities, and CI/CD optimization suggestions. The architecture preserves the existing FastAPI backend while adding a modern Next.js dashboard frontend, Redis-powered asynchronous workers for background processing, and a provider-abstracted AI layer using Google AI Studio's Gemini 1.5 Flash model. The system deploys with Railway for backend services and Vercel for the frontend, using Supabase PostgreSQL with Row-Level Security for multi-tenant data isolation, realtime subscriptions for live dashboard updates, and encrypted storage for GitHub tokens and sensitive artifacts.

## [Types]

The platform requires comprehensive TypeScript interfaces for the frontend and Python Pydantic models for the backend API, with shared type definitions for cross-platform consistency.

### Frontend TypeScript Types (frontend/src/types/)

```typescript
// frontend/src/types/auth.types.ts
interface User {
  id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  created_at: string;
  updated_at: string;
}

interface Session {
  access_token: string;
  refresh_token: string;
  expires_at: number;
  user: User;
}

interface AuthState {
  user: User | null;
  session: Session | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

// frontend/src/types/repository.types.ts
interface Repository {
  id: string;
  org_id: string;
  github_id: number;
  name: string;
  full_name: string;
  description: string | null;
  html_url: string;
  language: string | null;
  stargazers_count: number;
  forks_count: number;
  is_private: boolean;
  is_active: boolean;
  last_analyzed_at: string | null;
  created_at: string;
  updated_at: string;
}

interface RepositoryHealth {
  id: string;
  repository_id: string;
  overall_score: number;
  security_score: number;
  performance_score: number;
  code_quality_score: number;
  ci_cd_score: number;
  dependencies_score: number;
  analysis_timestamp: string;
  metrics: HealthMetrics;
}

interface HealthMetrics {
  open_issues_count: number;
  open_prs_count: number;
  stale_branches_count: number;
  outdated_dependencies_count: number;
  security_vulnerabilities: SecurityVulnerability[];
  code_complexity: ComplexityMetrics;
}

interface SecurityVulnerability {
  severity: 'critical' | 'high' | 'medium' | 'low';
  count: number;
  packages: string[];
}

interface ComplexityMetrics {
  average_cyclomatic: number;
  average_cognitive: number;
  maintainability_index: number;
}

// frontend/src/types/analysis.types.ts
interface Analysis {
  id: string;
  repository_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  analysis_type: 'full' | 'security' | 'performance' | 'ci_cd';
  triggered_by: string;
  started_at: string | null;
  completed_at: string | null;
  results: AnalysisResults | null;
  error_message: string | null;
  created_at: string;
}

interface AnalysisResults {
  summary: string;
  recommendations: Recommendation[];
  generated_ci_config: string | null;
  remediation_snippets: RemediationSnippet[];
  model_used: string;
  tokens_used: number;
}

interface Recommendation {
  id: string;
  category: 'security' | 'performance' | 'code_quality' | 'ci_cd' | 'dependencies';
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  title: string;
  description: string;
  file_path: string | null;
  line_number: number | null;
  suggested_fix: string | null;
}

interface RemediationSnippet {
  id: string;
  file_path: string;
  original_code: string;
  suggested_code: string;
  explanation: string;
  apply_status: 'pending' | 'applied' | 'rejected';
}

// frontend/src/types/job.types.ts
interface Job {
  id: string;
  job_type: 'analysis' | 'clone' | 'sync' | 'ci_generation';
  status: 'queued' | 'processing' | 'completed' | 'failed';
  repository_id: string;
  progress: number;
  error_message: string | null;
  result_data: Record<string, unknown> | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

interface JobProgress {
  job_id: string;
  current_step: string;
  total_steps: number;
  completed_steps: number;
  percentage: number;
  logs: string[];
}
```

### Backend Python Pydantic Models (backend/app/models/)

```python
# backend/app/models/user.py
from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None

class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# backend/app/models/repository.py
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional, List

class RepositoryBase(BaseModel):
    name: str
    full_name: str
    description: Optional[str] = None
    html_url: str
    language: Optional[str] = None
    is_private: bool = False

class RepositoryCreate(RepositoryBase):
    github_id: int
    org_id: UUID
    stargazers_count: int = 0
    forks_count: int = 0

class RepositoryResponse(RepositoryBase):
    id: UUID
    org_id: UUID
    github_id: int
    stargazers_count: int
    forks_count: int
    is_active: bool
    last_analyzed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class RepositoryHealthResponse(BaseModel):
    id: UUID
    repository_id: UUID
    overall_score: float
    security_score: float
    performance_score: float
    code_quality_score: float
    ci_cd_score: float
    dependencies_score: float
    analysis_timestamp: datetime
    metrics: dict

# backend/app/models/analysis.py
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional, List, Dict, Any
from enum import Enum

class AnalysisStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class AnalysisType(str, Enum):
    FULL = "full"
    SECURITY = "security"
    PERFORMANCE = "performance"
    CI_CD = "ci_cd"

class AnalysisCreate(BaseModel):
    repository_id: UUID
    analysis_type: AnalysisType = AnalysisType.FULL

class AnalysisResponse(BaseModel):
    id: UUID
    repository_id: UUID
    status: AnalysisStatus
    analysis_type: AnalysisType
    triggered_by: UUID
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    results: Optional[Dict[str, Any]]
    error_message: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class RecommendationModel(BaseModel):
    id: UUID
    category: str
    severity: str
    title: str
    description: str
    file_path: Optional[str]
    line_number: Optional[int]
    suggested_fix: Optional[str]

class RemediationSnippetModel(BaseModel):
    id: UUID
    file_path: str
    original_code: str
    suggested_code: str
    explanation: str
    apply_status: str

# backend/app/models/job.py
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any
from enum import Enum

class JobType(str, Enum):
    ANALYSIS = "analysis"
    CLONE = "clone"
    SYNC = "sync"
    CI_GENERATION = "ci_generation"

class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobCreate(BaseModel):
    job_type: JobType
    repository_id: UUID
    payload: Optional[Dict[str, Any]] = None

class JobResponse(BaseModel):
    id: UUID
    job_type: JobType
    status: JobStatus
    repository_id: UUID
    progress: int
    error_message: Optional[str]
    result_data: Optional[Dict[str, Any]]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class JobProgressUpdate(BaseModel):
    job_id: UUID
    current_step: str
    total_steps: int
    completed_steps: int
    logs: List[str]
```

### AI Provider Abstraction Types

```python
# backend/app/ai/types.py
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum

class AIProvider(str, Enum):
    GEMINI = "gemini"
    OPENROUTER = "openrouter"

class AnalysisRequest(BaseModel):
    repository_context: Dict[str, Any]
    file_contents: Optional[List[Dict[str, str]]] = None
    analysis_type: str
    custom_prompt: Optional[str] = None

class AIResponse(BaseModel):
    content: str
    model_used: str
    tokens_used: int
    provider: AIProvider
    structured_results: Optional[Dict[str, Any]] = None

class CIConfigRequest(BaseModel):
    repository_context: Dict[str, Any]
    target_platform: str  # github_actions, gitlab_ci, circleci
    requirements: List[str]

class CIConfigResponse(BaseModel):
    config_yaml: str
    explanations: List[str]
    provider: AIProvider
```

## [Files]

The implementation requires creating a structured monorepo with separate directories for frontend, backend, workers, and infrastructure.

### New Files to Create

**Frontend (Next.js TypeScript)**
- `frontend/package.json` - Node.js dependencies and scripts
- `frontend/next.config.js` - Next.js configuration with Supabase integration
- `frontend/tsconfig.json` - TypeScript strict mode configuration
- `frontend/tailwind.config.js` - Tailwind CSS configuration
- `frontend/postcss.config.js` - PostCSS configuration
- `frontend/.env.example` - Frontend environment variables template
- `frontend/src/app/layout.tsx` - Root layout with providers
- `frontend/src/app/page.tsx` - Landing page
- `frontend/src/app/dashboard/page.tsx` - Main dashboard
- `frontend/src/app/repositories/page.tsx` - Repository list and selection
- `frontend/src/app/repositories/[id]/page.tsx` - Repository detail view
- `frontend/src/app/repositories/[id]/analysis/page.tsx` - Analysis results
- `frontend/src/app/repositories/[id]/ci-cd/page.tsx` - CI/CD suggestions
- `frontend/src/app/repositories/[id]/logs/page.tsx` - Job logs viewer
- `frontend/src/app/auth/callback/page.tsx` - OAuth callback handler
- `frontend/src/app/auth/login/page.tsx` - Login page with GitHub OAuth
- `frontend/src/components/providers/SupabaseProvider.tsx` - Supabase client provider
- `frontend/src/components/providers/ThemeProvider.tsx` - Theme management
- `frontend/src/components/auth/LoginButton.tsx` - GitHub OAuth button
- `frontend/src/components/auth/UserMenu.tsx` - User dropdown menu
- `frontend/src/components/dashboard/HealthScoreCard.tsx` - Health score display
- `frontend/src/components/dashboard/RepositoryList.tsx` - Repository grid/list
- `frontend/src/components/dashboard/RecentActivity.tsx` - Activity feed
- `frontend/src/components/dashboard/AnalysisProgress.tsx` - Real-time progress
- `frontend/src/components/repositories/RepositoryCard.tsx` - Repository card
- `frontend/src/components/repositories/RepositorySelector.tsx` - GitHub repo selector
- `frontend/src/components/analysis/RecommendationCard.tsx` - Recommendation display
- `frontend/src/components/analysis/CodeDiffViewer.tsx` - Remediation diff view
- `frontend/src/components/ci/CIConfigPreview.tsx` - CI config preview
- `frontend/src/hooks/useAuth.ts` - Authentication hook
- `frontend/src/hooks/useRepositories.ts` - Repository data hook
- `frontend/src/hooks/useRealtime.ts` - Supabase realtime hook
- `frontend/src/hooks/useJobs.ts` - Job progress hook
- `frontend/src/lib/supabase/client.ts` - Supabase browser client
- `frontend/src/lib/supabase/server.ts` - Supabase server client
- `frontend/src/lib/api/client.ts` - Backend API client
- `frontend/src/types/auth.types.ts` - Auth type definitions
- `frontend/src/types/repository.types.ts` - Repository types
- `frontend/src/types/analysis.types.ts` - Analysis types
- `frontend/src/types/job.types.ts` - Job types

**Backend (FastAPI Python) - Extending existing app/**
- `backend/app/__init__.py` - Package initialization
- `backend/app/main.py` - FastAPI app factory and routes (modified)
- `backend/app/config.py` - Pydantic settings configuration
- `backend/app/database.py` - Database connection management
- `backend/app/supabase_client.py` - Supabase client (existing)
- `backend/app/models/__init__.py` - Model exports
- `backend/app/models/user.py` - User Pydantic models
- `backend/app/models/repository.py` - Repository models
- `backend/app/models/analysis.py` - Analysis models
- `backend/app/models/job.py` - Job models
- `backend/app/models/organization.py` - Organization models
- `backend/app/routers/__init__.py` - Router exports
- `backend/app/routers/auth.py` - Authentication routes
- `backend/app/routers/repositories.py` - Repository CRUD routes
- `backend/app/routers/analysis.py` - Analysis trigger and results
- `backend/app/routers/jobs.py` - Job status and logs
- `backend/app/routers/ci_cd.py` - CI/CD generation endpoints
- `backend/app/routers/webhooks.py` - GitHub webhook handlers
- `backend/app/services/__init__.py` - Service exports
- `backend/app/services/github_service.py` - GitHub API integration
- `backend/app/services/encryption_service.py` - Token encryption
- `backend/app/services/analysis_service.py` - Analysis orchestration
- `backend/app/services/job_service.py` - Job queue management
- `backend/app/ai/__init__.py` - AI module exports
- `backend/app/ai/provider.py` - AI provider abstract base
- `backend/app/ai/gemini_provider.py` - Gemini 1.5 Flash implementation
- `backend/app/ai/prompts.py` - Prompt templates
- `backend/app/ai/router.py` - AI request router
- `backend/app/workers/__init__.py` - Worker exports
- `backend/app/workers/tasks.py` - Background task definitions

**Workers (Redis/BullMQ)**
- `workers/package.json` - Worker dependencies
- `workers/tsconfig.json` - TypeScript configuration
- `workers/src/index.ts` - Worker entry point
- `workers/src/queues/analysis.queue.ts` - Analysis job queue
- `workers/src/queues/clone.queue.ts` - Repository clone queue
- `workers/src/processors/analysis.processor.ts` - Analysis job processor
- `workers/src/processors/clone.processor.ts` - Clone job processor
- `workers/src/services/git.service.ts` - Git operations
- `workers/src/services/static-analysis.service.ts` - Code analysis
- `workers/src/services/ai-client.service.ts` - AI API client
- `workers/src/services/supabase.service.ts` - Supabase client
- `workers/src/utils/logger.ts` - Structured logging

**Infrastructure**
- `infra/docker-compose.dev.yml` - Development Docker Compose
- `infra/docker-compose.prod.yml` - Production Docker Compose
- `infra/backend/Dockerfile` - Backend container
- `infra/workers/Dockerfile` - Workers container
- `infra/redis/redis.conf` - Redis configuration
- `infra/kubernetes/backend-deployment.yaml` - K8s backend deployment
- `infra/kubernetes/workers-deployment.yaml` - K8s workers deployment
- `infra/kubernetes/redis-deployment.yaml` - K8s Redis deployment
- `infra/kubernetes/secrets.yaml` - K8s secrets template
- `infra/kubernetes/configmap.yaml` - K8s configmap

**Database Migrations**
- `supabase/migrations/20260220000000_create_organizations.sql` - Organizations table
- `supabase/migrations/20260220000001_create_repositories.sql` - Repositories table
- `supabase/migrations/20260220000002_create_analyses.sql` - Analyses table
- `supabase/migrations/20260220000003_create_jobs.sql` - Jobs table
- `supabase/migrations/20260220000004_create_artifacts.sql` - Artifacts table
- `supabase/migrations/20260220000005_create_github_tokens.sql` - Encrypted tokens
- `supabase/migrations/20260220000006_enable_rls.sql` - Row-Level Security policies
- `supabase/migrations/20260220000007_create_functions.sql` - Database functions
- `supabase/seed.sql` - Demo data seeding

**CI/CD**
- `.github/workflows/ci.yml` - Lint, test, build pipeline
- `.github/workflows/cd-frontend.yml` - Vercel deployment
- `.github/workflows/cd-backend.yml` - Railway deployment
- `.github/workflows/db-migration.yml` - Database migration job

**Documentation**
- `docs/README.md` - Documentation index
- `docs/ARCHITECTURE.md` - Architecture documentation
- `docs/API.md` - OpenAPI specification
- `docs/DEPLOYMENT.md` - Deployment guide
- `docs/SECURITY.md` - Security controls checklist
- `docs/DEMO.md` - Demo script
- `docs/architecture.mermaid` - Mermaid diagram source

**Configuration**
- `.env.example` - Updated environment template
- `.gitignore` - Updated ignore patterns
- `.pre-commit-config.yaml` - Updated pre-commit hooks
- `pyproject.toml` - Python project configuration
- `setup.cfg` - Tool configuration
- `.eslintrc.js` - ESLint configuration
- `.prettierrc` - Prettier configuration
- `Makefile` - Development commands

### Existing Files to Modify

- `app/main.py` - Transform into modular FastAPI app factory
- `app/supabase_client.py` - Add connection pooling and error handling
- `requirements.txt` - Add new dependencies (cryptography, redis, etc.)
- `Dockerfile` - Multi-stage build for production
- `docker-compose.yml` - Add Redis, workers services
- `.gitignore` - Add new patterns for secrets, env files
- `.pre-commit-config.yaml` - Add ruff, mypy, additional hooks

### Files to Delete/Move

- Delete: `test_supabase.py` (root level test - move to tests/)
- Move: Current `app/` to `backend/app/` for monorepo structure
- Move: Current `tests/` to `backend/tests/`

## [Functions]

The implementation requires comprehensive API endpoints, service functions, and worker processors.

### New Functions

**Authentication (backend/app/routers/auth.py)**
- `GET /auth/github` - Initiate GitHub OAuth flow
- `GET /auth/github/callback` - Handle OAuth callback, exchange code for token
- `POST /auth/token/refresh` - Refresh GitHub access token
- `DELETE /auth/github/disconnect` - Revoke GitHub access
- `GET /auth/session` - Get current session info

**Repositories (backend/app/routers/repositories.py)**
- `GET /repositories` - List user's connected repositories
- `GET /repositories/github` - List available GitHub repos for connection
- `POST /repositories/connect` - Connect a GitHub repository
- `DELETE /repositories/{id}` - Disconnect a repository
- `GET /repositories/{id}/health` - Get repository health score
- `POST /repositories/{id}/sync` - Trigger metadata sync

**Analysis (backend/app/routers/analysis.py)**
- `POST /analysis` - Trigger new analysis job
- `GET /analysis/{id}` - Get analysis results
- `GET /analysis/{id}/recommendations` - Get recommendations list
- `POST /analysis/{id}/apply` - Apply remediation (simulation mode)
- `GET /repositories/{id}/analyses` - List repository analyses

**Jobs (backend/app/routers/jobs.py)**
- `GET /jobs` - List all jobs for user
- `GET /jobs/{id}` - Get job status
- `GET /jobs/{id}/logs` - Get job logs
- `DELETE /jobs/{id}` - Cancel queued job

**CI/CD (backend/app/routers/ci_cd.py)**
- `POST /ci-cd/generate` - Generate CI/CD config from template
- `GET /ci-cd/templates` - List available templates
- `POST /ci-cd/validate` - Validate existing CI config

**Webhooks (backend/app/routers/webhooks.py)**
- `POST /webhooks/github` - Handle GitHub webhook events
- `POST /webhooks/github/verify` - Verify webhook signature

**Services (backend/app/services/)**

`github_service.py`:
- `get_user_repositories(token: str) -> List[Repository]` - Fetch user's GitHub repos
- `get_repository_metadata(owner: str, repo: str, token: str) -> RepositoryMetadata` - Get repo details
- `create_webhook(repo_id: str, token: str) -> WebhookConfig` - Setup webhook
- `delete_webhook(hook_id: str, token: str) -> bool` - Remove webhook
- `get_rate_limit(token: str) -> RateLimitInfo` - Check API rate limits

`encryption_service.py`:
- `encrypt_token(token: str, key: bytes) -> str` - Encrypt GitHub token
- `decrypt_token(encrypted: str, key: bytes) -> str` - Decrypt token
- `rotate_encryption_key(old_key: bytes, new_key: bytes) -> None` - Key rotation

`analysis_service.py`:
- `create_analysis(repo_id: UUID, analysis_type: AnalysisType) -> Analysis` - Initialize analysis
- `queue_analysis_job(analysis_id: UUID) -> Job` - Queue background job
- `process_analysis_results(analysis_id: UUID, results: dict) -> None` - Store results

`job_service.py`:
- `create_job(job_type: JobType, repo_id: UUID) -> Job` - Create new job
- `update_job_progress(job_id: UUID, progress: int, step: str) -> Job` - Update progress
- `complete_job(job_id: UUID, results: dict) -> Job` - Mark complete
- `fail_job(job_id: UUID, error: str) -> Job` - Mark failed

**AI Provider (backend/app/ai/)**

`provider.py`:
- `abstract class AIProviderBase` - Base class for AI providers
- `async analyze(request: AnalysisRequest) -> AIResponse` - Perform analysis
- `async generate_ci_config(request: CIConfigRequest) -> CIConfigResponse` - Generate CI config

`gemini_provider.py`:
- `class GeminiProvider(AIProviderBase)` - Gemini implementation
- `async analyze(request: AnalysisRequest) -> AIResponse` - Call Gemini API
- `async generate_ci_config(request: CIConfigRequest) -> CIConfigResponse` - Generate with Gemini
- `_build_prompt(request: AnalysisRequest) -> str` - Construct prompt

`prompts.py`:
- `ANALYSIS_SYSTEM_PROMPT` - System prompt for analysis
- `SECURITY_ANALYSIS_PROMPT` - Security-focused prompt
- `PERFORMANCE_ANALYSIS_PROMPT` - Performance analysis prompt
- `CI_GENERATION_PROMPT` - CI config generation prompt
- `REMEDIATION_PROMPT` - Fix suggestion prompt

`router.py`:
- `class AIRouter` - Routes to appropriate provider
- `async route_analysis(request: AnalysisRequest) -> AIResponse` - Route analysis
- `async route_ci_generation(request: CIConfigRequest) -> CIConfigResponse` - Route CI gen

**Worker Processors (workers/src/processors/)**

`analysis.processor.ts`:
- `processAnalysisJob(job: Job)` - Main analysis processor
- `fetchRepositoryContext(repoId: string)` - Get repo context
- `callAIProvider(request: AnalysisRequest)` - Call backend AI
- `storeResults(analysisId: string, results: AnalysisResults)` - Save to DB

`clone.processor.ts`:
- `processCloneJob(job: Job)` - Clone processor
- `shallowClone(url: string, branch: string)` - Shallow git clone
- `sparseClone(url: string, paths: string[])` - Sparse checkout
- `extractMetadata(repoPath: string)` - Extract repo info

### Modified Functions

**backend/app/main.py** (currently app/main.py):
- Transform from single file to app factory pattern
- Add middleware for CORS, rate limiting, request ID
- Add exception handlers for custom errors
- Include routers for all modules
- Add OpenAPI documentation configuration
- Add health check and metrics endpoints

**app/supabase_client.py** (move to backend/app/):
- Add connection pooling with async support
- Add retry logic for transient failures
- Add logging for database operations
- Export both sync and async clients

## [Classes]

### New Classes

**Backend Classes**

`backend/app/services/github_service.py`:
- `class GitHubService` - GitHub API client wrapper
  - Methods: `get_user_repositories`, `get_repository_metadata`, `create_webhook`, `delete_webhook`, `get_rate_limit`
  - Handles rate limiting, retries, error handling

`backend/app/services/encryption_service.py`:
- `class EncryptionService` - AES-256-GCM encryption service
  - Methods: `encrypt_token`, `decrypt_token`, `rotate_encryption_key`
  - Uses cryptography library for secure token storage

`backend/app/services/analysis_service.py`:
- `class AnalysisService` - Analysis orchestration
  - Methods: `create_analysis`, `queue_analysis_job`, `process_analysis_results`, `get_analysis_history`
  - Coordinates between GitHub, AI, and database

`backend/app/services/job_service.py`:
- `class JobService` - Job queue management
  - Methods: `create_job`, `update_job_progress`, `complete_job`, `fail_job`, `get_job_status`
  - Interfaces with Redis queue

`backend/app/ai/provider.py`:
- `class AIProviderBase(ABC)` - Abstract base for AI providers
  - Abstract methods: `analyze`, `generate_ci_config`, `validate_response`
  - Concrete methods: `build_context`, `parse_structured_response`

`backend/app/ai/gemini_provider.py`:
- `class GeminiProvider(AIProviderBase)` - Gemini 1.5 Flash implementation
  - Methods: `analyze`, `generate_ci_config`, `validate_response`
  - Handles Gemini API authentication, rate limiting, response parsing

`backend/app/ai/router.py`:
- `class AIRouter` - Routes to configured AI provider
  - Methods: `route_analysis`, `route_ci_generation`, `switch_provider`
  - Provider abstraction for future extensibility

**Worker Classes**

`workers/src/services/git.service.ts`:
- `class GitService` - Git operations wrapper
  - Methods: `shallowClone`, `sparseCheckout`, `getMetadata`, `cleanup`
  - Uses isomorphic-git for cross-platform support

`workers/src/services/static-analysis.service.ts`:
- `class StaticAnalysisService` - Code analysis
  - Methods: `analyzeComplexity`, `analyzeSecurity`, `analyzeDependencies`, `generateMetrics`
  - Integrates multiple analysis tools

`workers/src/services/ai-client.service.ts`:
- `class AIClientService` - AI API client
  - Methods: `analyze`, `generateCIConfig`, `streamResponse`
  - Handles communication with backend AI router

### Modified Classes

None - the current implementation uses functional style without classes that need modification.

## [Dependencies]

### Frontend Dependencies (frontend/package.json)

```json
{
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "@supabase/supabase-js": "^2.43.0",
    "@supabase/auth-helpers-nextjs": "^0.10.0",
    "@tanstack/react-query": "^5.36.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.1",
    "lucide-react": "^0.378.0",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "@radix-ui/react-tabs": "^1.0.4",
    "@radix-ui/react-tooltip": "^1.0.7",
    "react-hot-toast": "^2.4.1",
    "date-fns": "^3.6.0",
    "diff": "^5.2.0",
    "react-diff-viewer": "^4.0.4"
  },
  "devDependencies": {
    "typescript": "^5.4.5",
    "@types/node": "^20.12.12",
    "@types/react": "^18.3.2",
    "@types/react-dom": "^18.3.0",
    "eslint": "^8.57.0",
    "eslint-config-next": "^14.2.0",
    "prettier": "^3.2.5",
    "@typescript-eslint/eslint-plugin": "^7.9.0",
    "@typescript-eslint/parser": "^7.9.0"
  }
}
```

### Backend Dependencies (requirements.txt additions)

```text
# AI Integration
google-generativeai>=0.5.0
httpx>=0.27.0

# Redis and Queue
redis>=5.0.0
rq>=1.16.0

# Security
cryptography>=42.0.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4

# GitHub Integration
PyGithub>=2.3.0

# Code Analysis
radon>=6.0.0
bandit>=1.7.8
safety>=3.1.0

# Observability
sentry-sdk[fastapi]>=1.45.0
prometheus-client>=0.20.0
structlog>=24.1.0

# Testing
pytest-asyncio>=0.23.6
pytest-cov>=5.0.0
pytest-mock>=3.14.0
testcontainers>=4.4.0

# Linting and Formatting
ruff>=0.4.0
mypy>=1.10.0
types-redis>=4.6.0
```

### Worker Dependencies (workers/package.json)

```json
{
  "dependencies": {
    "bullmq": "^5.8.0",
    "ioredis": "^5.4.1",
    "@supabase/supabase-js": "^2.43.0",
    "isomorphic-git": "^0.44.0",
    "node-fetch": "^3.3.2",
    "pino": "^9.0.0",
    "pino-pretty": "^11.0.0",
    "dotenv": "^16.4.5",
    "zod": "^3.23.8"
  },
  "devDependencies": {
    "typescript": "^5.4.5",
    "@types/node": "^20.12.12",
    "eslint": "^8.57.0",
    "prettier": "^3.2.5",
    "vitest": "^1.6.0",
    "@types/ioredis": "^5.0.0"
  }
}
```

### Infrastructure Dependencies
- Redis 7.x (Alpine image)
- Node.js 20.x (Alpine image for workers)
- Python 3.11 (Slim image for backend)

## [Testing]

### Test File Requirements

**Backend Tests (backend/tests/)**

`test_auth.py`:
- Test GitHub OAuth flow initialization
- Test OAuth callback handling
- Test token refresh mechanism
- Test token revocation

`test_repositories.py`:
- Test repository listing
- Test repository connection
- Test repository disconnection
- Test health score calculation

`test_analysis.py`:
- Test analysis job creation
- Test analysis result retrieval
- Test recommendation generation
- Test remediation application (simulation mode)

`test_github_service.py`:
- Mock GitHub API responses
- Test rate limit handling
- Test webhook creation/deletion
- Test metadata extraction

`test_encryption_service.py`:
- Test token encryption/decryption
- Test key rotation
- Test encryption with invalid inputs

`test_ai_provider.py`:
- Mock Gemini API responses
- Test prompt construction
- Test response parsing
- Test error handling

`test_integration.py`:
- End-to-end analysis workflow
- Job queue processing
- Real-time updates via Supabase

**Frontend Tests (frontend/__tests__/)**

`auth.test.tsx`:
- Test login button renders
- Test OAuth redirect
- Test session persistence

`dashboard.test.tsx`:
- Test repository list rendering
- Test health score display
- Test real-time progress updates

`analysis.test.tsx`:
- Test analysis trigger
- Test recommendation display
- Test code diff viewer

**Worker Tests (workers/src/__tests__/)**

`analysis.processor.test.ts`:
- Test job processing
- Test error handling
- Test retry logic

`clone.processor.test.ts`:
- Test shallow clone
- Test sparse checkout
- Test metadata extraction

### Test Coverage Requirements
- Backend: Minimum 80% coverage
- Frontend: Minimum 70% coverage for components
- Workers: Minimum 75% coverage
- Critical paths (auth, encryption, AI): 100% coverage

### Validation Strategies
1. Unit tests for all service functions
2. Integration tests for API endpoints
3. E2E tests for critical user flows
4. Load testing for job queue
5. Security testing for authentication flows

## [Implementation Order]

The implementation follows a logical sequence to minimize conflicts and ensure successful integration:

1. **Foundation Setup** (Days 1-2)
   - Create monorepo directory structure
   - Setup Python backend configuration (pyproject.toml, ruff, mypy)
   - Setup Next.js frontend project (package.json, tailwind, typescript)
   - Setup workers project (package.json, typescript)
   - Create comprehensive .env.example

2. **Database Schema & Migrations** (Day 3)
   - Create Supabase migration files for all tables
   - Implement Row-Level Security policies
   - Create database functions and triggers
   - Seed demo data

3. **Backend Core Services** (Days 4-5)
   - Implement configuration management
   - Implement encryption service
   - Implement GitHub service
   - Implement Supabase client improvements

4. **Backend API Routes** (Days 6-7)
   - Implement authentication routes
   - Implement repository routes
   - Implement analysis routes
   - Implement job routes
   - Implement webhook routes

5. **AI Integration Layer** (Day 8)
   - Implement AI provider abstraction
   - Implement Gemini 1.5 Flash provider
   - Implement AI router
   - Create prompt templates

6. **Worker Infrastructure** (Days 9-10)
   - Setup Redis queue
   - Implement analysis processor
   - Implement clone processor
   - Implement static analysis service

7. **Frontend Foundation** (Days 11-12)
   - Setup Supabase providers
   - Implement authentication flow
   - Create layout components
   - Implement API client

8. **Frontend Dashboard & Features** (Days 13-15)
   - Implement repository list and selector
   - Implement health dashboard
   - Implement analysis results view
   - Implement CI/CD suggestions
   - Implement real-time progress

9. **CI/CD Pipelines** (Day 16)
   - Create GitHub Actions CI workflow
   - Create frontend deployment workflow
   - Create backend deployment workflow
   - Create database migration workflow

10. **Docker & Kubernetes** (Day 17)
    - Create production Dockerfiles
    - Create Docker Compose files
    - Create Kubernetes manifests

11. **Observability & Security** (Day 18)
    - Add structured logging
    - Add Sentry integration
    - Add Prometheus metrics
    - Complete security checklist

12. **Documentation** (Day 19)
    - Write comprehensive README
    - Create architecture diagram
    - Write API documentation
    - Write deployment guide
    - Write security report

13. **Testing & Validation** (Day 20)
    - Complete unit test coverage
    - Complete integration tests
    - Write demo script
    - Final validation and cleanup