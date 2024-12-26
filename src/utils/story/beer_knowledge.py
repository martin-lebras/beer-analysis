import pandas as pd
import numpy as np


def number_of_beer_per_style(df_ratings: pd.DataFrame) -> pd.DataFrame:
    """Gets the total number of available beers per beer style on each day

    Arguments:
        df_ratings: a pandas DataFrame with the ratings of the users for the beers, their ids, their styles and the day of the rating

    Returns:
        df_current_berr_per_style: a pandas DataFrame with the number of beers available per beer style on each day
    """
    # Get the day of the first rating for each beer
    df_beer_first_app = (
        df_ratings[["beer_id", "day", "beer_global_style"]]
        .groupby(["beer_global_style", "beer_id"])
        .min()
        .reset_index()
    )
    # Transform the dataframe by creating dummy columns for the beer styles and dropping the initial beer_style column
    df_beer_first_app = pd.concat(
        [
            df_beer_first_app,
            pd.get_dummies(df_beer_first_app["beer_global_style"], prefix="max").astype(
                int
            ),
        ],
        axis=1,
    ).drop(["beer_global_style", "beer_id"], axis=1)
    # Get the number of new beer per day per style
    df_new_beer_per_day_style = (
        df_beer_first_app.groupby("day").sum().sort_values(by="day").reset_index()
    )
    # Get the number of available beer per beer style on each day of appearance of new beers
    df_current_beer_per_style = pd.concat(
        [
            df_new_beer_per_day_style["day"],
            df_new_beer_per_day_style.drop("day", axis=1).cumsum(),
        ],
        axis=1,
    )
    # Create the full dates dataframe for the period of the study
    df_dates = pd.DataFrame(
        {
            "day": pd.date_range(
                start=pd.to_datetime(df_ratings["day"].min()),
                end=pd.to_datetime(df_ratings["day"].max()),
                freq="D",
            )
        }
    )
    # Get the number of available beer per beer style on each day of the study
    df_current_beer_per_style = (
        df_dates.merge(df_current_beer_per_style, how="left", on="day")
        .sort_values(by="day")
        .ffill()
    )

    return df_current_beer_per_style


def add_global_knowledge(
    df_current_beer_per_style_year: pd.DataFrame,
    df_users_past_beer_style: pd.DataFrame,
    count_columns: list,
) -> tuple[pd.DataFrame]:
    """Adds the global knowledge for each user at the time of their ratings

    Arguments:
        df_current_beer_per_style_year: a pandas DataFrame with the number of beers available per beer style on each day
        df_user_past_beer_style: a pandas dataframe with the past counts of each beer style for the users at the time of rating
        count_columns: a list of strings with the name of the columns containing the past counts of each beer style for the users at the time of rating

    Returns:
        df_user_past_beer_style: a pandas dataframe with the past counts of each beer style for the users at the time of rating updated with the global knowledge
    """
    # Get the total number of beer styles
    n_beer_style = len(count_columns)
    # Get the mean number of available beers across the styles on each day
    df_mean_beers = pd.concat(
        [
            df_current_beer_per_style_year["day"],
            df_current_beer_per_style_year.iloc[:, 1:].mean(axis=1),
        ],
        axis=1,
    ).rename(columns={0: "mean_beers"})
    # Get the number of style tried by the users at the time of the ratings
    df_users_past_beer_style["style_tried"] = np.sign(
        df_users_past_beer_style[count_columns]
    ).sum(axis=1)
    # Get the share of styles tried by the users at the time of the ratings
    df_users_past_beer_style["style_tried_share"] = (
        df_users_past_beer_style["style_tried"] / n_beer_style
    )
    # Get the mean number of tried beers across the styles by the users at the time of the ratings
    df_users_past_beer_style["mean_beer_tried"] = (
        df_users_past_beer_style[count_columns].sum(axis=1)
        / df_users_past_beer_style["style_tried"]
    )
    # Add the column of the mean number of available beers across the styles to the main dataframe
    df_users_past_beer_style = df_users_past_beer_style.merge(
        df_mean_beers, how="left", on="day"
    )
    # Set the mean beer tried to zero when not a style has been previously tried, it means it's the first rating of the user
    df_users_past_beer_style.loc[
        df_users_past_beer_style["style_tried"] == 0, "mean_beer_tried"
    ] = 0
    # Combine the previously calculated columns to compute the global knowledge for each user at the time of the rating
    df_users_past_beer_style["global_knowledge"] = (
        df_users_past_beer_style["style_tried_share"]
        * np.log(1 + df_users_past_beer_style["mean_beer_tried"])
        / np.log(1 + df_users_past_beer_style["mean_beers"])
    )

    return df_users_past_beer_style


