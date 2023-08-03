"""Unit testing module."""
# Import testing packages
import pandas as pd
import pytest
import numpy as np

from src.imputation.pg_conversion import pg_to_pg_mapper


@pytest.fixture
def dummy_data() -> pd.DataFrame:
    # Set up the dummyinput  data
    data = pd.DataFrame(
        {
            "201": [0, 1, 2, 3, 4, 5],
        }
    )
    data.astype("category")
    return data


@pytest.fixture
def mapper() -> pd.DataFrame:
    # Set up the dummy mapper data
    mapper = {
        "2016 > Form PG": [0, 1, 2, 3, 4, 5],
        "2016 > Pub PG": [np.nan, "A", "B", "C", "C", "D"],
    }
    return pd.DataFrame(mapper)


@pytest.fixture
def expected_output() -> pd.DataFrame:
    # Set up the dummy output data
    expected_output = pd.DataFrame(
        {
            "201": [np.nan, "A", "B", "C", "C", "D"],
        }
    )
    return expected_output


def test_pg_mapper(dummy_data, expected_output, mapper):
    """Tests for pg mapper function."""

    target_col = dummy_data.columns[0]
    expected_output_data = expected_output.astype("category")

    df_result = pg_to_pg_mapper(dummy_data, mapper, target_col)

    pd.testing.assert_frame_equal(df_result, expected_output_data)
