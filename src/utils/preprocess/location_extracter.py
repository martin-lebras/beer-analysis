import pandas as pd
from thefuzz import process
import json

DF_ISO_CODES = pd.read_csv("src/data/iso_codes.csv")[["name", "alpha-3"]]

# Map region to country (useful when we only have the region)
with open("src/data/region_to_country.json", "r") as region_to_country_file:
    REGION_TO_COUNTRY = json.load(region_to_country_file)


# Try to get the country code from the country using fuzzy matching
def get_closest_match_or_none(
    query: str, serie_choices: pd.Series, serie_values: pd.Series, threshold: int = 80
):
    match, score, _ = process.extractOne(query, serie_choices)
    if score >= threshold:
        return serie_values[serie_choices == match].values[0]
    return None


def extract_location(
    serie_locations: pd.Series,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    serie_locations.replace(
        {
            "UNKNOWN": pd.NA,
            "Swaziland": "Esawtini",  # Swaziland changed its name to Esawtini
            "Northern Ireland": "United Kingdom, Northern Ireland",  # Northern Ireland is part of the United Kingdom
            "Aotearoa": "New Zealand",  # Aotearoa is the Maori name for New Zealand
            "Nagorno-Karabakh": "Azerbaijan",  # Nagorno-Karabakh is a disputed territory (currenlty controlled by Azerbaijan)
            "Transdniestra": "Moldova",  # Transdniestra is a disputed territory (currenlty controlled by Moldova)
            "Tibet": "China",  # Tibet is an autonomous region of China
            "Abkhazia": "Georgia",  # Abkhazia is a disputed territory (currenlty controlled by Georgia)
        },
        inplace=True,
    )

    # Match location with Google Maps links and extract the location (before the </a> tag)
    extracted_location_matches = serie_locations.str.extract(r"^(.*?)(?=</a>)|^(.*)$")
    serie_locations = extracted_location_matches[0].fillna(
        extracted_location_matches[1]
    )

    splits = serie_locations.str.split(", ", expand=True)
    splits.rename(columns={0: "country", 1: "region"}, inplace=True)

    # Replace occurence of regions that were considered as countries
    splits["country"] = splits["country"].replace(REGION_TO_COUNTRY)

    # Try to match the country with the ISO code (exact match)
    splits = splits.merge(
        DF_ISO_CODES[["name", "alpha-3"]],
        left_on="country",
        right_on="name",
        how="left",
    )

    # Try to match the country with ISO code (fuzzy match)
    splits["alpha-3"] = splits.apply(
        lambda row: (
            row["alpha-3"]
            if pd.notna(row["alpha-3"]) or pd.isna(row["country"])
            else get_closest_match_or_none(
                row["country"], DF_ISO_CODES["name"], DF_ISO_CODES["alpha-3"]
            )
        ),
        axis=1,
    )

    splits.loc[splits["country"] == "Kosovo", "alpha-3"] = (
        "XKX"  # Kosovo is not in the ISO list
    )
    splits.loc[splits["country"] == "Vatican City", "alpha-3"] = (
        "VAT"  # Vatican City is not in the ISO list
    )

    return splits["country"], splits["region"], splits["alpha-3"]