def add_local_knowledge(
    df_current_beer_per_style_year: pd.DataFrame,
    df_users_past_beer_style: pd.DataFrame,
    max_columns: list,
    count_columns: list,
) -> tuple[pd.DataFrame]:
    """Computes the local knowledge for each user in each beer style at the time of their ratings and adds the maximum local knowledge to the main dataframe

    Arguments:
        df_current_beer_per_style_year: a pandas DataFrame with the number of beers available per beer style on each day
        df_users_past_beer_style: a pandas dataframe with the past counts of each beer style for the users at the time of rating
        max_columns: a list of strings with the name of the columns containing the number of available beers of each beer style on each day
        count_columns: a list of strings with the name of the columns containing the past counts of each beer style for the users at the time of rating

    Returns:
        df_users_past_beer_style: a pandas dataframe with the past counts of each beer style for the users at the time of rating updated with their maximum local knowledge
        df_local_knowledge: a pandas dataframe with the local knowledge of the users in each beer style at the time of their ratings
    """
    # Add the number of available beers for each beer style on the day of the ratings of the users to the main dataframe
    df_users_past_beer_style = df_users_past_beer_style.merge(
        df_current_beer_per_style_year, how="left", on="day"
    )
    # Sort the dataframe by user_id, day and the number of past beers rated for each beer style on each day by each user
    # to make sure the rows are in ascending order both chronologically and in terms of count
    df_users_past_beer_style.sort_values(by=["user_id", "day"] + count_columns)
    # Compute the share of beers tried in each style for each user at the time of the ratings
    df_shares_by_style = pd.DataFrame(
        df_users_past_beer_style[count_columns].values
        / df_users_past_beer_style[max_columns].values
    )
    # Apply a cubic root in order to spread the distribution and better match the global knowledge distribution
    df_local_knowledge = np.power(df_shares_by_style, 1 / 3)
    # Rename the columns as the names were lost when computing the shares per beer style
    df_local_knowledge.rename(
        columns={
            0: "Bock",
            1: "Brown Ale",
            2: "Dark Ales",
            3: "Dark Lager",
            4: "Hybrid Beer",
            5: "India Pale Ale",
            6: "Pale Ale",
            7: "Pale Lager",
            8: "Porter",
            9: "Speciality Beer",
            10: "Stout",
            11: "Strong Ale",
            12: "Wheat Beer",
            13: "Wild/Sour Beer",
        },
        inplace=True,
    )
    # Add back the user_id, day and beer_id to the local knowledge dataframe
    df_local_knowledge = df_local_knowledge.merge(
        df_users_past_beer_style[["user_id", "day", "beer_id"]],
        how="inner",
        left_index=True,
        right_index=True,
    )
    # Get the maximum local knowledge across the the beer styles for each knowledge
    df_users_past_beer_style["local_knowledge"] = df_local_knowledge.iloc[:, :-3].max(
        axis=1
    )

    return df_users_past_beer_style, df_local_knowledge


def add_all_knowledge(
    df_user_beer_style_past_ratings: pd.DataFrame,
    df_current_beer_per_style: pd.DataFrame,
):
    # Get the list of columns with the count and max values for each beer style
    count_columns = [
        col for col in df_user_beer_style_past_ratings.columns if "count" in col
    ]
    max_columns = [col for col in df_current_beer_per_style.columns if "max" in col]

    # Add the global and local knowledge
    df_user_beer_style_past_ratings = add_global_knowledge(
        df_current_beer_per_style, df_user_beer_style_past_ratings, count_columns
    )
    df_user_beer_style_past_ratings, df_local_knowledge = add_local_knowledge(
        df_current_beer_per_style,
        df_user_beer_style_past_ratings,
        max_columns,
        count_columns,
    )

    # Create the knowledge dataframe
    df_knowledge = df_user_beer_style_past_ratings[
        [
            "user_id",
            "day",
            "beer_id",
            "global_knowledge",
            "local_knowledge",
            "style_tried",
        ]
    ]
    df_knowledge.loc[:, "knowledge"] = (
        df_knowledge["global_knowledge"] + df_knowledge["local_knowledge"]
    ) / 2

    # Set to NaN the zero local knowedge meaning it is the first rating of the user
    df_knowledge.loc[:, "local_knowledge"] = df_knowledge.loc[
        :, "local_knowledge"
    ].replace(0, np.nan)

    return (
        df_user_beer_style_past_ratings,
        df_knowledge,
        df_local_knowledge,
        max_columns,
    )


