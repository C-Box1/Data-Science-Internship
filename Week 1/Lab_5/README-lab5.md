# Lab 5 — Functions

## Overview

In-depth exploration of Python functions: positional and keyword arguments, default values, variadic parameters (`*args`, `**kwargs`), scope, mutable default arguments, and documentation conventions.

---

## Checklist

### Exploring arguments and parameters

- [X] Exercise 1 — Identified valid/invalid calls for `print_two(a, b)` and commented out invalid ones
- [X] Exercise 2 — Identified valid/invalid calls for `keyword_args(a, b=1, c='X', d=None)`
- [X] Exercise 3 — Identified valid/invalid calls for `variadic(*args, **kwargs)`
- [X] Exercise 4 — Identified valid/invalid calls for `all_together(x, y, z=1, *nums, indent=True, spaces=4, **options)`

### Writing functions

- [X] Exercise 5 — Implemented `speak_excitedly(msg, n_excl_marks=1, in_caps=False)` and wrote the four required calls
- [X] Exercise 6 — Implemented `average(*args)` returning the mean or `None` for no arguments, and called it with an unpacked list
- [X] Exercise 7 — Implemented `make_table(**kwargs)` with `key_justify` and `value_justify` alignment options (bonus)

### Review exercises

- [X] Review 1 — Predicted output of `return` vs `print` examples
- [X] Review 2 — Understood `reassign` vs `append_one` (object reference vs rebinding)
- [X] Review 3 — Traced variable scope across two `foo()` case studies
- [X] Review 4 — Understood the `UnboundLocalError` and why it occurs
- [X] Review 5 — Understood mutable default argument behavior (`append_twice`) and the `None` sentinel fix
- [X] Review 6 — Read and understood `__doc__` docstrings
- [X] Review 7 — Read and understood parameter annotations (`__annotations__`)
- [X] Exercise 8 — Implemented `autodoc(f)` that appends argument and return type info to a function's docstring

---

## Difficulties

* In this Lab what I found confusing is how python treats inserted arguments and how it shows them when you try to look into how it understands list unpacking or dict unpacking

---

## Feedback

* In this Lab there was a lot of stuff to learn all the way from learning how to define a function to learning how to deal with positional argument and keyword argument and the different ways arguments can be inserted in the parameters of a function and learning what a lambda function is, also understandng how local and global variables behaves and how python scans inncompile time and then runs line by line in runtime. And on top of that seeing some python attributes and how they work in python.
