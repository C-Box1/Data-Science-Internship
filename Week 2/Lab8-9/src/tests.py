import contextlib
import csv
import io
import itertools
import os
import sys
import unittest
from unittest.mock import patch

from monkey_model import Monkey
from monkey_classif import read_monkeys_from_csv, compute_knn, main
from monkey_visualize import scatter
from utils import euclidean_distance


class MonkeyModelTestCase(unittest.TestCase):
	"""Test case for Monkey class"""

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.expected_species = "species"
		self.expected_weight = 42
		self.expected_size = 37
		self.expected_furcolor = "#123456"
		self.expected_repr = "Monkey (species), 42kg, 37cm, fur: #123456"
		self.expected_str = "Monkey (species), 42kg, 37cm, fur: #123456"
		self.ex_monkey = Monkey(
			self.expected_weight,
			self.expected_size,
			self.expected_furcolor,
			species=self.expected_species
        )

	def test_constructor(self):
		"""testing the constructor produces the expect object """
		self.assertEqual(self.ex_monkey.species, self.expected_species)
		self.assertEqual(self.ex_monkey.weight, self.expected_weight)
		self.assertEqual(self.ex_monkey.size, self.expected_size)
		self.assertEqual(self.ex_monkey.fur_color, self.expected_furcolor)

	def test_str(self):
		"""testing the representation matches expections"""
		self.assertEqual(repr(self.ex_monkey), self.expected_repr)
		self.assertEqual(str(self.ex_monkey), self.expected_str)

	def test_check_fur(self):
		"""testing checkhexacolor is correctly applied"""
		with self.assertRaises(ValueError):
			_ = Monkey(
				self.expected_weight,
				self.expected_size,
				"WRONG",
				species=self.expected_species
			)

	def test_bmi(self):
		"""testing Body Mass Index computations"""
		with self.assertRaises(ValueError):
			_ = Monkey(
                    "11",
                    self.expected_size,
                    self.expected_furcolor,
                    species=self.expected_species
			)
		with self.assertRaises(ValueError):
			__ = Monkey(
                    0,
                    self.expected_size,
                    self.expected_furcolor,
                    species=self.expected_species
			)

class MonkeyCSVTestCase(unittest.TestCase):
    """Test case for Monkey CSV reading functions"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.header = "species","size","weight","color"
        self.sup_cols = "monkey", "fur_color_int", "bmi"
        self.basic_line = 'foo', 42.1, 42.2, "#123456"
        self.test_filename = "test.csv"

    def setUp(self):
        with open(self.test_filename, 'w') as ostr:
            writer = csv.writer(ostr)
            _ = writer.writerow(self.header)

    def tearDown(self):
        os.remove(self.test_filename)

    def _remake_file(self):
        """regenerate test file"""
        self.tearDown()
        self.setUp()

    def _add_lines(self, *lines):
        """add rows to the csv"""
        with open(self.test_filename, 'a') as ostr:
            writer = csv.writer(ostr)
            for line in lines:
                _ = writer.writerow(line)

    def test_columns_raises(self):
        """test whether unknown and missing columns yield an error"""
        old_header = self.header
        self.header = [*self.header, 'incorrect']
        self._remake_file()
        with self.assertRaises(ValueError):
            read_monkeys_from_csv(self.test_filename)
        self.header = old_header

    def test_missing_values(self):
        """test how undefined data is handled"""
        self._add_lines(['', *self.basic_line[1:]])
        self.assertEqual(len(read_monkeys_from_csv(self.test_filename)), 1)
        for i in [1, 2, 3]:
            tweaked_line = [*self.basic_line[:i], '', *self.basic_line[i+1:]]
            self._remake_file()
            self._add_lines(tweaked_line)
            self.assertEqual(len(read_monkeys_from_csv(self.test_filename)), 0)

    def test_incorrect_values(self):
        """test how incorrect data is handled"""
        for i in [1, 2]:
            tweaked_line = [*self.basic_line[:i], -self.basic_line[i], *self.basic_line[i+1:]]
            self._remake_file()
            self._add_lines(tweaked_line)
            self.assertEqual(len(read_monkeys_from_csv(self.test_filename)), 0)
        tweaked_line = [*self.basic_line[:-1], "#WRONG"]
        self._remake_file()
        self._add_lines(tweaked_line)
        self.assertEqual(len(read_monkeys_from_csv(self.test_filename)), 0)

    def test_sup_cols_present(self):
        """test whether the columns that should be added are all present"""
        self._add_lines(self.basic_line)
        self.assertEqual([*read_monkeys_from_csv(self.test_filename).columns], [*self.header, *self.sup_cols])

    def test_strict_mode(self):
        """test whether missing values provokes an error in strict mode."""
        self._add_lines(self.basic_line)
        read_monkeys_from_csv(self.test_filename, strict=True)
        for i in [0, 1, 2, 3]:
            tweaked_line = [*self.basic_line[:i], '', *self.basic_line[i+1:]]
            self._remake_file()
            self._add_lines(tweaked_line)
            with self.assertRaises(ValueError):
                read_monkeys_from_csv(self.test_filename, strict=True)


class KNNTestCase(unittest.TestCase):
    """Test case for KNN algorithm"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_filename = "test.csv"
        self._mk_file()

        self.df = compute_knn(read_monkeys_from_csv(self.test_filename))
        os.remove(self.test_filename)

    def _mk_file(self):
        lines = [
            ["species","size","weight","color"],
            ["A", 9.5, 9.5, "#FFFEEE"],
            ["A", 9., 9., "#EEEEEE"],
            ["B", 1.5, 1.5, "#111000"],
            ["B", 2., 2., "#111111"],
            ["B", 3., 3., "#222222"],
            ["A", 8., 8., "#DDDDDD"],
            ["", 10., 10., "#FFFFFF"], # an A
            ["", 1., 1., "#000000"], # a B
        ]
        with open(self.test_filename, "w") as ostr:
            writer = csv.writer(ostr)
            for line in lines:
                _ = writer.writerow(line)

    def test_euclidean_distance(self):
        """test Euclidean distance function"""
        self.assertEqual(euclidean_distance([1, 1], [2, 1]), 1.0)

    def test_all_labelled(self):
        """test that all monkeys have a species"""
        self.assertTrue(self.df['species'].all())
        self.assertTrue(self.df['monkey'].apply(lambda m: m.species).all())

    def test_assignment_correct(self):
        """test that monkey species are as expected"""
        self.assertEqual(self.df.loc[6]['species'], "A")
        self.assertEqual(self.df.loc[7]['species'], "B")

    def test_column_options(self):
        """test that columns used for knn can be chosen"""
        self._mk_file()

        valid_cols = {"fur_color_int", "fur_color_int_r", "fur_color_int_g", "fur_color_int_b", "weight", "size", "bmi"}

        for column_pairs in itertools.combinations(valid_cols, 2):
            df = compute_knn(read_monkeys_from_csv(self.test_filename), columns=column_pairs)
            self.assertEqual(df.loc[6]['species'], "A")
            self.assertEqual(df.loc[7]['species'], "B")

        with self.assertRaises(AssertionError):
            df = compute_knn(read_monkeys_from_csv(self.test_filename), columns=["bmi"])

        with self.assertRaises(AssertionError):
            df = compute_knn(read_monkeys_from_csv(self.test_filename), columns=["bmi", "foo"])

        os.remove(self.test_filename)


