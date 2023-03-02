import time
from src.utils.wrappers import time_logger_wrap, exception_wrap, df_change_wrap
import time
import numpy as np
import pandas as pd


@exception_wrap
def divbyzero(num: int):
    """Define a testing function that will throw an exception.

    Args:
        num (int): Integer value

    Returns:
        Error: This function returns a zero division error
    """
    ans = num / 0
    return ans


@exception_wrap
def this_definitely_works(num: int):
    """Define a testing function that will not throw an exception.

    Args:
        num (int): Integer value

    Returns:
        int: Returns the squared value of the integer input
    """
    ans = num**num
    return ans


@time_logger_wrap
def takes_a_while(num: int):
    """Define a testing function that takes some time to run.

    Args:
        num (int): Integer value

    Returns:
        int: Integer value after sleep function ends
    """
    ans = 0
    for _ in range(num):
        ans += (num**2) ** 2
        time.sleep(5.5)
    return ans


@time_logger_wrap
@exception_wrap
def addition(a: int, b: int):
    """Testing multiple wrappers for one function

    Args:
        a (int): Integer value
        b (int): Integer value

    Returns:
        int: Integer value
    """
    c = a + b
    time.sleep(0.5)
    return c


@time_logger_wrap
@exception_wrap
def create_dummy_df(seed=42):
    """Create a dataframe with headers using random integers

    Args:
        seed (int, optional): Seed value to repeat randomness. Defaults to 42.

    Returns:
        pd.Dataframe: Returns a 4*100 Pandas dataframe with column names
    """
    np.random.seed(seed=seed)
    df = pd.DataFrame(np.random.randint(0, 100, size=(100, 4)), columns=list("ABCD"))
    LOGGER.info("Dummy dataframe has been created")
    return df



class Manipulate_data():
    
    def __init__(self,df):
        self.vf_df = df
        self.table_config = "SingleLine"
        self.df = self.manipulate_df()[0]
    
    @df_change_wrap
    @time_logger_wrap
    @exception_wrap
    def manipulate_df(self):
        df1 = self.vf_df[0]
        print(df1)
        df2 = self.vf_df[0] * 2
        print(df2)
        df = df1.append(df2)
        LOGGER.info("Dummy dataframe has been manipulated")
        return df


def add(a: int, b: int):
    """Simple addition function with error raising for Pytest

    Args:
        a (int): Integer value
        b (int): Integer value

    Raises:
        TypeError: Raise error if a or b is not an integer

    Returns:
        int: Sum of both inputs
    """
    if not isinstance(a, int) or not isinstance(b, int):
        raise TypeError("a and b must be integers")
    return a + b
