import pytest
import numpy as np
from pandas import DataFrame as pandasDF
from pandas._testing import assert_frame_equal

from src.imputation.impute_civ_def import (
    prep_cd_imp_classes,
    create_civdef_dict,
    calc_cd_proportions,
    _get_random_civdef,
)


class TestCalcCDPorportions:
    """Unit tests for calc_cd_proportions function."""

    def create_input_df(self):
        """Create an input dataframe for the test."""
        input_cols = ["reference", "instance", "200", "202", "pg_sic_class"]

        data1 = [
            [1001, 1, "C", 100, "AC_1234"],
            [1001, 2, "C", 200, "AC_1234"],
            [1001, 3, "D", 50, "AC_1234"],
            [3003, 1, "C", 230, "AC_1234"],
            [3003, 2, "C", 59, "AC_1234"],
            [3003, 3, "D", 805, "AC_1234"],
            [3003, 4, "C", 33044, "AC_1234"],
            [3003, 5, "D", 4677, "AC_1234"],
            [3003, 6, np.nan, 0, "AC_1234"],
        ]

        data2 = [
            [1001, 1, "C", 100, "AC_1234"],
            [1001, 2, "C", 200, "AC_1234"],
            [3003, 6, np.nan, 0, "AC_1234"],
        ]

        input_df1 = pandasDF(data=data1, columns=input_cols)
        input_df2 = pandasDF(data=data2, columns=input_cols)
        return input_df1, input_df2

    def test_calc_cd_proportions(self):
        "Test for calc_cd_proportions function."
        input_df1, input_df2 = self.create_input_df()

        out_c1, out_d1 = calc_cd_proportions(input_df1)

        assert out_c1 == 0.625
        assert out_d1 == 0.375

        out_c2, out_d2 = calc_cd_proportions(input_df2)

        assert out_c2 == 1.0
        assert out_d2 == 0.0


class TestCreateCivdefDict:
    """Unit tests for create_civdef_dict function."""

    def create_input_df(self):
        """Create an input dataframe for the test."""
        input_cols = [
            "reference",
            "instance",
            "200",
            "201",
            "202",
            "statusencoded",
            "cellnumber",
            "rusic",
            "pg_sic_class",
            "empty_pgsic_group",
            "pg_class",
            "empty_pg_group",
        ]
        data = [
            [1001, 0, np.nan, np.nan, 0, "Clear", "800", "1234", "nan_1234", False, "nan", False],
            [1001, 1, "C", "AC", 100, "Clear", "800", "1234", "AC_1234", False, "AC", False],
            [1001, 2, "C", "AC", 200, "Clear", "800", "1234", "AC_1234", False, "AC", False],
            [1001, 3, "D", "AC", 50, "Clear", "800", "1234", "AC_1234", False, "AC", False],
            [1002, 0, np.nan, np.nan, 0, "Clear", "800", "1234", "nan_1234", False, "nan", False],
            [1002, 1, "C", "AC", 100, "Clear", "800", "1234", "AC_1234", False, "AC", False],
            [2002, 0, np.nan, np.nan, np.nan, "Clear", "800", "444", "nan_444", False, "nan", False],
            [2002, 1, np.nan, "AC", 200, "Clear", "800", "444", "AC_444", True, "AC", False],
            [2002, 2, "D", "AC", 200, "999", "800", "444", "AC_444", True, "AC", False],
            [3003, 0, np.nan, np.nan, 0, "Clear", "800", "1234", "nan_1234", False, "nan", False],
            [3003, 1, "C", "ZZ", 230, "Clear", "800", "12", "ZZ_12", False, "ZZ", False],
            [3003, 2, "C", "ZZ", 59, "Clear", "800", "12", "ZZ_12", False, "ZZ", False],
            [3003, 3, "D", "ZZ", 805, "Clear", "800", "12", "ZZ_12", False, "ZZ", False],
            [3003, 4, "C", "ZZ", 33044, "Clear", "800", "12", "ZZ_12", False, "ZZ", False],
            [3003, 5, "D", "ZZ", 4677, "Clear", "800", "12", "ZZ_12", False, "ZZ", False],
            [3003, 6, np.nan, np.nan, 0, "Clear", "800", "12", "nan_12", False, "nan", False],
        ]

        input_df = pandasDF(data=data, columns=input_cols)
        return input_df

    def test_create_civdef_dict(self):
        "Test the pg_sic dict calcuclation in create_civdef_dict function."
        input_df = self.create_input_df()

        pgsic_dict, pg_dict = create_civdef_dict(input_df)

        exp_pgsic_dict = {"AC_1234": (0.75, 0.25), "ZZ_12": (0.6, 0.4)}

        assert pgsic_dict == exp_pgsic_dict

    def test_create_civdef_dict2(self):
        "Test the pg only dict calcuclation in create_civdef_dict function."
        input_df = self.create_input_df()

        pgsic_dict, pg_dict = create_civdef_dict(input_df)

        exp_pg_dict = {"AC": (0.6, 0.4)}

        assert pg_dict == exp_pg_dict