class CLITestCase(unittest.TestCase):
    """Test case for the command line interface"""

    # unittest.mock.patch allows you to "pretend" to call a function, instead
    # of actually calling it. Calls these functions now only increment a counter
    # representing the number of times it has been called.
    # the return_value keyword allows us to specify which value is returned by
    # the mock patch.
    @patch('monkey_classif.save_to_csv')
    @patch('monkey_classif.compute_knn', return_value="snd df mock")
    @patch('monkey_classif.read_monkeys_from_csv', return_value="fst df mock")
    def test_cli_knn(self, mock_read, mock_knn, mock_save):
        """test whether knn subcommand links to the correct functions."""
        sys.argv = ['monkey_classif.py', 'knn', 'in.csv', 'out.csv', '--k', '7', '--obs', 'bmi', 'fur_color_int']
        main()
        # we can look up that counter and ensure it has been called only once, with the correct arguments.
        mock_read.assert_called_once_with('in.csv')
        mock_knn.assert_called_once_with("fst df mock", k=7, columns=['bmi', 'fur_color_int'])
        mock_save.assert_called_once_with("snd df mock", 'out.csv')

    @patch('monkey_visualize.scatter')
    def test_cli_viz(self, mock_scatter):
        """test whether visualization subcommand links to the correct functions."""
        sys.argv = ['monkey_classif.py', 'visualize', 'out.csv', 'bmi', 'fur_color_int']
        main()
        mock_scatter.assert_called_once_with('out.csv', 'bmi', 'fur_color_int')


class VisualizationTestCase(unittest.TestCase):
    """Test case for the visualization"""

    # unittest.mock.patch allows you to "pretend" to call a function, instead
    # of actually calling it. Calls `show()` now only increment a counter
    # representing the number of times it has been called.
    @patch('matplotlib.pyplot.show')
    def test_callable_columns(self, mock_pyplot_show):
        """test whether all columns can be properly used for scatter plots."""
        test_filename = "test.csv"
        lines = [
            ["species","size","weight","color"],
            ["A", 9.5, 9.5, "#FFFEEE"],
            ["A", 9., 9., "#EEEEEE"],
            ["B", 1.5, 1.5, "#111000"],
            ["B", 2., 2., "#111111"],
            ["B", 3., 3., "#222222"],
            ["A", 8., 8., "#DDDDDD"],
        ]

        with open(test_filename, "w") as ostr:
            writer = csv.writer(ostr)
            for line in lines:
                _ = writer.writerow(line)

        valid_cols = {"fur_color_int", "fur_color_int_r", "fur_color_int_g", "fur_color_int_b", "weight", "size", "bmi"}

        #this line and then next one serve to suppress a warning message about calling show() too often.
        f = io.StringIO()
        with contextlib.redirect_stderr(f):
            col_pairs = list(itertools.combinations(valid_cols, 2))
            for column_pairs in col_pairs:
                scatter(test_filename, *column_pairs)
            self.assertEqual(mock_pyplot_show.call_count, len(col_pairs))
            with self.assertRaises(AssertionError):
                scatter(test_filename, "foo", "bmi")
            with self.assertRaises(AssertionError):
                scatter(test_filename, "bmi", "foo")
            os.remove(test_filename)


if __name__ == '__main__':
    unittest.main()
