# Lab 3 — Strings

## Overview

Deep dive into Python strings: operators, formatting, `split` / `join`, and several word-puzzle challenges using a dictionary file.

---

## Checklist

### String operators & basics

- [X] Exercise 1 — Implemented `self_add(s, n)` using `+` and `self_mul(s, n)` using `*`

### String formatting

- [X] Exercise 2 — Implemented `dict_contents(d)` generating a formatted message from a dictionary

### Split and join

- [X] Exercise 3 — Implemented `every_other_word(s)` — splits on spaces, joins every other word with `_`

### Word puzzles (requires `/usr/share/dict/words`)

- [X] Exercise 4 — Implemented `load_english()` — loads, lowercases, deduplicates, and filters ASCII words (expected: 72165 words)
- [X] Exercise 5 — Implemented `is_cyclone_word(word)` and `is_cyclone_phrase(phrase)`, generated `all_cyclone_words` (expected: 441 words)
- [X] Exercise 6 — Implemented `is_triangle_word(word)`, generated `all_triangle_words` (expected: 5432 words)
- [X] Exercise 7 — Implemented `is_triad_word(word)` and `is_triad_phrase(phrase)`, generated `all_triad_words` (expected: 1041 words)
- [X] Exercise 8 — Implemented `is_surpassing_word(word)` and `is_surpassing_phrase(phrase)`, generated `all_surpassing_words` (expected: 1150 words)

---

## Difficulties

* During this lab the difficult or confusing parts were mainly the puzzles even tho they weren't very difficult just took a little more time than usual to find the solution for each problem

---

## Feedback

* This lab was fun especially when trying to understand how the .split() and .join() functions operate with different entries and how useful they are
