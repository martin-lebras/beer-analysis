import pandas as pd


def compute_cumulative_ratings_count(dataframe: pd.DataFrame):
    """Computes the cumulative count of ratings

    Arguments:
        dataframe: a pandas dataframe with the ratings of beers and the dates

    Returns:
        dataframe: a pandas dataframe with the cumulative count of ratings
    """
    dataframe = dataframe.sort_values(["date"])
    dataframe["_count"] = 1
    dataframe["cumulative_ratings_count"] = dataframe["_count"].cumsum()
    dataframe = dataframe.drop(columns=["_count"])
    return dataframe


def remove_before_month(
    dataframe: pd.DataFrame, dataframe_past: pd.DataFrame, month: str
) -> pd.DataFrame:
    """Removes the ratings of user who joined before a given month

    Arguments:
        dataframe: a pandas dataframe with the ratings of the users and the dates
        dataframe_past: a pandas dataframe with the past beer style counts and averages
        month: a string denoting the threshold month
    Returns:
        dataframe: the filtered dataframe
    """
    dataframe = dataframe.sort_values(["user_id", "date"])
    dataframe = dataframe.merge(
        (dataframe.groupby("user_id")["month"].first() >= month)
        .reset_index()
        .rename(columns={"month": "is_first_rating_after_month"}),
        on="user_id",
    )
    dataframe = dataframe[dataframe["is_first_rating_after_month"]]
    dataframe = dataframe.drop(columns=["is_first_rating_after_month"])

    # Drop the ratings given before the threshold date
    dataframe_past.drop(
        dataframe_past[dataframe_past["month"] < month].index, axis=0, inplace=True
    )
    # Drop the ratings given by after the threshold date by users who joined before the threshold
    dataframe_past = dataframe_past[
        dataframe_past["user_id"].isin(dataframe["user_id"].drop_duplicates())
    ]
    return dataframe, dataframe_past
