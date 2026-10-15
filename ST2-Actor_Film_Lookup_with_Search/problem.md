# ASSESSED STANDARD TASK 2/5: Actor Film Lookup with Search

In this activity, you will work with a list of actors and their well-known films, stored as ordered pairs such as:

```text
["Keanu Reeves", "The Matrix"]
```

The list is:

- ⭕ sorted alphabetically by actor name
- ⭕ not sorted by film name
- ⭕ allowed to contain duplicate actors, duplicate films, and actors with multiple films

Your task is to write a function `lookupActorFilmsOrFilmActors` that supports two types of queries:

## When the input is an actor name

- ⭕ Use binary search to locate the **first occurrence** of the actor. (Linear search is not allowed unless binary search fails.)
- ⭕ Once found, scan upward and downward to collect all films for that actor.
- ⭕ If the actor does not appear:
  - ⚫ randomly select two **different** actors
  - ⚫ return all films for both
  - ⚫ return results sorted alphabetically by actor name
  - ⚫ ensure the two actors are distinct even if the list contains duplicates
- ⭕ Actor names are **case-sensitive**.

## When the input is a film title

- ⭕ You must **not** assume the list is sorted by film. Instead, you must:
  - ⚫ scan the entire list
  - ⚫ collect all actors who appear in that film
  - ⚫ return them in alphabetical order
- ⭕ If the film does not appear:
  - ⚫ randomly select one actor
  - ⚫ return all films for that actor
  - ⚫ include a note that the film was not found
- ⭕ Film titles are **case-sensitive**.

## Your function must also

- ⭕ detect whether the input is an actor or a film (You may not assume the caller tells you which type it is.)
- ⭕ handle lists where:
  - ⚫ an actor appears many times
  - ⚫ multiple actors share the same film
  - ⚫ a film appears only once
  - ⚫ only one actor exists in the entire list
  - ⚫ only one film exists in the entire list
- ⭕ avoid building a full dictionary/map in advance. (You may build temporary structures during lookup, but not pre-index the entire list.)
- ⭕ return results in a structured format:
  - ⚫ for actor queries: `{ "Actor Name": [films...] }`
  - ⚫ for film queries: `{ "Film Title": [actors...] }`

## Example 1 — Actor Found

```python
pairs = [
    ["Brad Pitt", "Fight Club"],
    ["Emma Stone", "La La Land"],
    ["Emma Stone", "Cruella"],
    ["Keanu Reeves", "The Matrix"],
    ["Tom Hanks", "Forrest Gump"]
]

actor_name = "Emma Stone"
```

**Output**

```text
"Emma Stone": ["La La Land", "Cruella"]
```

## Example 2 — No Actor Found

```python
pairs = [
    ["Anne Hathaway", "Interstellar"],
    ["Anne Hathaway", "Les Misérables"],
    ["Chris Evans", "Captain America"],
    ["Zendaya", "Dune"]
]

actor_name = "Robert Downey Jr."
```

If the two random actors chosen are Anne Hathaway and Zendaya, the output must be:

```text
"Anne Hathaway": ["Interstellar", "Les Misérables"],
"Zendaya": ["Dune"]
```

## Example 3 — Film Found

```python
pairs = [
    ["Anne Hathaway", "Interstellar"],
    ["Matthew McConaughey", "Interstellar"],
    ["Jessica Chastain", "Interstellar"],
    ["Chris Evans", "Captain America"]
]

query = "Interstellar"
```

**Output**

```text
"Interstellar": ["Anne Hathaway", "Jessica Chastain", "Matthew McConaughey"]
```

## Example 4 — Film Not Found

```python
pairs = [
    ["Chris Evans", "Captain America"],
    ["Zendaya", "Dune"]
]

query = "Inception"
```

If the random actor chosen is Zendaya, the output must be:

```text
"Inception": [],
"Random Actor": {
    "Zendaya": ["Dune"]
}
```

## Additional function

You should add an additional function that improves the performance of the program. This could include, but is not limited to:

- ⭕ handling misspelt names using a similar string-comparison approach;
- ⭕ given a film, returning other films that share actors and ranking them by number of shared actors or by name similarity;
- ⭕ processing partial strings to identify possible actors or films efficiently.
