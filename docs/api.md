# API Documentation

Movie Opinion Meter exposes both traditional Django views (form-based) and RESTful JSON APIs. This document focuses on the REST API layer.

## API Philosophy

**Design Principles:**
- RESTful resource naming (nouns, not verbs)
- HTTP methods convey intent (GET = read, POST = write)
- JSON request/response bodies
- Standard HTTP status codes
- Consistent error response format

**Authentication Strategy:**
- Public endpoints: Movie listings, movie details
- Protected endpoints: Reviews, votes, AI features
- Session-based auth for web, token-ready architecture for future mobile

## Base URL

```
Production: https://movie-opinion-meter.onrender.com
Development: http://localhost:8000
```

## API Endpoints

### Public Endpoints

#### List Movies
```http
GET /api/movies/
```

**Query Parameters:**
- `search` (string): Filter by title
- `genre` (int): Filter by genre ID
- `status` (enum): `released` | `upcoming`

**Response:**
```json
[
  {
    "id": 1,
    "title": "Inception",
    "poster_path": "/path.jpg",
    "release_date": "2010-07-16",
    "is_released": true,
    "categories": [
      {"id": 1, "name": "Action"},
      {"id": 2, "name": "Sci-Fi"}
    ]
  }
]
```

**Notes:**
- Returns all movies matching filters (no pagination yet)
- `poster_path` is TMDB path, prefix with `https://image.tmdb.org/t/p/w500`

---

#### Movie Detail
```http
GET /api/movies/{id}/
```

**Response:**
```json
{
  "id": 1,
  "title": "Inception",
  "overview": "A thief who steals corporate secrets...",
  "poster_path": "/path.jpg",
  "release_date": "2010-07-16",
  "is_released": true,
  "categories": [...]
}
```

---

#### Movie Reviews
```http
GET /api/movies/{movie_id}/reviews/
```

**Response:**
```json
[
  {
    "id": 42,
    "user": "john@example.com",
    "rating": 5,
    "review_text": "Mind-bending masterpiece!",
    "contains_spoiler": false,
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

**Notes:**
- Orders by most recent
- User displayed as email (consider privacy implications in production)

---

### Protected Endpoints

All protected endpoints require authentication. Web app uses session cookies; API clients should use tokens (DRF authentication setup ready).

#### Submit/Update Review
```http
POST /api/movies/{movie_id}/review/
Authorization: Session (automatic for web) or Token
Content-Type: application/json
```

**Request Body:**
```json
{
  "rating": 5,
  "review_text": "Amazing film with incredible visuals.",
  "contains_spoiler": false
}
```

**Response (Success):**
```json
{
  "message": "Review saved successfully"
}
```

**Behavior:**
- Creates new review if user hasn't reviewed this movie
- Updates existing review otherwise (enforced by unique constraint)

**Validation:**
- `rating`: Required, integer 1-5
- `review_text`: Required, max 1000 characters
- `contains_spoiler`: Optional boolean, defaults to false

---

#### AI Review Rewrite
```http
POST /api/movies/{movie_id}/ai/rewrite/
Authorization: Required
Content-Type: application/json
```

**Request Body:**
```json
{
  "text": "good movie nice acting",
  "mode": "professional"
}
```

**Modes:**
- `rewrite`: Clean, polished version
- `shorten`: Compact version (<180 chars)
- `funny`: Humorous take
- `roast`: Playful criticism
- `professional`: Formal tone
- `hype`: Excited, enthusiastic
- `savage_1star`: Brutally negative (filtered for hate speech)

**Response:**
```json
{
  "result": "This film delivers exceptional performances..."
}
```

**Error Response (Rate Limit):**
```json
{
  "error": "Rate limit exceeded"
}
```
HTTP Status: `429 Too Many Requests`

**Rate Limiting:**
- 10 requests per 10 minutes per user per mode
- Enforced in application code, tracked in `AIRequestLog`

---

#### AI Pros/Cons Extraction
```http
POST /api/movies/{movie_id}/ai/pros-cons/
Authorization: Required
Content-Type: application/json
```

**Request Body:**
```json
{
  "text": "Great acting but weak plot. Stunning visuals compensate for pacing issues."
}
```

**Response:**
```json
{
  "pros": ["Great acting", "Stunning visuals"],
  "cons": ["Weak plot", "Pacing issues"]
}
```

**Validation:**
- Minimum 10 characters
- Maximum 1000 characters
- Same rate limiting as AI rewrite

---

### Traditional Form Endpoints (Non-API)

These use POST with form data, return redirects (not JSON).

#### Opinion Vote
```http
POST /movie/{id}/vote/
```

**Form Data:**
- `vote`: `bad` | `average` | `good` | `masterpiece` | `remove`

**Behavior:**
- Updates or creates vote
- `remove` deletes existing vote
- Redirects to movie detail page with flash message

---

#### Hype Vote (Upcoming Movies)
```http
POST /movie/{id}/hype/
```

**Form Data:**
- `vote`: `excited` | `not_excited` | `remove`

**Validation:**
- Returns error if `movie.is_released == True`
- Only upcoming movies can receive hype votes

---

#### Toggle Watchlist
```http
POST /movie/{id}/watchlist/
```

**Behavior:**
- Adds movie to watchlist if not present
- Removes if already in watchlist
- Idempotent toggle operation

---

#### Like Review (AJAX)
```http
POST /reviews/{review_id}/like/
X-Requested-With: XMLHttpRequest
```

**Response:**
```json
{
  "ok": true,
  "liked": true,
  "like_count": 42
}
```

**Frontend Integration:**
JavaScript intercepts form submit, calls this endpoint, updates UI without page reload.

---

## Error Handling

### Standard Error Format (API)

```json
{
  "error": "Error message here"
}
```

### HTTP Status Codes

- `200 OK`: Success
- `400 Bad Request`: Validation error
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Authenticated but not authorized
- `404 Not Found`: Resource doesn't exist
- `405 Method Not Allowed`: Wrong HTTP verb
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server-side failure

### Example Error Responses

**Invalid Vote:**
```http
POST /movie/123/vote/
vote=invalid_choice

