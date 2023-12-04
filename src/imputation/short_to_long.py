import pandas as pd

from src.outputs.short_form import create_headcount_cols


def fill_sf_zeros(df:pd.DataFrame) -> pd.DataFrame:
    """Fill nulls with zeros in short from numeric questions."""
    sf_questions = [str(q) for q in range(701, 712) if q != 708]

    sf_mask = (df["formtype"] == "0006") 
    clear_mask = (df["status"].isin(["Clear", "Clear - overriden"]))

    for q in sf_questions:
        df.loc[(sf_mask & clear_mask), q] = df.copy()[q].fillna(0)

    return df

def run_short_to_long(df:pd.DataFrame) -> pd.DataFrame:
    """Implement short form to long form conversion.

    Args:
        df (pd.DataFrame): The survey dataframe being prepared for
            short form output.
        selectiontype (list): Selection type(s) included in short to long conversion.

    Returns:
        pd.DataFrame: The dataframe with additional instances for civil and
            defence short form responses, in long form format.
    """
    # Fill shortform questions nulls with zeros for clear records
    df = fill_sf_zeros(df)
    
    # create columns temporary "headcount_civil" and "headcount_defence"
    df = create_headcount_cols(df)

    convert_short_to_long = [
        ("701", "702", "211"),
        ("703", "704", "305"),
        ("706", "707", "emp_total"),
        ("headcount_civil", "headcount_defence", "headcount_total"),
    ]

    civil_df = df.loc[df["formtype"] == "0006"].copy()
    defence_df = civil_df.copy()

    df.loc[df["formtype"] == "0006", "instance"] = 0

    civil_df.loc[:, "200"] = "C"
    civil_df.loc[:, "instance"] = 1

    defence_df.loc[:, "200"] = "D"
    defence_df.loc[:, "instance"] = 2

    for each in convert_short_to_long:
        civil_df[each[2]] = civil_df[each[0]]
        defence_df[each[2]] = defence_df[each[1]]

    df = df.drop(["headcount_civil", "headcount_defence"], axis=1)

    return df
