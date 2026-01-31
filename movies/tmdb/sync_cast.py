import time
from django.db import transaction
from movies.models import Movie, Cast, Crew, Person
from .client import fetch_movie_full, fetch_person_details


def get_or_create_person(tmdb_person_id, raw):
    person, _ = Person.objects.get_or_create(
        tmdb_id=tmdb_person_id,
        defaults={
            "name": raw.get("name", ""),
            "profile_path": raw.get("profile_path"),
            "known_for_department": raw.get("known_for_department", ""),
        },
    )#person name id char cast name adede in db or get 

    try:
        details = fetch_person_details(tmdb_person_id)#that person s info 
    except Exception:
        return person

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


def sync_cast_and_crew(limit=50):  #why limit 50 if i wnat manual from command then 
    movies = Movie.objects.all()[:limit]
    # [Movie(id=1), Movie(id=2), Movie(id=3)...]


    for movie in movies:
        try:
            data = fetch_movie_full(movie.tmdb_id)
        #       data= {
        #   "id": 101,
        #   "title": "...",
        #   "credits": {
        #      "cast": [...],
        #      "crew": [...]
        #   }
        # }
        except Exception:
            continue

        # "credits": {
        #      "cast": [...],
        #      "crew": [...]
        #   }
        credits = data.get("credits", {})

        Cast.objects.filter(movie=movie).delete()
        Crew.objects.filter(movie=movie).delete()

        for c in credits.get("cast", [])[:12]:
        # c =    {
        #   "id": 287,
        #   "name": "Brad Pitt",
        #   "character": "Tyler Durden"
        # }

            person = get_or_create_person(c["id"], c)

            Cast.objects.create(
                movie=movie,
                person=person,
                character=c.get("character", ""),
            )

        for c in credits.get("crew", []):
            if c.get("job") in {"Director", "Producer", "Writer"}:
                person = get_or_create_person(c["id"], c)

                Crew.objects.create(
                    movie=movie,
                    person=person,
                    job=c.get("job"),
                )

        time.sleep(0.8)
