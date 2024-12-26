import pandas as pd
from location_extracter import extract_location


def preprocess_ba_beers(
    df_beers: pd.DataFrame, df_beers_styles: pd.DataFrame
) -> pd.DataFrame:
    df_beers.rename(
        columns={
            "style": "beer_style",
            "nbr_ratings": "ratings_count",
            "nbr_reviews": "reviews_count",
            "avg": "ratings_average",
            "ba_score": "ratings_ba_score",
            "bros_score": "ratings_bros_score",
            "abv": "beer_alcohol_by_volume",
            "avg_computed": "ratings_average_computed",
            "nbr_matched_valid_ratings": "matching_ratings_count",
            "avg_matched_valid_ratings": "matching_ratings_average",
        },
        inplace=True,
    )

    df_beers.drop(columns=["brewery_name"], inplace=True, errors="ignore")

    df_beers = df_beers[
        [
            "beer_id",
            "brewery_id",
            "beer_name",
            "beer_style",
            "ratings_count",
            "reviews_count",
            "ratings_average",
            "ratings_ba_score",
            "ratings_bros_score",
            "beer_alcohol_by_volume",
            "ratings_average_computed",
            "zscore",
            "matching_ratings_count",
            "matching_ratings_average",
        ]
    ]

    df_beers = df_beers.merge(df_beers_styles, on="beer_style", how="left")

    return df_beers


def preprocess_ba_breweries(df_breweries: pd.DataFrame) -> pd.DataFrame:
    df_breweries.rename(
        columns={
            "id": "brewery_id",
            "location": "brewery_location",
            "name": "brewery_name",
            "nbr_beers": "brewery_beers_count",
        },
        inplace=True,
    )

    # Location of two breweries were missing, we found their location using Google
    df_breweries.loc[df_breweries["brewery_id"] == 18989, "brewery_location"] = (
        "United States"
    )
    df_breweries.loc[df_breweries["brewery_id"] == 11016, "brewery_location"] = (
        "Austria"
    )

    (
        df_breweries["brewery_country"],
        df_breweries["brewery_region"],
        df_breweries["brewery_country_code"],
    ) = extract_location(df_breweries["brewery_location"])
    df_breweries.drop(columns=["brewery_location"], inplace=True)

    return df_breweries


def preprocess_ba_users(df_users: pd.DataFrame) -> pd.DataFrame:
    df_users.rename(
        columns={
            "joined": "user_created_date",
            "location": "user_location",
            "nbr_ratings": "user_ratings_count",
            "nbr_reviews": "user_reviews_count",
        },
        inplace=True,
    )

    df_users["user_country"], df_users["user_region"], df_users["user_country_code"] = (
        extract_location(df_users["user_location"])
    )
    df_users.drop(columns=["user_location"], inplace=True)

    return df_users


def preprocess_ba_ratings(df_ratings: pd.DataFrame) -> pd.DataFrame:
    df_ratings.drop(
        columns=["user_name", "brewery_name", "beer_name", "style", "abv"],
        inplace=True,
        errors="ignore",
    )
    df_ratings = df_ratings[
        [
            "user_id",
            "beer_id",
            "brewery_id",
            "date",
            "review",
            "rating",
            "overall",
            "aroma",
            "appearance",
            "palate",
            "taste",
            "text",
        ]
    ]

    return df_ratings


def preprocess_rb_beers(df_beers: pd.DataFrame) -> pd.DataFrame:
    df_beers = df_beers.drop(columns=["brewery_name"])

    df_beers = df_beers.rename(
        columns={
            "style": "beer_style",
            "nbr_ratings": "ratings_count",
            "avg": "ratings_average",
            "overall_score": "ratings_overall_score",
            "abv": "beer_alcohol_by_volume",
            "avg_computed": "ratings_average_computed",
            "nbr_matched_valid_ratings": "matching_ratings_count",
            "avg_matched_valid_ratings": "matching_ratings_average",
        }
    )

    # Remove Saké as they are not beers
    df_beers = df_beers[~df_beers["beer_style"].str.contains("Saké")]

    # Remove Cider as they are not beers
    df_beers = df_beers[~df_beers["beer_style"].str.contains("Cider")]

    return df_beers


