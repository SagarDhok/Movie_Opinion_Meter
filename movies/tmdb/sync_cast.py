import time
from django.db import transaction
from movies.models import Movie, Cast, Crew, Person
from .client import fetch_movie_full, fetch_person_details


def get_or_create_person(tmdb_person_id, raw):
    # Step 1: create or fetch person WITHOUT external API
    person, _ = Person.objects.get_or_create(
        tmdb_id=tmdb_person_id,
        defaults={
            "name": raw.get("name", ""),
            "profile_path": raw.get("profile_path"),
            "known_for_department": raw.get("known_for_department", ""),
        },
    )

    # Step 2: fetch extra details SAFELY
    try:
        details = fetch_person_details(tmdb_person_id)
    except Exception:
        # TMDB failed — skip enrichment, keep base person
        return person

    # Step 3: update fields only if empty
    updated = False

    if not person.biography and details.get("biography"):
        person.biography = details["biography"]
        updated = True

    if not person.birthday and details.get("birthday"):
        person.birthday = details["birthday"]
        updated = True

    if not person.place_of_birth and details.get("place_of_birth"):
        person.place_of_birth = details["place_of_birth"]
        updated = True

    if updated:
        person.save(update_fields=["biography", "birthday", "place_of_birth"])

    return person


def sync_cast_and_crew(limit=50):
    movies = Movie.objects.all()[:limit]

    for movie in movies:
        try:
            data = fetch_movie_full(movie.tmdb_id)
        except Exception:
            # Skip movie if TMDB fails
            continue

        credits = data.get("credits", {})

        # Clear old relations first
        Cast.objects.filter(movie=movie).delete()
        Crew.objects.filter(movie=movie).delete()

        # CAST
        for c in credits.get("cast", [])[:12]:
            person = get_or_create_person(c["id"], c)

            Cast.objects.create(
                movie=movie,
                person=person,
                character=c.get("character", ""),
            )

        # CREW (important roles only)
        for c in credits.get("crew", []):
            if c.get("job") in {"Director", "Producer", "Writer"}:
                person = get_or_create_person(c["id"], c)

                Crew.objects.create(
                    movie=movie,
                    person=person,
                    job=c.get("job"),
                )

        # VERY IMPORTANT: slow down
        time.sleep(0.8)
