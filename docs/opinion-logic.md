# Opinion Aggregation Logic

This document explains how Movie Opinion Meter captures, stores, and calculates audience opinions. The opinion system is the core backend feature of this project.

## Overview

Movie Opinion Meter uses two distinct voting systems:

1. **Opinion Meter** (Released Movies): 4-category voting
2. **Hype Meter** (Upcoming Movies): Binary excitement voting

This separation reflects a fundamental insight: pre-release hype differs from post-release opinion.

---

## Opinion Meter (Released Movies)

### Vote Categories

```python
VOTE_CHOICES = [
    ("bad", "Bad"),
    ("average", "Average"),
    ("good", "Good"),
    ("masterpiece", "Masterpiece"),
]
```

**Why 4 categories?**
- More nuanced than binary like/dislike
- Less granular than 10-point scale (avoids analysis paralysis)
- Maps to natural language ("was it good?" → "bad/average/good/masterpiece")

**Alternative considered:** 5-star rating
**Rejected because:** Stars imply a continuous scale. These are discrete categories with semantic meaning.

### Data Capture

**Model:**
```python
class MovieVote(models.Model):
    user = ForeignKey(User)
    movie = ForeignKey(Movie)
    vote = CharField(choices=VOTE_CHOICES)
    created_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ("user", "movie")
```

**Constraint:** One vote per user per movie (database-enforced)

**Vote Submission Flow:**

```
1. User clicks "Good" button
   ↓
2. POST /movie/{id}/vote/ (vote="good")
   ↓
3. View validates vote choice
   ↓
4. MovieVote.objects.update_or_create(
       user=request.user,
       movie=movie,
       defaults={"vote": vote}
   )
   ↓
5. If existing vote → update
   If no vote → create
   ↓
6. Redirect to detail page
```

**Why update_or_create?**
- Handles both new votes and vote changes
- Atomic operation (no race condition)
- Relies on unique constraint

**Vote Removal:**
- User can click same category again to remove vote
- JavaScript detects this (button already selected)
- Sends `vote="remove"` to backend
- View calls `.delete()` on vote object

### Aggregation Logic

**Calculation Pattern:**

```python
# 1. Group votes by category
vote_stats = MovieVote.objects.filter(movie=movie)\
    .values("vote")\
    .annotate(count=Count("id"))

# Results: [
#   {"vote": "good", "count": 3},
#   {"vote": "bad", "count": 1},
# ]

# 2. Convert to dictionary
vote_counts = {x["vote"]: x["count"] for x in vote_stats}

# 3. Ensure all categories present
for key in ["bad", "average", "good", "masterpiece"]:
    vote_counts.setdefault(key, 0)

# 4. Calculate total
total_votes = sum(vote_counts.values())

# 5. Calculate percentages
vote_percents = {
    "bad": round((vote_counts["bad"] / total_votes) * 100) if total_votes > 0 else 0,
    # ... repeat for each category
}
```

**Why round()?** UI displays percentages as integers (73%, not 73.4285%)

**Why setdefault()?** Ensure all categories exist in dict even if count is 0 (prevents KeyError in template)

**Performance:** Single database query with GROUP BY and COUNT

**Alternative considered:** Store percentages in Movie model
**Rejected because:**
- Percentages change on every vote (constant updates)
- Recalculating on read is fast enough
- Avoids cache invalidation complexity

### Display Logic

**Template receives:**
```python
context = {
    "vote_counts": {"bad": 5, "average": 12, "good": 28, "masterpiece": 15},
    "vote_percents": {"bad": 8, "average": 20, "good": 47, "masterpiece": 25},
    "total_votes": 60,
    "user_vote": "good"  # Current user's vote (or empty string)
}
```

**UI renders:**
```
Opinion Meter
━━━━━━━━━━━━━━━━━━━━━━━

Bad
[████░░░░░░░░░░░░░░░░░]  8%

Average  
[█████████░░░░░░░░░░░░] 20%

Good ← (user voted this)
[███████████████░░░░░░] 47%

Masterpiece
[███████████░░░░░░░░░░] 25%

Total Votes: 60
```

**Frontend Logic:**
- Selected category has visual highlight
- Clicking selected category sends "remove" vote
- Progress bar width set via CSS variable: `--w: 47%`

---

## Hype Meter (Upcoming Movies)

### Vote Categories

```python
VOTE_CHOICES = [
    ("excited", "Excited"),
    ("not_excited", "Not Excited"),
]
```

**Why binary?**
- Pre-release: Intent is simpler than opinion
- "Will I watch this?" is yes/no decision
- Reduces cognitive load (too early for 4 categories)

### Eligibility Check

```python
if movie.is_released:
    return error("Hype voting is only for upcoming movies")
```

**Enforced at:** Application level (view logic)

**Why not database constraint?** 
- Would require CHECK constraint or trigger (complex)
- View-level check is sufficient (all writes go through views)

