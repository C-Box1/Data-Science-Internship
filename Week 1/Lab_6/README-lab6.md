# Lab 6 — OOP Basics

## Overview

Introduction to Object-Oriented Programming in Python. Covered class definition, constructors, attributes, methods, inheritance, magic methods, static/class methods, and `functools.total_ordering`.

---

## Checklist

### Part 1 — A Tale of One Hero

- [X] Exercise 1 — Extended `Monkey` class to include a `name` attribute in `__init__`
- [X] Exercise 2 — Created `Hero` class with `name` and `super_power` attributes
- [X] Exercise 3 — Added `use_power()` method to `Hero` that prints a descriptive message
- [X] Exercise 4 — Added `steal_peanut(monkey_victim)` to `BadGuy` and `defeat(loser_badguy, mistreated_monkeys=[])` to `Hero`; ran `tell_a_story()`

### Part 2 — Primatology

- [X] Exercise 5 — Printed all four attributes of the `washoe` `Ape` instance
- [X] Exercise 6 — Created `Nut` class; updated `Ape` with `nut_stash` as a list, `stash_nuts(*nuts)`, and `has_nut(nut)` methods
- [X] Exercise 7 — Implemented `__str__` on `Ape` for a human-friendly print representation
- [X] Exercise 8 — Implemented `__ge__` and `__eq__` on `Ape`; implemented `__ge__` on `Gorilla` (silver-back priority); applied `@total_ordering`; bonus: also implemented `__le__`, `__lt__`, `__gt__`
- [X] Exercise 9 — Implemented static method `nut_inventory(*monkeys)` returning a dict of nut type counts; bonus: used `Counter` with `__hash__` and `__eq__` on `Nut`

---

## Difficulties

* In this lab OOP python was new to me because I was used to a mix of mostly procedural and functional programming so understanding the layout of how it worked was different. Most difficulties came in the Primatology part where I had to understand how different functions worked and ngl I have used AI to help me understand how do the `__eq__`, `__lt__`, `__hash__` and the rest of the functions work and they can be used at first they were confusing but after a few examples provided by the ai and showing their use case, I understood everything.

---

## Feedback

* This lab was very helpful in expanding my knowledge about Python and how it can be used especially that I have been trying to understand everything. So this lab was my entrypoint to OOP and I'm pretty sure there's so much more to learn
