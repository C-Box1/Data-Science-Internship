# Lab 6 — OOP Basics

## Overview
Introduction to Object-Oriented Programming in Python. Covered class definition, constructors, attributes, methods, inheritance, magic methods, static/class methods, and `functools.total_ordering`.

---

## Checklist

### Part 1 — A Tale of One Hero

- [ ] Exercise 1 — Extended `Monkey` class to include a `name` attribute in `__init__`
- [ ] Exercise 2 — Created `Hero` class with `name` and `super_power` attributes
- [ ] Exercise 3 — Added `use_power()` method to `Hero` that prints a descriptive message
- [ ] Exercise 4 — Added `steal_peanut(monkey_victim)` to `BadGuy` and `defeat(loser_badguy, mistreated_monkeys=[])` to `Hero`; ran `tell_a_story()`

### Part 2 — Primatology

- [ ] Exercise 5 — Printed all four attributes of the `washoe` `Ape` instance
- [ ] Exercise 6 — Created `Nut` class; updated `Ape` with `nut_stash` as a list, `stash_nuts(*nuts)`, and `has_nut(nut)` methods
- [ ] Exercise 7 — Implemented `__str__` on `Ape` for a human-friendly print representation
- [ ] Exercise 8 — Implemented `__ge__` and `__eq__` on `Ape`; implemented `__ge__` on `Gorilla` (silver-back priority); applied `@total_ordering`; bonus: also implemented `__le__`, `__lt__`, `__gt__`
- [ ] Exercise 9 — Implemented static method `nut_inventory(*monkeys)` returning a dict of nut type counts; bonus: used `Counter` with `__hash__` and `__eq__` on `Nut`

---

## Difficulties
> *Fill in what you found hard or confusing during this lab.*

-

---

## Feedback
> *Your thoughts on this lab — what worked, what didn't, what surprised you.*

-
