# Data Model Documentation

This document describes the database schema for Movie Opinion Meter, focusing on relationships, constraints, and design rationale.

## Schema Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         MOVIES                              │
├─────────────────────────────────────────────────────────────┤
│  Movie ←─────→ Genre (many-to-many)                        │
│  Movie ←─────→ Person (through Cast, Crew)                 │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                   USER INTERACTIONS                         │
├─────────────────────────────────────────────────────────────┤
│  User → MovieVote → Movie (opinion meter)                  │
│  User → MovieHypeVote → Movie (hype for upcoming)          │
│  User → MovieReview → Movie                                │
│  User → ReviewLike → MovieReview                           │
│  User → ReviewComment → MovieReview                        │
│  User → Watchlist → Movie                                  │
│  User → AIRequestLog → Movie (optional FK)                 │
└─────────────────────────────────────────────────────────────┘
```

## Core Models

### Movie

**Purpose:** Stores movie metadata synced from TMDB

**Fields:**
```python
tmdb_id          PositiveIntegerField (unique)
title            CharField (indexed)
overview         TextField (nullable)
poster_path      CharField (nullable, TMDB path)
release_date     DateField (indexed, nullable)
is_released      BooleanField (indexed, default=False)
categories       ManyToManyField(Genre)
created_at       DateTimeField (auto)
updated_at       DateTimeField (auto)
```

**Constraints:**
- `tmdb_id` unique: Prevents duplicate syncs
- Indexes on `title`, `release_date`, `is_released`: Common filter fields

**Relationships:**
- Many-to-many with `Genre`
- One-to-many with `Cast` (via `cast` related name)
- One-to-many with `Crew` (via `crew` related name)

**Design Notes:**
- `is_released` flag enables upcoming vs released logic
- `poster_path` stores TMDB path, not full URL (flexibility)
- No runtime, budget, revenue fields (intentionally limited scope)

**Ordering:** `["-release_date"]` (newest first)

---

### Genre

**Purpose:** Movie categories (Action, Drama, etc.)

**Fields:**
```python
name    CharField (unique, max_length=100)
```

**Constraints:**
- Unique name prevents duplicates
- Unique constraint creates implicit database index

**Why separate table?** 
- Normalization (avoid repeated strings)
- Many-to-many relationship with movies
- Enables genre-based filtering

---

### Person

**Purpose:** Actors, directors, crew members

**Fields:**
```python
tmdb_id              IntegerField (unique, indexed)
name                 CharField (indexed)
biography            TextField (blank)
profile_path         CharField (nullable, TMDB path)
known_for_department CharField (e.g., "Acting", "Directing")
birthday             DateField (nullable)
place_of_birth       CharField (nullable)
```

**Constraints:**
- `tmdb_id` unique: One record per TMDB person
- Indexes on `tmdb_id`, `name`: Fast lookups

**Why indexed name?** Search functionality, autocomplete scenarios

---

### Cast

**Purpose:** Links Person to Movie as actor

**Fields:**
```python
movie      ForeignKey(Movie, on_delete=CASCADE)
person     ForeignKey(Person, on_delete=CASCADE)
character  CharField (role name)
```

**Relationships:**
- Many cast members per movie
- Many movies per person

**Why not many-to-many?** Need `character` field (through model required)

**Cascade Delete:** If movie deleted, cast records deleted too (maintains referential integrity)

---

### Crew

**Purpose:** Links Person to Movie as crew (director, producer, etc.)

**Fields:**
```python
movie   ForeignKey(Movie, on_delete=CASCADE)
person  ForeignKey(Person, on_delete=CASCADE)
job     CharField (e.g., "Director", "Producer")
```

**Design Decision:** Separate from `Cast` because:
- Different semantics (role vs job)
- Different display logic in UI
- Cleaner queries (`movie.cast.all()` vs `movie.crew.all()`)

**Alternative considered:** Single `Credit` table with `credit_type` field. Rejected for clarity.

---

## Opinion Models

### MovieVote

**Purpose:** Captures audience opinion on released movies

**Fields:**
```python
user       ForeignKey(User, on_delete=CASCADE)
movie      ForeignKey(Movie, on_delete=CASCADE, related_name="votes")
vote       CharField (choices=VOTE_CHOICES)
created_at DateTimeField (auto)
```

**Vote Choices:**
```python
[
    ("bad", "Bad"),
    ("average", "Average"),
    ("good", "Good"),
    ("masterpiece", "Masterpiece"),
]
```

**Constraints:**
- `unique_together("user", "movie")`: One vote per user per movie

**Why this constraint?** 
- Prevents duplicate votes (data integrity)
- Database enforces business rule
- `update_or_create` relies on this for upsert logic

**Related Name:** `movie.votes.all()` returns QuerySet of votes for a movie

---

### MovieHypeVote

**Purpose:** Captures pre-release excitement for upcoming movies

**Fields:**
```python
user       ForeignKey(User, on_delete=CASCADE)
movie      ForeignKey(Movie, on_delete=CASCADE, related_name="hype_votes")
vote       CharField (choices=VOTE_CHOICES)
created_at DateTimeField (auto)
```

**Vote Choices:**
```python
[
    ("excited", "Excited"),
    ("not_excited", "Not Excited"),
]
```

**Constraints:**
- `unique_together("user", "movie")`

**Why Separate Table from MovieVote?**

**Option 1 (Rejected):** Single table with `vote_type` field
```python
class Vote(models.Model):
    vote = CharField()  # bad/average/good/masterpiece/excited/not_excited
    vote_type = CharField()  # opinion/hype