def add_experts(
    df_local_knowledge: pd.DataFrame,
    df_users_past_beer_style: pd.DataFrame,
    quantile_thresh: float,
) -> tuple[pd.DataFrame]:
    """Adds the expert information to each user for each beer style at the time of the ratings

    Arguments:
        df_local_knowledge: a pandas dataframe with the local knowledge of the users in each beer style at the time of their ratings
        df_users_past_beer_style: a pandas dataframe with the past counts of each beer style for the users at the time of rating
        quantile_thresh: a scalar denoting the quantile chosen to define the share of expert in the population

    Returns:
        df_users_past_beer_style: a pandas dataframe with the past counts of each beer style for the users at the time of rating
        df_local_knowledge_quantile_expert: a pandas dataframe with the local knowledge to reach to be an expert
    """
    # Get the best local knowledge for each user in each beer style
    df_best_local_per_user = (
        df_local_knowledge.iloc[:, :-1].groupby("user_id").max().reset_index()
    )
    # Get the threshold of local knowledge to be an expert for each beer style based on the chosen quantile
    df_local_knowledge_quantile_expert = (
        df_best_local_per_user.iloc[:, 1:-1]
        .replace(0, np.nan)
        .quantile(quantile_thresh)
    )
    # Get the information for each user at the time of each rating if they are expert for each style
    above_percentiles = (
        df_local_knowledge.iloc[:, :-3]
        .gt(df_local_knowledge_quantile_expert, axis=1)
        .astype(int)
    )
    # Rename the columns to add the "expert" suffix
    for col in above_percentiles.columns:
        above_percentiles.rename(columns={col: col + "_expert"}, inplace=True)
    # Add the expert information to the main dataframe
    df_users_past_beer_style = df_users_past_beer_style.merge(
        above_percentiles, how="inner", left_index=True, right_index=True
    )
    return df_users_past_beer_style, df_local_knowledge_quantile_expert


def add_novices(
    df_local_knowledge: pd.DataFrame,
    df_users_past_beer_style: pd.DataFrame,
    quantile_thresh: float,
) -> tuple[pd.DataFrame]:
    """Adds the novice information to each user for each beer style at the time of the ratings

    Arguments:
        df_local_knowledge: a pandas dataframe with the local knowledge of the users in each beer style at the time of their ratings
        df_users_past_beer_style: a pandas dataframe with the past counts of each beer style for the users at the time of rating
        quantile_thresh: a scalar denoting the quantile chosen to define the share of novice in the population

    Returns:
        df_users_past_beer_style: a pandas dataframe with the past counts of each beer style for the users at the time of rating
        df_local_knowledge_quantile_expert: a pandas dataframe with the local knowledge to reach to be an novice
    """
    df_best_local_per_user = (
        df_local_knowledge.iloc[:, :-1].groupby("user_id").max().reset_index()
    )
    # Get the threshold of local knowledge to be a novice for each beer style based on the chosen quantile
    df_local_knowledge_quantile_novice = (
        df_best_local_per_user.iloc[:, 1:-1]
        .replace(0, np.nan)
        .quantile(quantile_thresh)
    )
    # Get the information for each user at the time of each rating if they are novice for each style
    below_percentiles = (
        df_local_knowledge.iloc[:, :-3]
        .lt(df_local_knowledge_quantile_novice, axis=1)
        .astype(int)
    )
    # Rename the columns to add the "novice" suffix
    for col in below_percentiles.columns:
        below_percentiles.rename(columns={col: col + "_novice"}, inplace=True)
    # Add the novice information to the main dataframe
    df_users_past_beer_style = df_users_past_beer_style.merge(
        below_percentiles, how="inner", left_index=True, right_index=True
    )
    return df_users_past_beer_style, df_local_knowledge_quantile_novice


