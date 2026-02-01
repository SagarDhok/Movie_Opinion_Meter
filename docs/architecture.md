# Architecture Overview

This document explains the backend architecture of Movie Opinion Meter, focusing on separation of concerns, data flow, and integration patterns.

## Application Structure

```
movie_opinion_meter/
├── movies/                 # Core app
│   ├── views.py           # Traditional Django views (templates)
│   ├── views_ai.py        # AI-specific endpoints
│   ├── api/
│   │   ├── views.py       # DRF API views
│   │   ├── serializers.py # Data serialization
│   │   └── urls.py        # API routing
│   ├── services/
│   │   └── ai_service.py  # AI business logic
│   ├── tmdb/
│   │   ├── client.py      # TMDB API wrapper
│   │   ├── sync.py        # Movie sync logic
│   │   └── sync_cast.py   # Cast/crew sync logic
│   ├── models.py          # Database models
│   ├── forms.py           # Form validation
│   └── utils.py           # Helper functions
├── users/                  # User management
└── templates/             # HTML templates
```

## Separation of Concerns

### Views Layer
**Responsibility**: Handle HTTP requests, validate input, orchestrate responses

**Implementation:**
- `views.py`: Template-based views for server-side rendering
- `views_ai.py`: Dedicated AI endpoint handlers (rate limiting, logging)
- `api/views.py`: REST API views using Django REST Framework

**Example Pattern** (from `views.py`):
```python
def movie_detail(request, movie_id):
    # 1. Authentication check
    if not request.user.is_authenticated:
        return redirect to login
    
    # 2. Fetch data with query optimization
    movie = get_object_or_404(
        Movie.objects.prefetch_related(
            "categories", "cast__person", "crew__person"
        ),
        id=movie_id
    )
    
    # 3. Aggregate opinion data
    vote_stats = MovieVote.objects.filter(movie=movie)
        .values("vote").annotate(count=Count("id"))
    
    # 4. Prepare context
    context = {...}
    
    # 5. Render response
    return render(request, "movies/detail.html", context)
```

### Business Logic Layer
**Responsibility**: Implement domain-specific rules, calculations, validations

**Key Files:**
- `services/ai_service.py`: AI prompt construction, API calls, fallback logic
- `utils.py`: Hype score calculation
- View methods: Opinion aggregation, review enrichment

**Example: Hype Score Calculation**
```python
def attach_hype_score(objects):
    """Pure function: takes annotated querysets, adds calculated field"""
    for obj in objects:
        excited = getattr(obj, "excited_count", 0)
        total = getattr(obj, "total_hype_votes", 0)
        obj.hype_score = round((excited / total) * 100) if total > 0 else 0
    return objects
```

**Why not in models?** Hype score is derived from annotations, not a stored field. Keeping calculation in utils separates query construction (views) from computation (utils).

### Data Access Layer
**Responsibility**: Define schema, relationships, query interface

**Implementation:** Django ORM models in `models.py`

**Key Patterns:**
- `unique_together` constraints for business rules
- `related_name` for readable reverse queries
- Indexed fields for common filters

### Service Integration Layer
**Responsibility**: Wrap external APIs, handle failures, enforce rate limits

**TMDB Integration (`tmdb/client.py`):**
```python
class TMDBClient:
    def get_movie(self, tmdb_id):
        # Construct URL with API key
        # Make HTTP request
        # Parse JSON response
        # Return normalized data
```

**AI Integration (`services/ai_service.py`):**
- Primary model with fallback
- Prompt construction per mode (rewrite, shorten, etc.)
- JSON parsing for structured output (pros/cons)

## Data Flow Examples

### Opinion Vote Submission

```
1. POST /movie/{id}/vote/ (vote="good")
   ↓
2. vote_movie() view validates vote choice
   ↓
3. MovieVote.objects.update_or_create(user, movie, defaults={vote})
   ↓
4. Database constraint ensures one vote per user+movie
   ↓
5. Redirect to detail page
   ↓
6. movie_detail() aggregates all votes for percentages
   ↓
7. Render meter with updated stats
```

**Key Decision:** Vote aggregation happens on read, not write. We don't cache percentages—we recalculate on every detail page load. This keeps logic simple and data consistent.

### Review with AI Assistance

```
1. User writes draft review in textarea
   ↓
2. Clicks "Generate" → POST /movie/{id}/ai/assist/ (mode="funny")
   ↓
3. ai_review_assistant() checks rate limit (10/10min)
   ↓
4. Creates AIRequestLog entry (success=False)
   ↓
5. ai_service.ai_rewrite_review() constructs prompt with movie context
   ↓
6. groq_chat() calls Groq API (primary model, fallback if fails)
   ↓
7. Update log with output, success=True
   ↓
8. Return JSON response to frontend
   ↓
9. JavaScript replaces textarea content
```

**Why log requests?** Debugging AI failures requires seeing exact inputs. Logs also enable usage analytics and rate limit auditing.

## External API Integration

### TMDB (The Movie Database)