```

**Problems:**
- Invalid states possible (hype vote on released movie)
- Harder to query ("give me hype votes" needs WHERE clause)
- Business logic scattered

**Option 2 (Chosen):** Separate tables
- Schema enforces validity (hype votes have 2 choices, opinions have 4)
- Clear intent (`MovieHypeVote` is obviously pre-release)
- Easy to add hype-specific fields later (e.g., `will_watch_opening_day`)

**Tradeoff:** More tables, but better data integrity.

---

## Review Models

### MovieReview

**Purpose:** User reviews with rating and text

**Fields:**
```python
user             ForeignKey(User, on_delete=CASCADE)
movie            ForeignKey(Movie, on_delete=CASCADE, related_name="reviews")
rating           PositiveSmallIntegerField (choices=1-5)
review_text      TextField (max 1000 chars, validator)
contains_spoiler BooleanField (default=False)
created_at       DateTimeField (auto)
```

**Constraints:**
- `unique_together("user", "movie")`: One review per user per movie
- `MaxLengthValidator(1000)` on `review_text`: Enforced in DB and forms

**Why max 1000 chars?** 
- Keeps reviews concise
- AI processing limits (prompt size)
- UI design constraint (readability)

**Spoiler Flag:** Allows UI to hide content by default (user experience)

---

### ReviewLike

**Purpose:** Users can like reviews

**Fields:**
```python
user       ForeignKey(User, on_delete=CASCADE)
review     ForeignKey(MovieReview, on_delete=CASCADE, related_name="likes")
created_at DateTimeField (auto)
```

**Constraints:**
- `unique_together("user", "review")`: One like per user per review

**Design Decision:** No "dislike" feature (intentionally simpler, less negative)

**Related Usage:**
```python
review.likes.count()  # Total likes
review.likes.filter(user=request.user).exists()  # Did current user like?
```

---

### ReviewComment

**Purpose:** Nested comments on reviews (1 level deep)

**Fields:**
```python
user       ForeignKey(User, on_delete=CASCADE)
review     ForeignKey(MovieReview, on_delete=CASCADE, related_name="comments")
parent     ForeignKey("self", on_delete=CASCADE, nullable, related_name="replies")
text       TextField
created_at DateTimeField (auto)
```

**Self-Referential FK:** `parent` points to another `ReviewComment` for threading

**Constraints:**
- `parent` nullable: Top-level comments have `parent=None`
- Cascading delete: If parent deleted, replies deleted too

**Threading Depth:** Enforced at application level (view checks `parent.parent_id is None`)

**Why limit to 1 level?**
- Deep threads are hard to render
- Reduces complexity
- Sufficient for "comment → reply" use case

**Query Pattern:**
```python
# Top-level comments
comments = ReviewComment.objects.filter(review=review, parent__isnull=True)

# Prefetch replies (avoid N+1)
comments = comments.prefetch_related("replies")
```

---

## Utility Models

### Watchlist

**Purpose:** User's saved movies

**Fields:**
```python
user       ForeignKey(User, on_delete=CASCADE, related_name="watchlist_items")
movie      ForeignKey(Movie, on_delete=CASCADE, related_name="watchlisted_by")
created_at DateTimeField (auto)
```

**Constraints:**
- `unique_together("user", "movie")`: Movie appears once in user's watchlist

**Why created_at?** Sort by "recently added" order

**Alternative Considered:** Many-to-many field on User model
```python
class User:
    watchlist = ManyToManyField(Movie)
