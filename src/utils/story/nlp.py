import pandas as pd
import numpy as np
import networkx as nx
from statsmodels.stats.multicomp import pairwise_tukeyhsd


def tukey_test(
    dataframe: pd.DataFrame, group_column: str, value_column: str, alpha: float = 0.05
) -> pd.DataFrame:
    tukey = pairwise_tukeyhsd(
        endog=dataframe[value_column], groups=dataframe[group_column], alpha=alpha
    )
    raw_results = np.array(tukey.summary().data)

    df_tukey = pd.DataFrame(raw_results[1:], columns=[str(c) for c in raw_results[0]])
    df_tukey = df_tukey[df_tukey["reject"] == "True"]
    df_tukey = df_tukey.drop(columns=["reject"])

    df_tukey["weight"] = 1 - df_tukey["p-adj"].astype(float)
    df_tukey["difference"] = df_tukey["meandiff"].astype(float)
    df_tukey["absolute_difference"] = df_tukey["difference"].abs()
    df_tukey = df_tukey.drop(columns=["p-adj", "meandiff"])

    return df_tukey


def create_digraph(
    dataframe_tuckey: pd.DataFrame,
    dataframe_region: pd.DataFrame,
    nlp_error_column: str,
    threshold: float = 0.01,
) -> nx.DiGraph:
    G = nx.DiGraph()

    for _, row in dataframe_tuckey.iterrows():
        if row["absolute_difference"] < threshold:
            continue

        G.add_node(
            row["group1"],
            mean_error=dataframe_region[
                dataframe_region["user_country_region"] == row["group1"]
            ][nlp_error_column].mean(),
        )
        G.add_node(
            row["group2"],
            mean_error=dataframe_region[
                dataframe_region["user_country_region"] == row["group2"]
            ][nlp_error_column].mean(),
        )

        if row["difference"] < 0:
            G.add_edge(
                row["group2"],
                row["group1"],
                weight=row["absolute_difference"],
                difference=row["absolute_difference"],
            )
        else:
            G.add_edge(
                row["group1"],
                row["group2"],
                weight=row["absolute_difference"],
                difference=row["absolute_difference"],
            )

    return G