**Future improvement:** Database trigger to prevent direct SQL inserts

### Hype Score Calculation

**Definition:** Percentage of voters who selected "Excited"

```python
# Method 1: Application-level calculation (in utils.py)
def attach_hype_score(objects):
    for obj in objects:
        excited = obj.excited_count  # From annotation
        total = obj.total_hype_votes  # From annotation
        obj.hype_score = round((excited / total) * 100) if total > 0 else 0
    return objects
```

**Method 2: Database-level calculation (in views):**
```python
Movie.objects.annotate(
    excited_count=Count("hype_votes", filter=Q(hype_votes__vote="excited")),
    total_hype_votes=Count("hype_votes"),
    hype_score=Case(
        When(
            total_hype_votes__gt=0,
            then=F("excited_count") * 100.0 / F("total_hype_votes")
        ),
        default=Value(0.0),
        output_field=FloatField()
    )
)
```

**Why two methods?**
- Method 1: Simple, readable, Python-land
- Method 2: Faster (no loop), database does math

**Current usage:** Method 2 in "most hyped" section (sorting by score), Method 1 elsewhere

### Hype Score vs Vote Percentages

**Difference:**

**Opinion Meter:** Shows all 4 percentages
```python
{"bad": 8%, "average": 20%, "good": 47%, "masterpiece": 25%}
```

**Hype Meter:** Shows single score
```python
hype_score = 73  # 73% excited
```

**Why?**
- Hype is unidimensional (excitement level)
- Single number is easier to rank ("most hyped movies")
- UI shows breakdown in tooltip if user hovers

---

## Sorting & Ranking

### Most Voted Movies (Trending)

```python
trending_movies = Movie.objects\
    .filter(is_released=True)\
    .annotate(vote_count=Count("votes"))\
    .filter(vote_count__gt=0)\
    .order_by("-vote_count", "-release_date")[:12]
```

**Logic:**
- Count total votes (any category)
- Exclude movies with 0 votes
- Sort by descending vote count
- Tie-breaker: newer movies first
- Limit to 12 results

**Why not weight by category?** 
- Volume indicates engagement, not quality
- "Trending" = "people are talking about it" (even if votes are "bad")

### Most Hyped Movies

```python
hyped_movies = Movie.objects\
    .filter(is_released=False)\
    .annotate(
        excited_count=Count("hype_votes", filter=Q(hype_votes__vote="excited")),
        total_hype_votes=Count("hype_votes"),
        hype_score=ExpressionWrapper(
            F("excited_count") * 100.0 / F("total_hype_votes"),
            output_field=FloatField()
        )
    )\
    .filter(total_hype_votes__gt=0)\
    .order_by("-hype_score", "-total_hype_votes", "release_date")[:12]
```

**Sorting Priority:**
1. **Hype score** (percentage excited)
2. **Total votes** (tie-breaker: 90% of 100 votes beats 90% of 10 votes)
3. **Release date** (sooner releases first)

**Why 3-level sort?**
- Percentage ensures high excitement ranks first
- Volume prevents flukes (1 excited vote = 100% but meaningless)
- Date ensures upcoming movies don't stagnate

---

## Edge Cases Handled

### Division by Zero

**Problem:** `hype_score = excited / total` fails if `total == 0`

**Solution:**
```python
hype_score = round((excited / total) * 100) if total > 0 else 0
```

**Database version:**
```python
Case(When(total_hype_votes__gt=0, then=...), default=Value(0.0))
```

### Vote on Unreleased Movie with Opinion Meter

**Problem:** User tries to POST `/movie/123/vote/` (opinion vote) on upcoming movie

**Current behavior:** Allowed (no check in `vote_movie` view)

**Impact:** Data is stored but not displayed (template shows opinion meter only if `movie.is_released`)

**Should this be prevented?** Debatable.
- **Pro:** Cleaner data
- **Con:** Fails silently in current implementation

**Recommendation:** Add check:
```python
if not movie.is_released:
    return error("Opinion voting available after release")
```

### Hype Vote on Released Movie

**Problem:** User tries to POST `/movie/123/hype/` on released movie

**Current behavior:** Prevented
```python
if movie.is_released:
    messages.error(request, "Hype voting is only for upcoming movies.")
    return redirect(...)
```

**Why block?** Hype becomes irrelevant after release (opinion meter replaces it)

### Vote Update vs Create

**Problem:** User voted "good", now clicks "masterpiece"

**Behavior:** Vote updated (not duplicate created)

**Implementation:** `update_or_create` relies on `unique_together` constraint

**Database guarantees:** Even if two requests race, second throws IntegrityError (caught and retried)

### Vote Removal Idempotency

**Problem:** User clicks "remove vote" twice

**Behavior:**
```python
deleted_count = MovieVote.objects.filter(user=user, movie=movie).delete()[0]
if deleted_count:
    messages.success("Vote removed")
else:
    # No message (vote already didn't exist)
```