def get_beer_required_expert(
    df_user_beer_style_past_ratings: pd.DataFrame,
    df_local_knowledge_quantile_expert: pd.DataFrame,
    max_columns: list,
):
    """Gets the number of beers required to be an expert for each beer style on each day

    Arguments:
        df_user_beer_style_past_ratings: a pandas dataframe with the past counts of each beer style for the users at the time of rating
        df_local_knowledge_quantile_expert: a pandas dataframe with the local knowledge to reach to be an expert

    Returns:
        df_beer_required_to_be_expert_long: a pandas dataframe with the number of beers required to be an expert for each beer style on each date
    """
    # Get the available beers for each beer style by day
    max_available_beer_per_day = (
        df_user_beer_style_past_ratings[max_columns + ["day"]]
        .groupby("day")
        .max()
        .reset_index()
    )
    # Rename the columns to use column-wise multiplication between dataframes
    max_available_beer_per_day.columns = [
        "day"
    ] + df_local_knowledge_quantile_expert.index.to_list()
    # Get the number of beers to rate from the local knowledge to reach and the number of available beers per style
    max_available_beer_per_day.iloc[:, 1:] = max_available_beer_per_day.iloc[
        :, 1:
    ] * np.power(df_local_knowledge_quantile_expert, 3)
    # Melt the dataframe to a format better suited for visualisation
    df_beer_required_to_be_expert_long = max_available_beer_per_day.melt(
        id_vars="day", var_name="Beer Style", value_name="Beers to be expert"
    )
    return df_beer_required_to_be_expert_long


def get_expert_count(
    df_user_beer_style_past_ratings: pd.DataFrame, df_users: pd.DataFrame
):
    """Gets dataframes with the number of experts per beer style and country

    Arguments:
        df_user_beer_style_past_ratings: a pandas dataframe with the past counts of each beer style for the users at the time of rating
        df_users: a pandas dataframe with information about users including their country

    Returns:
        df_expert_users: a pandas dataframe with the user who were experts at some point, the beer styles they were experts in and their countries
        df_count_exp: a pandas dataframe with the the number of unique experts per country
        expert_columns: a list with the names of the column referring to the expertise of the users in each beer style
    """
    expert_columns = [
        col for col in df_user_beer_style_past_ratings.columns if "expert" in col
    ]

    # Get the users who were experts at some point and add their countries
    df_user_beer_style_past_ratings.loc[:, "isExpert"] = (
        df_user_beer_style_past_ratings[expert_columns].sum(axis=1)
    )
    df_expert_users = (
        df_user_beer_style_past_ratings.loc[
            df_user_beer_style_past_ratings["isExpert"] >= 1,
            ["user_id"] + expert_columns,
        ]
        .groupby("user_id")
        .max()
        .reset_index()
    )
    df_expert_users = df_expert_users.merge(
        df_users[["user_id", "user_country_code", "user_country"]],
        how="left",
        on="user_id",
    )

    # Add the log count of users for better visibility due to the massive count of the USA
    df_count_exp = df_expert_users["user_country_code"].value_counts().reset_index()
    df_count_exp["log_count"] = np.log(df_count_exp["count"])
    return df_expert_users, df_count_exp, expert_columns


def get_novice_count(
    df_user_beer_style_past_ratings: pd.DataFrame, df_users: pd.DataFrame
):
    """Gets dataframes with the number of novice per beer style and country

    Arguments:
        df_user_beer_style_past_ratings: a pandas dataframe with the past counts of each beer style for the users at the time of rating
        df_users: a pandas dataframe with information about users including their country

    Returns:
        df_novice_users: a pandas dataframe with the user who were novices at some point, the beer styles they were novices in and their countries
        df_count_nov: a pandas dataframe with the the number of unique novice per country
        novice_columns: a list with the names of the column referring to the novice info of the users in each beer style
    """
    novice_columns = [
        col for col in df_user_beer_style_past_ratings.columns if "novice" in col
    ]

    # Get the users who were experts at some point and add their countries
    df_user_beer_style_past_ratings.loc[:, "isNovice"] = (
        df_user_beer_style_past_ratings[novice_columns].sum(axis=1)
    )
    df_novice_users = (
        df_user_beer_style_past_ratings.loc[
            df_user_beer_style_past_ratings["isNovice"] >= 1,
            ["user_id"] + novice_columns,
        ]
        .groupby("user_id")
        .max()
        .reset_index()
    )
    df_novice_users = df_novice_users.merge(
        df_users[["user_id", "user_country_code", "user_country"]],
        how="left",
        on="user_id",
    )

    # Add the log count of users for better visibility due to the massive count of the USA
    df_count_nov = df_novice_users["user_country_code"].value_counts().reset_index()
    df_count_nov["log_count"] = np.log(df_count_nov["count"])
    return df_novice_users, df_count_nov, novice_columns