→ Redirect with error message (template view)
```

**AI Text Too Long:**
```json
{
  "error": "Review too long"
}
```
HTTP Status: `400`

**Rate Limit Hit:**
```json
{
  "error": "Too many requests. Try later."
}
```
HTTP Status: `429`

---

## Authentication

### Current Implementation
- Django session authentication (cookies)
- Login required decorator on protected views
- DRF `IsAuthenticated` permission on API endpoints

### Token Authentication (Future)
API is ready for token auth. To enable:

1. Add `rest_framework.authtoken` to `INSTALLED_APPS`
2. Run migrations
3. Generate tokens for users
4. Frontend passes `Authorization: Token <key>` header

**Why not now?** Web app doesn't need it. Sessions work fine for server-rendered pages.

---

## Pagination

**Current Status:** No pagination implemented

**Why?** Dataset size doesn't warrant it yet. All movies fit in a single response.

**Future Implementation:**
```python
# api/views.py
from rest_framework.pagination import PageNumberPagination

class MovieListAPIView(APIView):
    pagination_class = PageNumberPagination
```

Would return:
```json
{
  "count": 500,
  "next": "/api/movies/?page=2",
  "previous": null,
  "results": [...]
}
```

---

## CORS Configuration

**Current Setup:** `django-cors-headers` installed

**Purpose:** Allow frontend (if deployed separately) to call API

**Configuration:** In `settings.py`, configure `CORS_ALLOWED_ORIGINS`

**Why needed?** Browser security blocks cross-origin requests by default

---

## API Versioning

**Current Status:** No versioning

**Reasoning:** Single client (own frontend), breaking changes are rare

**If v2 needed:**
```
/api/v1/movies/
/api/v2/movies/
```

Or use header-based versioning:
```http
Accept: application/vnd.moviemeter.v2+json
```

---

## Rate Limiting Details

### Implementation

**Location:** `movies/views_ai.py`

```python
def user_ai_limit_exceeded(user, action, minutes=10, limit=10):
    since = timezone.now() - timedelta(minutes=minutes)
    count = AIRequestLog.objects.filter(
        user=user, 
        action=action, 
        created_at__gte=since
    ).count()
    return count >= limit
```

**Why in application code?** Framework-agnostic, easy to customize per endpoint, enables logging.

**Alternative:** Django-ratelimit library (not used to demonstrate custom implementation)

### Rate Limit Metrics

Tracked in `AIRequestLog`:
- User
- Action (mode)
- Success/failure
- Input/output text
- Timestamp

**Monitoring:** Query logs to identify:
- Most popular AI modes
- Failure rates
- Users hitting limits frequently

---

## Testing the API

### Using curl

**Get Movies:**
```bash
curl http://localhost:8000/api/movies/
```

**Submit Review (requires CSRF token for session auth):**
```bash
curl -X POST http://localhost:8000/api/movies/1/review/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rating": 5, "review_text": "Great!", "contains_spoiler": false}'
```

### Using Postman/Insomnia

1. Create POST request to `/api/movies/{id}/review/`
2. Set Content-Type header to `application/json`
3. Add request body (JSON)
4. If using tokens, add Authorization header

### Using DRF Browsable API

Navigate to `http://localhost:8000/api/movies/` in browser. DRF provides HTML interface for testing.

---

## API Design Decisions

### Why Two API Styles?

**Traditional Views (forms):**
- Simpler for server-rendered pages
- Built-in CSRF protection
- Easier debugging (HTML errors)

**REST API (JSON):**
- Clean for AJAX requests
- Mobile-ready
- Demonstrates REST design skill

Both coexist because they serve different use cases.

### Why JSON for Errors?

API endpoints return JSON errors for machine parsing:
```json
{"error": "message"}
```

Template views redirect with flash messages for human display:
```python
messages.error(request, "message")
```

Consistency within each context.

### Why Not GraphQL?

- Adds complexity (schema, resolvers)
- REST is sufficient for this data model
- N+1 problem solvable with proper prefetch
- Portfolio goal: demonstrate REST proficiency

---

## Conclusion

This API design demonstrates:
- RESTful conventions
- Authentication patterns
- Rate limiting implementation
- Error handling consistency
- AJAX integration

For a portfolio project, this API is appropriately scoped and ready for technical discussion in interviews.
