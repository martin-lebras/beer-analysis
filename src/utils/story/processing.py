import pandas as pd
import numpy as np


def remove_low_alcohol(
    dataframe: pd.DataFrame, dataframe_past: pd.DataFrame
) -> tuple[pd.DataFrame]:
    """Removes the rows and columns related to low alcohol beers from the dataframes

    Arguments:
        dataframe: a pandas dataframe with the ratings of the beers by users and the beer style
        dataframe_past: a pandas dataframe with the past ratings count and average of the users at the time of the ratings

    Returns:
        dataframe: the updated dataframe without rows related to low alcohol beers
        dataframe_past: the updated dataframe_past without columns related to low alcohol beers
    """
    dataframe = dataframe.loc[~(dataframe["beer_global_style"] == "Low Alcohol Beer")]
    dataframe_past = dataframe_past.drop(
        columns=[
            "user_past_ratings_Low Alcohol Beer_count",
            "user_past_ratings_Low Alcohol Beer_average",
        ],
        errors="ignore",
    )
    return dataframe, dataframe_past


def shift_past_count(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Fixes the past beer style count and average

    Arguments:
        dataframe: a pandas dataframe with the past beer style count and averages of the user

    Returns:
        dataframe: the updated dataframe
    """
    # Remove one to all the counts in order to get the past count
    dataframe.loc[:, "user_beer_style_past_ratings_count"] = (
        dataframe["user_beer_style_past_ratings_count"] - 1
    )
    # Set the past average to NaN for the first rating as there is no previous rating
    dataframe.loc[
        dataframe["user_beer_style_past_ratings_count"] == 0,
        "user_beer_style_past_ratings_average",
    ] = np.nan
    return dataframe


def create_time_variables(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Creates the columns for time variables at several levels

    Arguments:
        dataframe: a pandas dataframe with a data column in second

    Return:
        dataframe: the dataframe with the newly created time columns
    """
    dataframe["day"] = pd.to_datetime(dataframe["date"], unit="s").dt.round("D")
    dataframe["week"] = (
        pd.to_datetime(dataframe["date"], unit="s").dt.to_period("W").dt.start_time
    )
    dataframe["month"] = (
        pd.to_datetime(dataframe["date"], unit="s").dt.to_period("M").dt.start_time
    )
    dataframe["quarter"] = pd.to_datetime(dataframe["date"], unit="s").dt.to_period("Q")
    dataframe["year"] = pd.to_datetime(dataframe["date"], unit="s").dt.to_period("Y")
    return dataframe
