import pandas as pd


def describe_dataframe(dataframe: pd.DataFrame, site: str, name: str):
    print(
        f"[{site}] Dataframe contains {dataframe.shape[0]} rows and {dataframe.shape[1]} columns"
    )
    dataframe.isna().mean(axis=0).sort_values().plot(
        figsize=(6, 3),
        kind="barh",
        title=f"[{site}] Missing values in {name} dataset",
        xlabel="Proportion of missing values",
    )