```

**Rejected because:**
- Can't add `created_at` to M2M without through model
- Explicit model is clearer for querying

---

### AIRequestLog

**Purpose:** Audit trail for AI feature usage

**Fields:**
```python
user          ForeignKey(User, on_delete=CASCADE)
movie         ForeignKey(Movie, on_delete=SET_NULL, nullable)
action        CharField (choices=ACTION_CHOICES)
input_text    TextField
output_text   TextField (blank)
success       BooleanField (default=False)
error_message CharField (blank, max 255)
created_at    DateTimeField (auto)
```

**Action Choices:**
```python
[
    ("rewrite", "Rewrite"),
    ("shorten", "Shorten"),
    ("funny", "Funny"),
    ("roast", "Roast"),
    ("professional", "Professional"),
    ("hype", "Hype"),
    ("savage_1star", "Savage 1-Star"),
    ("pros_cons", "Pros & Cons"),
]
```

**Why Log Failures?**
- Debug AI errors (see exact input that failed)
- Monitor success rate
- Detect abuse patterns

**Why SET_NULL on movie?**
- If movie deleted, keep logs for analytics
- Movie context not critical for log record

**Privacy Note:** Stores user input text. In production, consider data retention policy.

---

## Indexes Strategy

**Explicit Indexes (defined in models):**
- `Movie.title`
- `Movie.release_date`
- `Movie.is_released`
- `Person.name`

**Implicit Indexes (Django creates automatically):**
- Primary keys
- Foreign keys
- Unique fields

**Why these fields?**
- `title`: Search queries (`WHERE title ILIKE '%query%'`)
- `release_date`: Sorting, recent movies queries
- `is_released`: Filter movies by status (common)
- `name`: Person search/autocomplete

**Future Optimization:** Composite index on `(is_released, release_date)` if filtering both frequently.

---

## Database Constraints

### Unique Constraints
```python
# Genre.name
# Movie.tmdb_id
# Person.tmdb_id
# (User, Movie) in MovieVote, MovieHypeVote, MovieReview, Watchlist
# (User, Review) in ReviewLike
```

**Why at database level?**
- Prevents race conditions (two simultaneous inserts)
- Faster than application-level check (single query)
- Enforced even if code bypasses ORM

### Cascading Deletes
```python
# If Movie deleted → all votes, reviews, watchlist entries deleted
# If Review deleted → all likes, comments deleted
# If Comment deleted → all replies deleted
```

**Why CASCADE?**
- Orphaned records are meaningless (review without movie)
- Automatic cleanup
- Maintains referential integrity

**Exception:** `AIRequestLog.movie` uses `SET_NULL` (preserve logs)

---

## Schema Evolution

**Current Migration Count:** 17 migrations

**Notable Changes:**
- Added `MovieHypeVote` (migration 0012)
- Added `ReviewComment.parent` for threading (migration 0011)
- Added `AIRequestLog` (migration 0015)
- Removed unused indexes (migration 0017)

**Why many migrations?**
- Iterative development (features added incrementally)
- Database-first approach (models drive schema)

**Best Practice:** Squash migrations before production deployment (reduces migration count)

---

## Query Patterns

### Efficient Vote Aggregation

**Naive (N+1 queries):**
```python
for movie in movies:
    print(movie.votes.count())  # Query per movie
```

**Optimized (single query):**
```python
movies = Movie.objects.annotate(vote_count=Count("votes"))
for movie in movies:
    print(movie.vote_count)  # No query, uses annotation
```

### Prefetching Related Data

**Reviews with user info:**
```python
reviews = MovieReview.objects.select_related("user", "movie")
# One query with JOIN instead of 1 + N
```

**Movies with genres:**
```python
movies = Movie.objects.prefetch_related("categories")
# Two queries total: movies, then genres
```

### Conditional Aggregation

**Hype score calculation:**
```python
Movie.objects.annotate(
    excited_count=Count("hype_votes", filter=Q(hype_votes__vote="excited")),
    total_hype_votes=Count("hype_votes")
)
# Single query with conditional COUNT
```

---

## Schema Normalization

**Normal Forms Achieved:**

**1NF (First Normal Form):** ✅
- All fields atomic (no arrays)

**2NF (Second Normal Form):** ✅
- No partial dependencies (composite key tables like Cast have only key-dependent fields)

**3NF (Third Normal Form):** ✅
- No transitive dependencies (e.g., `hype_score` calculated, not stored)

**Why not denormalize?**
- Data volume doesn't justify it
- Normalized schema is easier to reason about
- Aggregations are fast enough

**Future Denormalization Candidates:**
- Cache `vote_count` on Movie (if aggregation becomes bottleneck)
- Cache `like_count` on MovieReview (currently annotated)

---

## Data Integrity Philosophy

**Database-Enforced Rules:**
- Uniqueness (votes, reviews)
- Referential integrity (foreign keys)
- Non-null requirements

**Application-Enforced Rules:**
- Comment threading depth (1 level)
- Hype votes only on unreleased movies
- Review text length (also has DB validator)
- AI rate limiting

**Why split?**
- Database handles what it does best (constraints)
- Application handles business logic (complex rules)

---

## Testing Database Logic

**Key Tests to Write:**

1. **Constraint Violations:**
```python
# Should raise IntegrityError
MovieVote.objects.create(user=user1, movie=movie1, vote="good")
MovieVote.objects.create(user=user1, movie=movie1, vote="bad")  # Error!
```

2. **Cascading Deletes:**
```python
review = MovieReview.objects.create(...)
ReviewLike.objects.create(review=review, user=user1)
review.delete()
assert ReviewLike.objects.count() == 0  # Cascade worked
```

3. **Query Optimization:**
```python
with self.assertNumQueries(1):
    movies = list(Movie.objects.prefetch_related("categories"))
```

---

## Conclusion

This schema demonstrates:
- **Normalization principles** (avoiding redundancy)
- **Constraint usage** (enforcing business rules)
- **Relationship modeling** (one-to-many, many-to-many, self-referential)
- **Query optimization awareness** (indexes, prefetching)
- **Intentional limitations** (simple is better than complex)

For a portfolio project, this schema is well-designed and interview-ready. It shows understanding of relational database fundamentals without over-engineering.
