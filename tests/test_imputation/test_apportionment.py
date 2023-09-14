import pandas as pd
import numpy as np
from pandas import DataFrame as pandasDF
from pandas._testing import assert_frame_equal

from src.imputation.apportionment import calc_202_totals

class TestCalc202Totals:
    """Unit tests for flag_outliers functtion."""

    def create_input_df(self):
        """Create an input dataframe for the test."""
        input_cols = [
            "reference",
            "instance",
            "200",
            "202",
        ]

        data = [
            [1001, 2, "C", 59],
            [1001, 1, "C", 230],
            [1001, 0, None, 0],
            [1001, 3, "D", 805],
            [1001, 4, "C", 33044],
            [1001, 5, "D", 4677],
            [1001, 6, None, 0],
            [2002, 0, None, 0],
            [2003, 0, None, 0],
            [2003, 1, "C", 100],
            [2003, 2, "C", 200],
            [2003, 3, "D", 50],
        ]

        input_df = pandasDF(data=data, columns=input_cols)
        return input_df

    def create_expected_df(self):
        """Create dataframe for the expected output of the test."""
        exp_cols = [
            "reference",
            "instance",
            "200",
            "202",
            "202_tot_all",
            "202_tot_CD",
        ]

        data = [
            [1001, 2, "C", 59, 38815, 33333.0],
            [1001, 1, "C", 230, 38815, 33333.0],
            [1001, 0, None, 0, 38815, np.nan],
            [1001, 3, "D", 805, 38815, 5482.0],
            [1001, 4, "C", 33044, 38815, 33333.0],
            [1001, 5, "D", 4677, 38815, 5482.0],
            [1001, 6, None, 0, 38815, np.nan],
            [2002, 0, None, 0, 0, np.nan],
            [2003, 0, None, 0, 350, np.nan],
            [2003, 1, "C", 100, 350, 300.0],
            [2003, 2, "C", 200, 350, 300.0],
            [2003, 3, "D", 50, 350, 50.0],
        ]

        expected_df = pandasDF(data=data, columns=exp_cols)
        return expected_df

    def test_calc_202_totals(self):
        """Test for flag_outliers function."""
        input_df = self.create_input_df()
        expected_df = self.create_expected_df()

        result_df = calc_202_totals(input_df)
        assert_frame_equal(result_df, expected_df)