def preprocess_rb_beers_style(
    df_beers: pd.DataFrame, df_beers_styles: pd.DataFrame, threshold: int = 90
) -> pd.DataFrame:
    beer_style_to_global_style = {
        "Barley Wine": "Strong Ale",
        "Amber Ale": "Pale Ale",
        "Imperial Pils/Strong Pale Lager": "Pale Lager",
        "Golden Ale/Blond Ale": "Pale Ale",
        "Spice/Herb/Vegetable": "Specialty Beer",
        "Sour/Wild Ale": "Wild/Sour Beer",
        "Fruit Beer": "Speciality Beer",
        "Premium Bitter/ESB": "Pale Ale",
        "Session IPA": "India Pale Ale",
        "Specialty Grain": "Specialty Beer",
        "Dunkel/Tmavý": "Dark Lager",
        "Amber Lager/Vienna": "Dark Lager",
        "Dortmunder/Helles": "Pale Lager",
        "Premium Lager": "Pale Lager",
        "Czech Pilsner (Světlý)": "Pale Lager",
        "Zwickel/Keller/Landbier": "Pale Lager",
        "Radler/Shandy": "Pale Lager",
        "Sour Red/Brown": "Wild/Sour Beer",
    }

    for beer_style in df_beers["beer_style"].unique():

        if beer_style in beer_style_to_global_style:
            continue

        match, score, _ = process.extractOne(beer_style, df_beers_styles["beer_style"])
        if score >= threshold:
            beer_style_to_global_style[beer_style] = df_beers_styles[
                df_beers_styles["beer_style"] == match
            ]["beer_global_style"].values[0]
        else:
            beer_style_to_global_style[beer_style] = pd.NA

    df_beers["beer_global_style"] = df_beers["beer_style"].map(
        beer_style_to_global_style
    )

    return df_beers


def preprocess_rb_breweries(df_breweries: pd.DataFrame) -> pd.DataFrame:
    df_breweries = df_breweries.rename(
        columns={
            "id": "brewery_id",
            "location": "brewery_location",
            "name": "brewery_name",
            "nbr_beers": "brewery_beers_count",
        }
    )

    (
        df_breweries["brewery_country"],
        df_breweries["brewery_region"],
        df_breweries["brewery_country_code"],
    ) = extract_location(df_breweries["brewery_location"])
    df_breweries = df_breweries.drop(columns=["brewery_location"])

    return df_breweries


def preprocess_rb_users(df_users: pd.DataFrame) -> pd.DataFrame:
    df_users = df_users.sort_values("joined", kind="stable")
    df_users = df_users.groupby("user_id").last().reset_index()

    df_users = df_users.rename(
        columns={
            "joined": "user_created_date",
            "location": "user_location",
            "nbr_ratings": "user_ratings_count",
        }
    )

    df_users["user_country"], df_users["user_region"], df_users["user_country_code"] = (
        extract_location(df_users["user_location"])
    )
    df_users = df_users.drop(columns=["user_location"])

    return df_users


def preprocess_rb_ratings(
    df_ratings: pd.DataFrame, df_beers: pd.DataFrame
) -> pd.DataFrame:
    df_ratings = df_ratings.drop(
        columns=["user_name", "brewery_name", "beer_name", "style", "abv"],
        errors="ignore",
    )

    df_ratings = df_ratings.sort_values("date")
    df_ratings = df_ratings.groupby(["user_id", "beer_id"]).last().reset_index()

    df_ratings = df_ratings[
        [
            "user_id",
            "beer_id",
            "brewery_id",
            "date",
            "rating",
            "overall",
            "aroma",
            "appearance",
            "palate",
            "taste",
            "text",
        ]
    ]

    # Drop ratings corresponding to dropped beers (see above)
    df_ratings = df_ratings[df_ratings["beer_id"].isin(df_beers["beer_id"])]
    return df_ratings


def compute_gini_impurity(
    df_ratings: pd.DataFrame, df_user_beer_style_past_ratings: pd.DataFrame
) -> pd.DataFrame:
    count_columns = [
        column
        for column in df_user_beer_style_past_ratings.columns
        if column.endswith("_count")
    ]

    total_ratings = df_user_beer_style_past_ratings[count_columns].sum(axis=1)
    proportions = (
        df_user_beer_style_past_ratings[count_columns]
        .div(total_ratings, axis=0)
        .fillna(0)
    )

    df_ratings["gini_impurity"] = (1 - (proportions**2).sum(axis=1)) / (
        1 - 1 / len(count_columns)
    )
    return df_ratings
