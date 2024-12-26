import pandas as pd
import numpy as np
import torch
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from torch.nn.functional import softmax
import networkx as nx
from statsmodels.stats.multicomp import pairwise_tukeyhsd


def compute_weighted_rating(df_predictions: pd.DataFrame) -> pd.DataFrame:
    def _compute_weighted_rating(rating_weights: pd.Series):
        prediction = int(rating_weights.idxmax())

        values = [prediction]
        weights = [rating_weights.max()]

        if prediction > 1:
            values.append(prediction - 1)
            weights.append(rating_weights.loc[str(prediction - 1)])

        if prediction < 5:
            values.append(prediction + 1)
            weights.append(rating_weights.loc[str(prediction + 1)])

        return np.average(values, weights=weights), np.sum(weights)
    return df_predictions.apply(_compute_weighted_rating, axis=1)


def predict_rating(reviews: pd.Series) -> pd.DataFrame:
    HUGGING_FACE_MODEL = "nlptown/bert-base-multilingual-uncased-sentiment"

    tokenizer = AutoTokenizer.from_pretrained(HUGGING_FACE_MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(HUGGING_FACE_MODEL)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    encoded_input = tokenizer(reviews.tolist(), padding=True, truncation=True, max_length=512, return_tensors='pt')
    encoded_input = {key: tensor.to(device) for key, tensor in encoded_input.items()}
    with torch.no_grad():
        output = model(**encoded_input)
    scores = softmax(output.logits, dim=1)

    df_predictions = pd.DataFrame([
        *scores.cpu().numpy()
    ], columns=['1', '2', '3', '4', '5'], index=reviews.index)

    df_predictions = pd.merge(df_predictions, compute_weighted_rating(df_predictions), left_index=True, right_index=True)
    df_predictions.columns = ['1', '2', '3', '4', '5', 'nlp_weighted_rating', 'nlp_weighted_confidence']
    return df_predictions


def tukey_test(dataframe: pd.DataFrame, group_column: str, value_column: str, alpha: float = 0.05) -> pd.DataFrame:
    tukey = pairwise_tukeyhsd(endog=dataframe[value_column], groups=dataframe[group_column], alpha=alpha)
    raw_results = np.array(tukey.summary().data)

    df_tukey = pd.DataFrame(raw_results[1:], columns=[str(c) for c in raw_results[0]])
    df_tukey = df_tukey[df_tukey['reject'] == 'True']
    df_tukey = df_tukey.drop(columns=['reject'])

    df_tukey['weight'] = 1 - df_tukey['p-adj'].astype(float)
    df_tukey['difference'] = df_tukey['meandiff'].astype(float)
    df_tukey['absolute_difference'] = df_tukey['difference'].abs()
    df_tukey = df_tukey.drop(columns=['p-adj', 'meandiff'])

    return df_tukey

def create_digraph(dataframe_tuckey: pd.DataFrame, dataframe_region: pd.DataFrame, nlp_error_column: str, threshold: float = 0.01) -> nx.DiGraph:
    G = nx.DiGraph()

    for _, row in dataframe_tuckey.iterrows():
        if row['absolute_difference'] < threshold: continue

        G.add_node(row['group1'], mean_error=dataframe_region[dataframe_region['user_country_region'] == row['group1']][nlp_error_column].mean())
        G.add_node(row['group2'], mean_error=dataframe_region[dataframe_region['user_country_region'] == row['group2']][nlp_error_column].mean())

        if row['difference'] < 0:
            G.add_edge(row['group2'], row['group1'], weight=row['absolute_difference'], difference=row['absolute_difference'])
        else:
            G.add_edge(row['group1'], row['group2'], weight=row['absolute_difference'], difference=row['absolute_difference'])
    
    return G

