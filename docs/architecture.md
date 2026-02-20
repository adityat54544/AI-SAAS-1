# AutoDevOps AI Platform - Architecture Documentation

**Author:** Aditya Tiwari, Founder & Lead Engineer  
**Last Updated:** February 2026

---

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Component Overview](#component-overview)
3. [Async Job Lifecycle](#async-job-lifecycle)
4. [Deployment Topology](#deployment-topology)
5. [Data Flow Diagrams](#data-flow-diagrams)
6. [Security Architecture](#security-architecture)
7. [Scaling Architecture](#scaling-architecture)

---

## High-Level Architecture

The system follows a layered, event-driven architecture designed for scalability and resilience.

```mermaid
flowchart TB
    subgraph "Client Layer"
        Browser[Browser]
        NextJS[Next.js 14<br/>Vercel Edge]
    end
    
    subgraph "API Layer - Railway"
        Gateway[API Gateway<br/>FastAPI]
        Auth[Auth Module<br/>OAuth2/JWT]
        RateLimit[Rate Limiter<br/>Redis-backed]
    end
    
    subgraph "Queue Layer - Railway"
        Redis[(Redis<br/>BullMQ)]
        Worker1[Worker 1]
        Worker2[Worker 2]
        WorkerN[Worker N]
    end
    
    subgraph "AI Layer"
        Router[AI Router<br/>Circuit Breaker]
        Quota[Quota Manager]
        Gemini[Gemini 1.5 Flash]
    end
    
    subgraph "Data Layer - Supabase"
        Postgres[(PostgreSQL<br/>+ RLS)]
        Realtime[Realtime<br/>Subscriptions]
        AuthDB[Auth Service]
    end
    
    subgraph "External Services"
        GitHub[GitHub API<br/>OAuth + Webhooks]
    end
    
    Browser --> NextJS
    NextJS -->|REST/HTTPS| Gateway
    Gateway --> Auth
    Gateway --> RateLimit
    Gateway --> Redis
    Gateway --> Postgres
    Gateway <-->|OAuth| GitHub
    
    Redis --> Worker1
    Redis --> Worker2
    Redis --> WorkerN
    
    Worker1 --> Router
    Worker2 --> Router
    WorkerN --> Router
    
    Router --> Quota
    Quota --> Gemini
    
    Worker1 --> Postgres
    Worker2 --> Postgres
    WorkerN --> Postgres
    
    Worker1 <-->|Fetch Content| GitHub
    
    NextJS <-->|Realtime| Realtime
    Postgres --> Realtime
    Auth --> AuthDB
```

---

## Component Overview

### Frontend (Next.js 14 / Vercel)

| Component | Technology | Purpose |
|-----------|------------|---------|
| Pages | App Router (RSC) | Server-rendered UI |
| State | React Query + Zustand | Client state management |
| Realtime | Supabase Realtime | Live job updates |
| Auth | Supabase Auth | Session management |

### API (FastAPI / Railway)

| Endpoint Group | Purpose | Rate Limit |
|----------------|---------|------------|
| `/auth/*` | OAuth flow, session management | 20/min |
| `/repositories/*` | GitHub repo management | 30/min |
| `/analysis/*` | Trigger and fetch analyses | 10/min |
| `/jobs/*` | Job status and logs | 20/min |
| `/webhooks/*` | GitHub webhooks | 100/min |

### Workers (BullMQ / Railway)

| Queue | Purpose | Concurrency | Timeout |
|-------|---------|-------------|---------|
| `analysis` | Repository analysis | 5 | 5 min |
| `sync` | Repository sync | 3 | 2 min |
| `ci_generation` | CI/CD config generation | 3 | 3 min |

### Data Layer (Supabase)

| Table | Purpose | RLS |
|-------|---------|-----|
| `users` | User profiles | Yes |
| `organizations` | Tenant accounts | Yes |
| `repositories` | Connected repos | Yes |
| `analyses` | Analysis results | Yes |
| `jobs` | Job records | Yes |
| `github_tokens` | Encrypted OAuth tokens | Yes |

---

## Async Job Lifecycle

### Complete Job Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Queue
    participant Worker
    participant GitHub
    participant AI
    participant DB
    participant Realtime
    
    User->>Frontend: Click "Analyze"
    Frontend->>API: POST /analysis
    API->>API: Validate request
    API->>API: Check rate limit
    API->>Queue: Enqueue job
    API->>DB: Create job record (pending)
    API-->>Frontend: 202 Accepted + job_id
    Frontend->>Realtime: Subscribe to job updates
    
    Queue->>Worker: Dequeue job
    Worker->>DB: Update job (active)
    DB->>Realtime: Broadcast update
    Realtime->>Frontend: Job status: active
    
    Worker->>GitHub: Fetch repository content
    GitHub-->>Worker: File tree + content
    
    Worker->>Worker: Token estimation
    Worker->>AI: Analyze request
    AI->>AI: Quota check
    AI->>AI: Circuit breaker check
    
    alt AI Success
        AI-->>Worker: Analysis result
        Worker->>Worker: Parse results
        Worker->>DB: Store analysis + update job (completed)
        DB->>Realtime: Broadcast update
        Realtime->>Frontend: Job status: completed
    else AI Failure
        AI-->>Worker: Error
        Worker->>Queue: Re-enqueue (with delay)
        Worker->>DB: Update job (retrying)
    end
    
    Frontend->>User: Display results
```

### Job State Machine

```mermaid
stateDiagram-v2
    [*] --> pending: Job Created
    
    pending --> active: Worker Acquires Lock
    pending --> failed: Queue Error
    
    active --> processing: Content Fetched
    active --> failed: Fetch Error
    active --> cancelled: User Cancel
    
    processing --> ai_request: Files Prepared
    processing --> failed: Parse Error
    
    ai_request --> completed: AI Success
    ai_request --> retrying: AI Error (retryable)
    ai_request --> failed: AI Error (fatal)
    
    retrying --> pending: Backoff Delay
    retrying --> dead_letter: Max Retries
    
    failed --> pending: Retry Available
    failed --> dead_letter: No More Retries
    
    completed --> [*]
    dead_letter --> [*]
    cancelled --> [*]
```

### Retry Configuration

```mermaid
flowchart LR
    A[Attempt 1] -->|Fail| B[Wait 30s]
    B --> C[Attempt 2]
    C -->|Fail| D[Wait 2m]
    D --> E[Attempt 3]
    E -->|Fail| F[Wait 5m]
    F --> G[Attempt 4]
    G -->|Fail| H[Dead Letter Queue]
    
    style H fill:#ff6b6b
```

---

## Deployment Topology

### Production Environment

```mermaid
flowchart TB
    subgraph "Vercel - Frontend"
        Edge[Edge Network<br/>CDN]
        NextApp[Next.js App<br/>Serverless Functions]
    end
    
    subgraph "Railway - Backend"
        subgraph "API Service"
            API1[API Replica 1]
            API2[API Replica 2]
            API3[API Replica 3]
        end
        
        subgraph "Worker Service"
            W1[Worker 1]
            W2[Worker 2]
            W3[Worker 3-5]
        end
        
        subgraph "Cron Service"
            Cron[Scheduler<br/>Backup/Cleanup]
        end
        
        subgraph "Infrastructure"
            RedisCluster[(Redis<br/>Managed)]
        end
    end
    
    subgraph "Supabase - Data"
        SupabaseAPI[Supabase API]
        SupabaseDB[(PostgreSQL<br/>Primary)]
        SupabaseRT[Realtime Server]
    end
    
    subgraph "External"
        GitHub[GitHub API]
        Gemini[Google AI]
        Sentry[Sentry]
    end
    
    Edge --> NextApp
    NextApp -->|HTTPS| API1
    NextApp -->|HTTPS| API2
    NextApp -->|HTTPS| API3
    
    API1 --> RedisCluster
    API2 --> RedisCluster
    API3 --> RedisCluster
    
    RedisCluster --> W1
    RedisCluster --> W2
    RedisCluster --> W3
    
    API1 --> SupabaseAPI
    API2 --> SupabaseAPI
    API3 --> SupabaseAPI
    
    W1 --> SupabaseAPI
    W2 --> SupabaseAPI
    W3 --> SupabaseAPI
    
    SupabaseAPI --> SupabaseDB
    SupabaseDB --> SupabaseRT
    
    NextApp <-->|Realtime WS| SupabaseRT
    
    API1 <-->|OAuth| GitHub
    W1 <-->|Fetch Content| GitHub
    W1 -->|Analysis| Gemini
    
    API1 -->|Errors| Sentry
    W1 -->|Errors| Sentry
    
    Cron --> SupabaseAPI
```

### Railway Service Configuration

```mermaid
flowchart LR
    subgraph "Railway Project"
        direction TB
        
        subgraph "autodevops-api"
            API[FastAPI Service]
            API_Config[Replicas: 1-3<br/>Health: /health<br/>Memory: 512MB]
        end
        
        subgraph "autodevops-worker"
            Worker[BullMQ Service]
            Worker_Config[Replicas: 1-5<br/>Queues: 3<br/>Memory: 1GB]
        end
        
        subgraph "autodevops-cron"
            Cron[Scheduler Service]
            Cron_Config[Replicas: 1<br/>Schedule: Daily 2AM<br/>Memory: 256MB]
        end
        
        subgraph "redis"
            Redis[(Redis Plugin)]
            Redis_Config[Memory: 256MB<br/>Persistence: AOF]
        end
    end
    
    API --> Redis
    Worker --> Redis
    Cron --> Redis
```

### Container Architecture

```mermaid
flowchart TB
    subgraph "Dockerfile.api"
        API_Base[python:3.11-slim]
        API_Deps[Install Dependencies]
        API_App[Copy Application]
        API_Run[uvicorn app.main:app]
    end
    
    subgraph "Dockerfile.worker"
        Worker_Base[node:20-alpine]
        Worker_Deps[npm install]
        Worker_App[Copy Workers]
        Worker_Run[node dist/index.js]
    end
    
    subgraph "Dockerfile.cron"
        Cron_Base[python:3.11-slim]
        Cron_Deps[Install Dependencies]
        Cron_Scripts[Copy Scripts]
        Cron_Run[cron + backup_pg.sh]
    end
    
    API_Base --> API_Deps --> API_App --> API_Run
    Worker_Base --> Worker_Deps --> Worker_App --> Worker_Run
    Cron_Base --> Cron_Deps --> Cron_Scripts --> Cron_Run
```

---

## Data Flow Diagrams

### Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant GitHub
    participant Supabase
    
    User->>Frontend: Click "Login with GitHub"
    Frontend->>API: GET /auth/github
    API->>API: Generate state (CSRF token)
    API->>API: Store state in session
    API-->>Frontend: Redirect to GitHub
    Frontend->>GitHub: OAuth authorize URL
    
    User->>GitHub: Authorize app
    GitHub-->>Frontend: Redirect to callback?code=...&state=...
    Frontend->>API: GET /auth/github/callback?code&state
    API->>API: Verify state matches session
    
    API->>GitHub: Exchange code for token
    GitHub-->>API: access_token
    
    API->>API: Encrypt token (AES-256-GCM)
    API->>Supabase: Store encrypted token
    API->>Supabase: Create/update user
    API->>API: Generate JWT session
    API-->>Frontend: Set HttpOnly cookie + redirect
    
    Frontend->>User: Redirect to dashboard
```

### Webhook Processing Flow

```mermaid
sequenceDiagram
    participant GitHub
    participant API
    participant Queue
    participant Worker
    participant Supabase
    
    GitHub->>API: POST /webhooks/github
    Note over API: X-Hub-Signature-256 header
    
    API->>API: Verify HMAC signature
    alt Invalid Signature
        API-->>GitHub: 401 Unauthorized
    end
    
    API->>API: Parse webhook event
    alt push event
        API->>Queue: Enqueue analysis job
        API->>Supabase: Log webhook event
        API-->>GitHub: 202 Accepted
        
        Queue->>Worker: Process job
        Worker->>Supabase: Update job status
        Worker->>GitHub: Fetch changed files
        Worker->>Worker: Analyze changes
        Worker->>Supabase: Store results
    else ping event
        API-->>GitHub: 200 OK
    end
```

### AI Request Flow

```mermaid
flowchart TB
    Start[Worker: AI Request] --> Estimate{Token<br/>Estimation}
    
    Estimate -->|> 1M tokens| Reject[Reject: Context Too Large]
    Estimate -->|OK| Quota{Quota<br/>Check}
    
    Quota -->|Over Limit| Queue[Re-queue with Delay]
    Quota -->|OK| Circuit{Circuit<br/>Breaker}
    
    Circuit -->|Open| Fallback[Return Cached/Error]
    Circuit -->|Closed| Request[Send to Gemini]
    
    Request --> Response{Response}
    Response -->|Success| Parse[Parse Results]
    Response -->|Rate Limited| Backoff[Exponential Backoff]
    Response -->|Error| Increment[Increment Failure Count]
    
    Backoff --> Request
    Increment --> Check{Failure<br/>Threshold?}
    Check -->|Yes| OpenCircuit[Open Circuit]
    Check -->|No| Raise[Raise Exception]
    OpenCircuit --> Raise
    
    Parse --> Store[Store in Database]
    Store --> Complete[Job Complete]
    
    Fallback --> Raise
    Raise --> Retry{Retry<br/>Available?}
    Retry -->|Yes| Queue
    Retry -->|No| DeadLetter[Dead Letter Queue]
```

---

## Security Architecture

### Multi-Layer Security Model

```mermaid
flowchart TB
    subgraph "Layer 1: Network"
        HTTPS[HTTPS Everywhere]
        CORS[CORS Restrictions]
        WAF[WAF Rules]
    end
    
    subgraph "Layer 2: Authentication"
        OAuth[GitHub OAuth2]
        JWT[JWT Sessions]
        CSRF[CSRF Protection]
    end
    
    subgraph "Layer 3: Authorization"
        RLS[Row-Level Security]
        OrgIsolation[Organization Isolation]
        APIPerms[API Permissions]
    end
    
    subgraph "Layer 4: Data Protection"
        Encrypt[Token Encryption<br/>AES-256-GCM]
        WebhookVerify[Webhook Verification<br/>HMAC-SHA256]
        Secrets[Secrets Management]
    end
    
    subgraph "Layer 5: Monitoring"
        Audit[Audit Logging]
        Alerts[Security Alerts]
        Errors[Error Tracking]
    end
    
    HTTPS --> OAuth --> RLS --> Encrypt --> Audit
    CORS --> JWT --> OrgIsolation --> WebhookVerify --> Alerts
    WAF --> CSRF --> APIPerms --> Secrets --> Errors
```

### Row-Level Security Implementation

```mermaid
flowchart LR
    subgraph "Request"
        A[User Request<br/>with JWT]
    end
    
    subgraph "API Layer"
        B[Extract user_id<br/>from JWT]
        C[Set session<br/>variable]
    end
    
    subgraph "Database"
        D[RLS Policy<br/>Check]
        E[Return only<br/>authorized rows]
    end
    
    A --> B --> C --> D --> E
    
    subgraph "RLS Policy Example"
        Policy["CREATE POLICY org_isolation ON repositories<br/>
                USING (organization_id IN (<br/>
                  SELECT organization_id FROM org_members<br/>
                  WHERE user_id = current_setting('request.jwt.claims.user_id')::uuid<br/>
                ))"]
    end
```

---

## Scaling Architecture

### Horizontal Scaling Strategy

```mermaid
flowchart TB
    subgraph "Load Balancer"
        LB[Railway Load Balancer]
    end
    
    subgraph "API Pool"
        API1[API 1]
        API2[API 2]
        API3[API 3]
    end
    
    subgraph "Worker Pool"
        W1[Worker 1]
        W2[Worker 2]
        W3[Worker 3]
        W4[Worker 4]
        W5[Worker 5]
    end
    
    subgraph "Shared Resources"
        Redis[(Redis)]
        DB[(Supabase)]
    end
    
    LB --> API1
    LB --> API2
    LB --> API3
    
    API1 --> Redis
    API2 --> Redis
    API3 --> Redis
    
    Redis --> W1
    Redis --> W2
    Redis --> W3
    Redis --> W4
    Redis --> W5
    
    W1 --> DB
    W2 --> DB
    W3 --> DB
    W4 --> DB
    W5 --> DB
    
    API1 --> DB
    API2 --> DB
    API3 --> DB
```

### Auto-Scaling Triggers

```mermaid
flowchart LR
    subgraph "Metrics"
        CPU[CPU > 70%]
        Memory[Memory > 80%]
        QueueDepth[Queue Depth > 100]
        Latency[P99 Latency > 500ms]
    end
    
    subgraph "Actions"
        ScaleUp[Scale Up]
        ScaleDown[Scale Down]
        Alert[Send Alert]
    end
    
    CPU --> ScaleUp
    Memory --> ScaleUp
    QueueDepth --> ScaleUp
    Latency --> ScaleUp
    
    CPU -->|< 30% for 10m| ScaleDown
    QueueDepth -->|< 10 for 10m| ScaleDown
```

### Database Connection Pooling

```mermaid
flowchart LR
    subgraph "Application Instances"
        A1[API 1]
        A2[API 2]
        A3[API 3]
        W1[Workers]
    end
    
    subgraph "Connection Pool"
        Pool[PgBouncer<br/>Pool Size: 100]
    end
    
    subgraph "Supabase"
        DB[(PostgreSQL<br/>Max Connections: 200)]
    end
    
    A1 --> Pool
    A2 --> Pool
    A3 --> Pool
    W1 --> Pool
    
    Pool --> DB
```

---

## Summary

This architecture documentation covers the complete system design from high-level components to detailed data flows. Key architectural decisions include:

1. **Event-Driven Processing**: Async job queues for long-running AI operations
2. **Defense-in-Depth Security**: Multiple layers from network to data protection
3. **Horizontal Scalability**: Stateless services with shared Redis/Postgres
4. **Resilience Patterns**: Circuit breakers, retries with backoff, dead letter queues
5. **Observable Operations**: Structured logging, health probes, real-time monitoring

For operational procedures, see [../ops/runbook.md](../ops/runbook.md).  
For architectural decisions rationale, see [staff-overview.md](./staff-overview.md).