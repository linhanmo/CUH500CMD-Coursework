import sys
import os
import random
import difflib


def binary_search(pairs, actor):
    low, high = 0, len(pairs) - 1
    result = -1
    while low <= high:
        mid = (low + high) // 2
        mid_actor = pairs[mid][0]
        if mid_actor == actor:
            result = mid
            high = mid - 1
        elif mid_actor < actor:
            low = mid + 1
        else:
            high = mid - 1
    return result


def collect_films_for_actor(pairs, actor, start_index):
    films = []
    seen = set()
    i = start_index
    while i < len(pairs) and pairs[i][0] == actor:
        film = pairs[i][1]
        if film not in seen:
            seen.add(film)
            films.append(film)
        i += 1
    return films


def get_unique_actors(pairs):
    unique = []
    prev = None
    for actor, _ in pairs:
        if actor != prev:
            unique.append(actor)
            prev = actor
    return unique


def get_films_for_actor(pairs, actor):
    films = []
    seen = set()
    for a, f in pairs:
        if a == actor and f not in seen:
            seen.add(f)
            films.append(f)
    return films


def get_actors_for_film(pairs, film):
    actors = set()
    for a, f in pairs:
        if f == film:
            actors.add(a)
    return sorted(actors)


def fuzzy_lookup(pairs, query):
    actors = get_unique_actors(pairs)
    films = list({f for _, f in pairs})

    actor_matches = difflib.get_close_matches(query, actors, n=1, cutoff=0.6)
    film_matches = difflib.get_close_matches(query, films, n=1, cutoff=0.6)

    if actor_matches and film_matches:
        actor_score = difflib.SequenceMatcher(None, query, actor_matches[0]).ratio()
        film_score = difflib.SequenceMatcher(None, query, film_matches[0]).ratio()
        if actor_score >= film_score:
            return "actor", actor_matches[0]
        else:
            return "film", film_matches[0]
    elif actor_matches:
        return "actor", actor_matches[0]
    elif film_matches:
        return "film", film_matches[0]
    else:
        return None, None


def lookupActorFilmsOrFilmActors(pairs, query):
    # Exact actor
    idx = binary_search(pairs, query)
    if idx != -1:
        films = collect_films_for_actor(pairs, query, idx)
        return {query: films}

    # Exact film
    actors_for_film = get_actors_for_film(pairs, query)
    if actors_for_film:
        return {query: actors_for_film}

    # Fuzzy match
    match_type, best_match = fuzzy_lookup(pairs, query)

    if match_type == "actor":
        films = get_films_for_actor(pairs, best_match)
        return {best_match: films}

    if match_type == "film":
        actors = get_actors_for_film(pairs, best_match)
        return {best_match: actors}

    # No fuzzy match
    unique_actors = get_unique_actors(pairs)
    if not unique_actors:
        return {query: [], "Random Actor": {}}

    looks_like_actor = query[0:1].isupper() and " " in query

    if looks_like_actor and len(unique_actors) >= 2:
        # Actor not found
        selected = random.sample(unique_actors, 2)
        selected.sort()
        return {a: get_films_for_actor(pairs, a) for a in selected}

    # Film not found
    random_actor = random.choice(unique_actors)
    films = get_films_for_actor(pairs, random_actor)
    return {query: [], "Random Actor": {random_actor: films}}


if __name__ == "__main__":
    pairs1 = [
        ["Brad Pitt", "Fight Club"],
        ["Emma Stone", "La La Land"],
        ["Emma Stone", "Cruella"],
        ["Keanu Reeves", "The Matrix"],
        ["Tom Hanks", "Forrest Gump"],
    ]
    print(lookupActorFilmsOrFilmActors(pairs1, "Emma Stone"))

    pairs2 = [
        ["Anne Hathaway", "Interstellar"],
        ["Anne Hathaway", "Les Misérables"],
        ["Chris Evans", "Captain America"],
        ["Zendaya", "Dune"],
    ]
    print(lookupActorFilmsOrFilmActors(pairs2, "Robert Downey Jr."))

    pairs3 = [
        ["Anne Hathaway", "Interstellar"],
        ["Matthew McConaughey", "Interstellar"],
        ["Jessica Chastain", "Interstellar"],
        ["Chris Evans", "Captain America"],
    ]
    print(lookupActorFilmsOrFilmActors(pairs3, "Interstellar"))

    pairs4 = [["Chris Evans", "Captain America"], ["Zendaya", "Dune"]]
    print(lookupActorFilmsOrFilmActors(pairs4, "Inception"))

    # Misspelt actor name
    print(lookupActorFilmsOrFilmActors(pairs1, "Ema Stone"))