**No error:** Idempotent operation (safe to retry)

---

## Review Ratings vs Opinion Votes

**Question:** Why separate reviews (1-5 stars) from opinion votes (bad/average/good/masterpiece)?

**Answer:** Different purposes.

**Opinion Votes:**
- Quick, one-click engagement
- Anonymous aggregate (no authorship shown)
- Focus on distribution ("47% say good")
- Social proof mechanism

**Reviews:**
- In-depth, written feedback
- Attributed to user (shows email/name)
- Personal rating (1-5 stars) + text
- Content-driven, not just sentiment

**Analogy:**
- Opinion vote = Amazon's "X% of customers recommend"
- Review = Amazon's written reviews with star rating

**Can user do both?** Yes. They're complementary.

---

## Opinion Data in API

### GET /api/movies/{id}/

**Response includes:**
```json
{
  "id": 1,
  "title": "Inception",
  "is_released": true
  // ... but NO opinion stats
}
```

**Why not include vote percentages?**
- Would require annotation (expensive for list view)
- Not always needed (depends on client)

**Future:** Add `/api/movies/{id}/opinions/` endpoint for stats

### Custom Endpoint for Opinion Stats

**Proposed Design:**
```
GET /api/movies/{id}/opinions/
```

**Response:**
```json
{
  "total_votes": 60,
  "breakdown": {
    "bad": {"count": 5, "percent": 8},
    "average": {"count": 12, "percent": 20},
    "good": {"count": 28, "percent": 47},
    "masterpiece": {"count": 15, "percent": 25}
  }
}
```

**Why separate endpoint?** 
- Not all clients need it (separation of concerns)
- Cacheable independently

---

## Performance Optimization

### Current Performance

**Query count for movie detail page:**
- 1 query: Movie with prefetch (categories, cast, crew)
- 1 query: Vote aggregation
- 1 query: Review list with likes annotation
- **Total:** ~3-5 queries

**Speed:** Fast enough for expected load (<100ms)

### If Scaling Required

**Bottleneck:** Vote aggregation on every page load

**Solution 1: Cache votes in Redis**
```python
cache_key = f"movie:{movie_id}:vote_stats"
stats = cache.get(cache_key)
if not stats:
    stats = calculate_vote_stats(movie)
    cache.set(cache_key, stats, timeout=300)  # 5 min
```

**Invalidation:** Set cache on vote create/update/delete

**Tradeoff:** Adds complexity, requires Redis

**Solution 2: Materialized view**
```sql
CREATE MATERIALIZED VIEW movie_opinion_stats AS
SELECT movie_id, vote, COUNT(*) as count
FROM movies_movievote
GROUP BY movie_id, vote;
```

**Refresh:** Periodically or on write

**Tradeoff:** Stale data (eventual consistency)

**Current decision:** Neither. Premature optimization.

---

## Testing Opinion Logic

### Unit Tests

**Vote aggregation:**
```python
def test_vote_percentages():
    movie = Movie.objects.create(...)
    MovieVote.objects.create(user=u1, movie=movie, vote="good")
    MovieVote.objects.create(user=u2, movie=movie, vote="good")
    MovieVote.objects.create(user=u3, movie=movie, vote="bad")
    
    stats = calculate_vote_stats(movie)
    assert stats["good"] == 67  # 2/3 rounded
    assert stats["bad"] == 33
```

**Hype score:**
```python
def test_hype_score():
    movies = Movie.objects.annotate(...).all()
    scored = attach_hype_score(movies)
    assert scored[0].hype_score == 75  # Depends on test data
```

### Integration Tests

**Vote update:**
```python
def test_vote_update():
    client.post("/movie/1/vote/", {"vote": "good"})
    client.post("/movie/1/vote/", {"vote": "masterpiece"})
    
    vote = MovieVote.objects.get(user=user, movie=movie)
    assert vote.vote == "masterpiece"
    assert MovieVote.objects.count() == 1  # Not 2
```

**Edge case (division by zero):**
```python
def test_zero_votes():
    movie = Movie.objects.create(...)
    stats = calculate_vote_stats(movie)
    assert stats["good"] == 0  # No error
```

---

## Conclusion

The opinion aggregation system demonstrates:

**Backend Skills:**
- Data modeling (separate tables for different vote types)
- Aggregation queries (GROUP BY, COUNT, conditional aggregation)
- Constraint usage (unique_together)
- Business logic implementation (eligibility checks, percentage calculation)
- Edge case handling (division by zero, idempotency)

**Design Thinking:**
- Separating pre-release hype from post-release opinion
- Choosing appropriate granularity (4 categories vs binary)
- Balancing simplicity (calculate on read) with performance (query optimization)
- Documenting tradeoffs (caching vs. freshness)

This is the core backend feature that makes Movie Opinion Meter distinct from a generic review site.
