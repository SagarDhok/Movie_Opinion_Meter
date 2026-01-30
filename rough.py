
#! select_related (SQL JOIN)
# What it does

# select_related performs a SQL JOIN and fetches related objects in the same query.

# Use when relationship is:

# ForeignKey

# OneToOneField

# Example

# Models:

# class Movie(models.Model):
#     director = models.ForeignKey(Person, on_delete=models.CASCADE)


# Query:

# movies = Movie.objects.select_related("director")


# SQL idea:
# SELECT movie.*, person.*
# FROM movie
# JOIN person ON movie.director_id = person.id;


# Access:

# movie.director.name  # NO extra query


# Summary (notes)

# select_related = JOIN

# Best for ForeignKey / OneToOne

# Reduces queries by fetching everything at once



#! prefetch_related (Separate queries + Python join)
# What it does

# prefetch_related runs multiple queries and joins the results in Python, not SQL.

# Use when relationship is:

# ManyToManyField

# Reverse ForeignKey (movie.review_set)

# When JOIN would explode rows

# Example

# Models:

# class Movie(models.Model):
#     categories = models.ManyToManyField(Genre)


# Query:

# movies = Movie.objects.prefetch_related("categories")


# Queries executed:

# SELECT * FROM movie;
# SELECT * FROM genre
# JOIN movie_categories ON genre.id = movie_categories.genre_id;


# Django then maps categories → movies in Python.

# Access:

# movie.categories.all()  # NO extra query

# Key characteristics

# ✅ Avoids N+1

# ✅ Works with ManyToMany

# ❌ Uses more memory

# ❌ Not a single SQL query

# Summary (notes)

# prefetch_related = separate queries

# Used for ManyToMany / reverse relations

# Python-level joining







#! filter() → extract row 

#! order_by() → rearranges rows

#! annotate() → adds columns