def get_mean_expert_vs_non(
    df_ratings: pd.DataFrame,
    df_user_beer_style_past_ratings: pd.DataFrame,
    expert_columns: list,
    k: int = 100,
) -> pd.DataFrame:
    """Gets the mean ratings for experts and non experts for each beer style

    Arguments:
        df_ratings: a pandas dataframe with the ratings of the users and the beer style
        df_user_beer_style_past_ratings: a pandas dataframe with the expertise of each beer style for the users at the time of rating
        expert_columns: a list with the names of the column referring to the expertise of the users in each beer style
        k: a scalar denoting the number of beers to consider

    Returns:
        df_means_all_styles: a pandas dataframe with the ratings of experts and non-experts users in beer styles on the selected beers
    """
    df_expert_ratings = (
        df_user_beer_style_past_ratings[expert_columns + ["day", "user_id", "beer_id"]]
        .groupby(["user_id", "day"])
        .max()
        .reset_index()
        .merge(
            df_ratings[["user_id", "day", "beer_global_style", "rating"]],
            how="inner",
            on=["user_id", "day"],
        )
    )
    df_means = []
    for style in expert_columns:
        beer_rated_by_experts = df_expert_ratings[(df_expert_ratings[style] == 1)][
            "beer_id"
        ].unique()
        top_k_beers = (
            df_ratings[
                (df_ratings["beer_global_style"] == style.split("_")[0])
                & (df_ratings["beer_id"].isin(beer_rated_by_experts))
            ][["rating", "beer_id"]]
            .groupby("beer_id")
            .count()
            .reset_index()
            .sort_values(by="rating", ascending=False)
            .head(k)["beer_id"]
            .to_numpy()
        )
        df_same_beers = df_expert_ratings[
            (df_expert_ratings["beer_global_style"] == style.split("_")[0])
            & (df_expert_ratings["beer_id"].isin(top_k_beers))
        ]
        df_means.append(
            df_same_beers[["beer_global_style", "rating", style]].rename(
                columns={style: "expert"}
            )
        )
    df_means_all_styles = pd.concat(df_means, axis=0)
    return df_means_all_styles


def get_expert_vs_novice(
    df_ratings: pd.DataFrame,
    df_user_beer_style_past_ratings: pd.DataFrame,
    expert_columns: list,
    novice_columns: list,
    k: int = 100,
) -> pd.DataFrame:
    """Gets the mean ratings for experts and non experts for each beer style

    Arguments:
        df_ratings: a pandas dataframe with the ratings of the users and the beer style
        df_user_beer_style_past_ratings: a pandas dataframe with the expertise of each beer style for the users at the time of rating
        expert_columns: a list with the names of the column referring to the expertise of the users in each beer style
        expert_columns: a list with the names of the column referring to the novice info of the users in each beer style
        k: a scalar denoting the number of beers to consider

    Returns:
        df_means_all_styles: a pandas dataframe with the ratings of experts and novice users in beer styles on the selected beers
    """
    df_expert_novice_ratings = (
        df_user_beer_style_past_ratings[
            expert_columns + novice_columns + ["day", "user_id", "beer_id"]
        ]
        .groupby(["user_id", "day"])
        .max()
        .reset_index()
        .merge(
            df_ratings[["user_id", "day", "beer_global_style", "rating"]],
            how="inner",
            on=["user_id", "day"],
        )
    )
    df_means = []
    for style in expert_columns:
        beer_rated_by_experts = df_user_beer_style_past_ratings[
            (df_user_beer_style_past_ratings[style] == 1)
        ]["beer_id"].unique()
        beer_rated_by_novices = df_user_beer_style_past_ratings[
            (df_user_beer_style_past_ratings[style.replace("expert", "novice")] == 1)
        ]["beer_id"].unique()
        top_k_beers = (
            df_ratings[
                (df_ratings["beer_global_style"] == style.split("_")[0])
                & (df_ratings["beer_id"].isin(beer_rated_by_experts))
                & (df_ratings["beer_id"].isin(beer_rated_by_novices))
            ][["rating", "beer_id"]]
            .groupby("beer_id")
            .count()
            .reset_index()
            .sort_values(by="rating", ascending=False)
            .head(k)["beer_id"]
            .to_numpy()
        )
        df_same_beers = df_expert_novice_ratings[
            (df_expert_novice_ratings["beer_global_style"] == style.split("_")[0])
            & (df_expert_novice_ratings["beer_id"].isin(top_k_beers))
            & (
                (df_expert_novice_ratings[style] == 1)
                | (df_expert_novice_ratings[style.replace("expert", "novice")] == 1)
            )
        ]
        df_means.append(
            df_same_beers[["beer_global_style", "rating", style]].rename(
                columns={style: "expert_or_novice"}
            )
        )
    df_means_all_styles = pd.concat(df_means, axis=0)
    return df_means_all_styles
