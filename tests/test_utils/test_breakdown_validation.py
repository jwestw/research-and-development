from src.utils.breakdown_validation import breakdown_validation, run_breakdown_validation
from pandas import DataFrame as pandasDF
import pytest
import logging

class TestBreakdownValidation:
    """Unit tests for breakdown_validation function."""

    def create_input_df(self):
        """Create an input dataframe for the test."""
        input_cols = ["reference", "202", "203", "222", "223", "204","205", "206", "207","219","220", "209", 
        "221", "210", "211", '212','214','216','242','250','243','244','245','246','247','248', '249', '218',
        '225','226','227','228','229','237','302', '303','304','305','501','503','505','507','502','504','506',
        '508','405', '407','409', '411', '406', '408', '410', '412', "871"]

        data = [
             ['A', 10, 30, 15, 15, 40, 10, 10, 20, 10, 15, 20, 10, 45, 85, 10, 10, 10, 10, 10, 10, 10, 10, 1, 1, 2, 1, 85, 20, 20, 20, 20, 2, 3, 50, 20, 10, 80, 50, 20, 25, 95, 60, 20, 10, 90, 80, 20, 10, 110, 80, 90, 20, 190, None],  
             ['B', 1, 30, 15, 15, 40, 10, 10, 20, 10, 15, 20, 10, 45, 85, 10, 10, 10, 10, 10, 10, 10, 10, 1, 1, 2, 1, 85, 20, 20, 20, 20, 2, 3, 50, 20, 10, 80, 50, 20, 25, 95, 60, 20, 10, 90, 80, 20, 10, 110, 80, 90, 20, 190, None],
             ['C',],
             ['D', None, 0, None, None, 0, None, None, None, None, None, None, None, 0, 0, None, None, None, None, None, None, None, None, None, None, None, None, 0, None,	None, None,	None, None, None, None,	None, None, 0, None, None, None, 0,	None, None,	None, 0, None, None, None, 0, None,	None, None,	0, None],
             ]

        input_df = pandasDF(data=data, columns=input_cols)

        return input_df


    def test_breakdown_validation_success(self, caplog):
        """Test for run_breakdown_validation function where the values match."""
        input_df = self.create_input_df()
        input_df = input_df.loc[(input_df['reference'] == 'A')]
        msg = 'All breakdown values are valid.\n'
        with caplog.at_level(logging.INFO):
            run_breakdown_validation(input_df)
            assert msg in caplog.text
  
    def test_breakdown_validation_fail(self):
        """Test for run_breakdown_validation function where the values do not meet the criteria."""
        input_df = self.create_input_df()
        input_df = input_df.loc[(input_df['reference'] == 'B')]
        with pytest.raises(ValueError):
            run_breakdown_validation(input_df)

    def test_breakdown_validation_fail_all_null(self, caplog):
        """Test for run_breakdown_validation function where the values do not meet the criteria."""
        input_df = self.create_input_df()
        input_df = input_df.loc[(input_df['reference'] == 'C')]
        msg = 'All breakdown values are valid.\n'
        with caplog.at_level(logging.INFO):
            run_breakdown_validation(input_df)
            assert msg in caplog.text

    def test_breakdown_validation_fail_totals_zero(self, caplog):
        """Test for run_breakdown_validation function where the values do not meet the criteria."""
        input_df = self.create_input_df()
        input_df = input_df.loc[(input_df['reference'] == 'D')]
        msg = 'All breakdown values are valid.\n'
        with caplog.at_level(logging.INFO):
            run_breakdown_validation(input_df)
            assert msg in caplog.text

    def test_breakdown_validation_msg(self):
        """Test for run_breakdown_validation function to check the returned message."""
        input_df = self.create_input_df()
        input_df = input_df.loc[(input_df['reference'] == 'B')]
        msg = "Columns 202 + 223 do not equal column 204 for reference: B.\n "
        with pytest.raises(ValueError) as e:
            run_breakdown_validation(input_df)
        assert str(e.value) == msg