class TestPrepCDImpClasses:
    """Unit tests for prep_cd_imp_classes function."""

    def create_input_df(self):
        """Create an input dataframe for the test."""
        input_cols = [
            "reference",
            "instance",
            "200",
            "201",
            "202",
            "status",
            "cellnumber",
            "rusic",
        ]

        data = [
            [1001, 0, np.nan, np.nan, 0, "Clear", "800", "1234"],
            [1001, 1, "C", "AC", 100, "Clear", "800", "1234"],
            [1001, 2, "C", "AC", 200, "Clear", "800", "1234"],
            [1001, 3, "D", "AC", 50, "Clear", "800", "1234"],
            [1002, 0, np.nan, np.nan, 0, "Clear", "800", "1234"],
            [1002, 1, "C", "AC", 100, "Clear", "800", "1234"],
            [2002, 0, np.nan, np.nan, np.nan, "Clear", "800", "444"],
            [2002, 1, np.nan, "AC", 200, "Clear", "800", "444"],
            [2002, 2, "D", "AC", 200, "999", "800", "444"],
            [3003, 0, np.nan, np.nan, 0, "Clear", "800", "1234"],
            [3003, 1, "C", "ZZ", 230, "Clear", "800", "12"],
            [3003, 2, "C", "ZZ", 59, "Clear", "800", "12"],
            [3003, 3, "D", "ZZ", 805, "Clear", "800", "12"],
            [3003, 4, "C", "ZZ", 33044, "Clear", "800", "12"],
            [3003, 5, "D", "ZZ", 4677, "Clear", "800", "12"],
            [3003, 6, np.nan, np.nan, 0, "Clear", "800", "12"],
        ]

        input_df = pandasDF(data=data, columns=input_cols)
        return input_df

    def create_exp_output_df(self):
        """Create an expected output dataframe for the test."""
        output_cols = [
            "reference",
            "instance",
            "200",
            "201",
            "202",
            "status",
            "cellnumber",
            "rusic",
            "pg_sic_class",
            "empty_pgsic_group",
            "pg_class",
            "empty_pg_group",
        ]

        data = [
            [1001, 0, np.nan, np.nan, 0, "Clear", "800", "1234", "nan_1234", False, "nan", False],
            [1001, 1, "C", "AC", 100, "Clear", "800", "1234", "AC_1234", False, "AC", False],
            [1001, 2, "C", "AC", 200, "Clear", "800", "1234", "AC_1234", False, "AC", False],
            [1001, 3, "D", "AC", 50, "Clear", "800", "1234", "AC_1234", False, "AC", False],
            [1002, 0, np.nan, np.nan, 0, "Clear", "800", "1234", "nan_1234", False, "nan", False],
            [1002, 1, "C", "AC", 100, "Clear", "800", "1234", "AC_1234", False, "AC", False],
            [2002, 0, np.nan, np.nan, np.nan, "Clear", "800", "444", "nan_444", False, "nan", False],
            [2002, 1, np.nan, "AC", 200, "Clear", "800", "444", "AC_444", True, "AC", False],
            [2002, 2, "D", "AC", 200, "999", "800", "444", "AC_444", True, "AC", False],
            [3003, 0, np.nan, np.nan, 0, "Clear", "800", "1234", "nan_1234", False, "nan", False],
            [3003, 1, "C", "ZZ", 230, "Clear", "800", "12", "ZZ_12", False, "ZZ", False],
            [3003, 2, "C", "ZZ", 59, "Clear", "800", "12", "ZZ_12", False, "ZZ", False],
            [3003, 3, "D", "ZZ", 805, "Clear", "800", "12", "ZZ_12", False, "ZZ", False],
            [3003, 4, "C", "ZZ", 33044, "Clear", "800", "12", "ZZ_12", False, "ZZ", False],
            [3003, 5, "D", "ZZ", 4677, "Clear", "800", "12", "ZZ_12", False, "ZZ", False],
            [3003, 6, np.nan, np.nan, 0, "Clear", "800", "12", "nan_12", False, "nan", False]
        ]

        input_df = pandasDF(data=data, columns=output_cols)
        return input_df

    def test_prep_cd_imp_classes2(self):
        """Test for prep_imp_classes function"""
        input_df = self.create_input_df()
        expected_df = self.create_exp_output_df()

        result_df = prep_cd_imp_classes(input_df)

        assert_frame_equal(result_df, expected_df)


class TestGetRandomCivdef(object):
    """Tests for _get_random_civdef."""

    @pytest.mark.parametrize(
            "seed, proportions",
            [
                (1234567891011, [0.4, 0.6]),
                (1, [0.52, 0.48]),
                (54321, [0.1, 0.9]),
                (9999999, [0.75, 0.25]),
            ]
    )
    def test__get_random_civdef(self, seed, proportions):
        """General tests for _get_random_civdef."""
        # ensure the seed continues to give the same value with a given proportion
        values = []
        print(f"seed: {seed}, proportions: {proportions}")
        for i in range(10):
            rand = _get_random_civdef(ref=seed, proportions=proportions)
            values.append(rand)
            print(f"rand: {rand}")
        unique = set(values)
        assert len(unique) == 1, "Multiple random values found from one seed."
