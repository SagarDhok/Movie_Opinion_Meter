import time
from movies.models import Movie, Cast, Crew, Person
from .client import fetch_movie_full, fetch_person_details



def get_or_create_person(tmdb_person_id, raw):
    person, created = Person.objects.get_or_create(
        tmdb_id=tmdb_person_id,
        defaults={
            "name": raw.get("name", ""),
            "profile_path": raw.get("profile_path"),
            "known_for_department": raw.get("known_for_department", ""),
        },
    )

    if created or not person.biography:
        details = fetch_person_details(tmdb_person_id)

        person.biography = details.get("biography", "")
        person.birthday = details.get("birthday") or None
        person.place_of_birth = details.get("place_of_birth") or ""

  

        person.save()

    return person


def sync_cast_and_crew(limit=50):
    movies = Movie.objects.all()[:limit]

    for movie in movies:
        data = fetch_movie_full(movie.tmdb_id)

        Cast.objects.filter(movie=movie).delete()
        Crew.objects.filter(movie=movie).delete()

        credits = data.get("credits", {})

        for c in credits.get("cast", [])[:12]:
            person = get_or_create_person(c["id"], c)
            Cast.objects.create(
                movie=movie,
                person=person,
                character=c.get("character", ""),
            )

        for c in credits.get("crew", []):
            if c.get("job") in ["Director", "Producer", "Writer"]:
                person = get_or_create_person(c["id"], c)
                Crew.objects.create(
                    movie=movie,
                    person=person,
                    job=c.get("job"),
                )

        time.sleep(0.6)  
