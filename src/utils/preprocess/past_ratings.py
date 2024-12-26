import pandas as pd


def get_past_ratings_count_and_average(
    df_ratings: pd.DataFrame,
    sorting_columns: list[str],
    grouping_columns: list[str],
    name: str,
    shift: bool,
) -> pd.DataFrame:
    df_ratings = df_ratings.sort_values(sorting_columns, kind="stable")

    if shift:
        df_ratings[f"{name}_past_ratings_count"] = df_ratings.groupby(
            grouping_columns
        ).cumcount()
        df_ratings[f"{name}_past_ratings_average"] = (
            df_ratings.groupby(grouping_columns)["rating"]
            .expanding()
            .mean()
            .shift()
            .reset_index(level=[i for i in range(len(grouping_columns))], drop=True)
        )
    else:
        df_ratings[f"{name}_past_ratings_count"] = (
            df_ratings.groupby(grouping_columns).cumcount() + 1
        )
        df_ratings[f"{name}_past_ratings_average"] = (
            df_ratings.groupby(grouping_columns)["rating"]
            .expanding()
            .mean()
            .reset_index(level=[i for i in range(len(grouping_columns))], drop=True)
        )

    df_ratings.loc[
        df_ratings[f"{name}_past_ratings_count"] == 0, f"{name}_past_ratings_average"
    ] = pd.NA

    df_ratings = df_ratings.sort_index()
    return df_ratings


def get_past_ratings_counts_all_style(
    df_ratings: pd.DataFrame, dummy_column: str, multiplying_columns_prefix: str
) -> pd.DataFrame:
    # Create one-hot encoded binary matrix for the beer styles
    beer_styles_one_hot_encoding = pd.get_dummies(
        df_ratings[dummy_column], dtype=int, prefix="user_past_ratings"
    ).replace(0, pd.NA)

    # Multiply the binary matrix with the past ratings count and average corresponding to the current rating style
    df_user_beer_style_past_ratings = pd.merge(
        beer_styles_one_hot_encoding.mul(
            df_ratings[f"{multiplying_columns_prefix}_past_ratings_count"], axis=0
        ),
        beer_styles_one_hot_encoding.mul(
            df_ratings[f"{multiplying_columns_prefix}_past_ratings_average"], axis=0
        ),
        left_index=True,
        right_index=True,
        suffixes=("_count", "_average"),
    )

    modified_columns = [
        column
        for column in df_user_beer_style_past_ratings.columns
        if ("_count" in column or "_average" in column)
    ]

    # Merge to get the user id and date in order to forward fill the values within groups of user_id
    df_user_beer_style_past_ratings = df_user_beer_style_past_ratings.merge(
        df_ratings[["user_id", "date", "beer_id"]],
        left_index=True,
        right_index=True,
        how="left",
    )

    # Ensure duplicate are well sorted by the next sorting
    df_user_beer_style_past_ratings.sort_index(inplace=True)

    # Fill forward the values within groups of user_id
    df_user_beer_style_past_ratings[modified_columns] = (
        df_user_beer_style_past_ratings.sort_values(["user_id", "date"], kind="stable")
        .groupby("user_id")
        .ffill()[modified_columns]
    )

    # Shift the value forward to have the counts and average without taking into
    # account the current rating (since counts and average are computed taking
    # into account current rating)
    df_user_beer_style_past_ratings[modified_columns] = (
        df_user_beer_style_past_ratings.sort_values(["user_id", "date"], kind="stable")
        .groupby("user_id")
        .shift(1)[modified_columns]
    )

    # Fill remaining cells with 0 as they are cells of ratings occuring before
    # the first rating in a given beer style
    df_user_beer_style_past_ratings[modified_columns] = df_user_beer_style_past_ratings[
        modified_columns
    ].fillna(0.0)

    return df_user_beer_style_past_ratings