**Purpose:** Authoritative movie metadata (titles, posters, release dates, cast)

**Integration Pattern:**
- Management commands (`sync_tmdb_movies`, `sync_tmdb_cast`)
- Runs manually or via scheduled job
- Stores TMDB ID to prevent duplicates
- Fetches paginated results, stores locally

**Why not real-time?** 
- TMDB data changes slowly
- Bulk sync is more efficient than per-request fetching
- Local storage enables offline development

**Code Location:** `movies/tmdb/`

### Groq AI

**Purpose:** Review rewriting and analysis

**Integration Pattern:**
- On-demand API calls (user-triggered)
- Contextual prompts (include movie title/overview)
- Primary/fallback model strategy
- Rate limiting at application level (not API key level)

**Why Groq over OpenAI?** Fast inference for real-time use cases. (This is inferred from code—could be cost, speed, or preference.)

**Code Location:** `movies/services/ai_service.py`

## Why This Architecture?

### Monolithic Django App
**Decision:** Single Django project, not microservices

**Rationale:**
- Complexity doesn't warrant service boundaries
- All features query the same database
- No independent scaling requirements
- Portfolio scope favors simplicity over distributed systems

### Hybrid View Strategy (Templates + API)
**Decision:** Traditional views for core pages, DRF for mobile/AJAX

**Rationale:**
- Template views demonstrate full-stack capability
- API views demonstrate REST design
- Some actions (like review likes) need AJAX responses
- Flexibility for future mobile app without rebuilding backend

### Service Layer for AI
**Decision:** Separate `services/ai_service.py` instead of inline in views

**Rationale:**
- AI logic is complex (prompt building, fallback, retries)
- Reused across multiple views (ai_review_assistant, ai_pros_cons)
- Easier to test in isolation
- Clear dependency: views depend on service, not vice versa

### No Caching Layer
**Decision:** Calculate aggregations on each request

**Rationale:**
- Vote counts change frequently (every vote invalidates cache)
- PostgreSQL aggregations are fast for this data volume
- Cache invalidation adds complexity
- Premature optimization for expected traffic

**Future:** If vote aggregation becomes a bottleneck, cache with Redis and invalidate on writes.

## Query Optimization Strategy

Django ORM can generate inefficient queries (N+1 problem). This project uses:

### select_related (Foreign Keys)
```python
MovieReview.objects.select_related("user", "movie")
# One query with JOIN instead of per-review user lookup
```

### prefetch_related (Many-to-Many, Reverse FKs)
```python
Movie.objects.prefetch_related("categories", "cast__person")
# Separate queries, but only 3 total instead of 1 + N
```

### annotate (Aggregations)
```python
MovieReview.objects.annotate(like_count=Count("likes"))
# Database calculates count, not Python loop
```

**Where to apply:** Any view that displays lists or related objects. Detail pages especially benefit.

## Error Handling Philosophy

**Views:** Redirect with user-friendly message (Django messages framework)

**API Views:** Return JSON with error key and appropriate HTTP status

**External APIs:** Log failure, return fallback or error response (don't crash)

**Example (AI service):**
```python
try:
    return call_model(PRIMARY_MODEL)
except Exception:
    return call_model(FALLBACK_MODEL)  # Graceful degradation
```

## Testing Considerations

*Note: Tests not currently implemented (intentional portfolio scoping)*

**If implementing:**
- Unit tests for `utils.py` functions (pure, no DB)
- Integration tests for vote aggregation logic
- Mock external APIs (TMDB, Groq) in tests
- Test rate limiting with frozen time
- Test unique constraints raise IntegrityError

## Scalability Considerations

**Current bottlenecks (if traffic 100x'd):**
1. Vote aggregation queries on every detail page load
2. AI API response latency (500ms–2s)
3. No CDN for TMDB images

**How to scale:**
- Cache vote percentages in Redis, invalidate on write
- Queue AI requests with Celery for async processing
- Add CDN for static assets and proxied TMDB images
- Database read replicas for queries

**Why not now?** These solutions add operational complexity. Current architecture handles expected load (hundreds of users, not millions).

## Deployment Architecture

*Current setup (inferred from render.yaml):*

```
Render Platform
├── Web Service (Gunicorn)
│   └── Django app
├── PostgreSQL Database
└── Environment Variables
    ├── TMDB_API_KEY
    ├── GROQ_API_KEY
    └── DATABASE_URL
```

**Static Files:** WhiteNoise serves from `staticfiles/`

**Media Files:** Supabase storage (inferred from supabase dependency)

**No task queue:** Management commands run manually or via Render cron jobs

## Conclusion

This architecture prioritizes:
- **Clarity** over cleverness
- **Simplicity** over scalability theater
- **Backend fundamentals** over framework magic

It demonstrates understanding of:
- Layered application design
- Query optimization patterns
- External API integration
- Rate limiting and logging
- Data integrity constraints

For a portfolio project, this architecture is appropriately scoped and well-suited to technical interview discussions.
