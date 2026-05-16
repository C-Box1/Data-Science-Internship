# Lab 8-9: Python Ecosystem & Monkey KNN Classification

A machine learning project implementing K-Nearest Neighbors (KNN) classification to distinguish monkey species based on physical features.

## Overview

This project demonstrates core Python concepts including:
- **Object-Oriented Programming**: `Monkey` class with validation and BMI computation
- **Data Processing**: Reading, cleaning, and transforming CSV data using pandas
- **Machine Learning**: KNN classification algorithm for species prediction
- **Testing**: Unit tests using `unittest` framework (TDD approach)
- **Python Ecosystem**: argparse for CLI, pandas/numpy for data handling, matplotlib for visualization

## Completed Tasks

### Exercise 1: Monkey Class Implementation
- ✅ `Monkey` class with attributes: `species`, `fur_color`, `size`, `weight`
- ✅ Hexadecimal color validation using `check_hexacolor()`
- ✅ `__str__` and `__repr__` methods for readable output
- ✅ Unit tests: `test_constructor()`, `test_str()`, `test_check_fur()`

### Exercise 2: Data Pipeline
- ✅ `read_monkeys_from_csv(csv_filepath, strict)` function for loading and cleaning data
- ✅ CSV validation (column names, missing values, invalid data)
- ✅ BMI computation: `compute_bmi()` method on `Monkey` objects
- ✅ Added `monkey`, `fur_color_int`, and `bmi` columns to dataframe
- ✅ Unit tests for data processing pipeline

### Exercise 3: KNN Classification
- ✅ `compute_knn(dataframe, k=5)` algorithm implementation
- ✅ 2D classification space: BMI (x-axis) vs. fur color (y-axis)
- ✅ Euclidean distance computation for neighbor ranking
- ✅ Species prediction for unlabeled monkeys using k-nearest neighbors
- ✅ Unit tests including `euclidean_distance` validation

### Bonus: Functional Programming Style
- Refactored KNN using FP paradigm: `filter`, `reduce`, `lambda` functions
- Pure functions without `if`/`for`/`while` keywords

## Environment Setup

### Option 1: Using `uv` (Recommended - Faster)

If you have miniconda installed with Python 3.8:

```bash
# Create and activate environment with Python 3.8
conda create -n monkey-env python=3.8
conda activate monkey-env

# Initialize uv project and install dependencies
uv init
uv add -r pip3.requirements.txt
```

### Option 2: Using `pip` (Standard)

```bash
# Create and activate virtual environment
python3.8 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r pip3.requirements.txt
```

### Environment Details

- **Python Version**: 3.8 (required)
- **Dependency Management**: Both `uv` and `pip` are supported
  - `uv` is faster for dependency resolution and was used during development
  - `pip` works with standard `requirements.txt`
- **Dependencies**: Listed in `pip3.requirements.txt` (pandas, numpy, matplotlib)
- **No Miniconda YAML**: This project uses only pure Python libraries; no conda-specific packages required
- **Lock Files**: `pyproject.toml` and `uv.lock` provided for reproducible builds

## Running the Project

### Test Suite
```bash
python src/tests.py
```

### Classification (KNN)
```bash
python src/monkey_classif.py knn ./data/monkeys.csv ./data/output.csv
```

### Visualization
```bash
python src/monkey_classif.py visualize ./data/output.csv weight fur_color_int
```

### Help & Options
```bash
python src/monkey_classif.py --help
python src/monkey_classif.py knn --help
python src/monkey_classif.py visualize --help
```

## Project Structure

```
.
├── src/
│   ├── monkey_classif.py      # Main entry point & KNN implementation
│   ├── monkey_model.py        # Monkey class definition
│   ├── monkey_visualize.py    # Matplotlib visualization
│   ├── utils.py               # Helper functions & CLI argument parsing
│   └── tests.py               # Unit test suite
├── data/
│   ├── monkeys.csv            # Training dataset (3K rows, 3 species)
│   └── viz_example.png        # Sample visualization output
├── pip3.requirements.txt       # Python dependencies
├── pyproject.toml             # uv project configuration
├── uv.lock                    # uv dependency lock file
└── README.md                  # This file
```

## Key Implementation Details

### Data Cleaning
- Handles ~25% unlabeled entries (species missing)
- Removes ~1% malformed values per column
- Validates hexadecimal color codes
- Drops rows with negative size/weight values

### KNN Algorithm
- 2D distance metric: √((BMI₁ - BMI₂)² + (color₁ - color₂)²)
- Default k=5 nearest neighbors
- Majority vote for species prediction
- Optional fuzzy classification (weighted by inverse distance)

## Testing

Unit tests verify:
- Monkey object construction and validation
- Hexadecimal color validation
- BMI calculation accuracy
- CSV parsing and data cleaning
- Euclidean distance computation
- KNN classification results

## References

See `lab8-9-ecosystem.ipynb` for detailed exercise instructions, background on TDD, functional programming patterns, and Python standard library pointers.
