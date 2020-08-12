import numpy as np
import pandas as pd

from constant import ANNOTATED_FCE_FIELDS, CHINESE, ENGLISH, \
                     GOLD_LABEL, MODEL_LABEL, CONFUSION_MATRIX_AXES
from visualization_functions import confusion_matrix


def evaluate_models(filename, fields, l1, l2):
    df = pd.read_csv(filename)
    # If the probability in the L1 is greater than the probability in the L2
    # the sequence is tagged as negative language transfer
    df[MODEL_LABEL] = np.where(df[l1] > df[l2], True, False)
    results = []
    for index, row in df.iterrows():
        is_guess_correct = row[MODEL_LABEL] == row[GOLD_LABEL]
        results.append(is_guess_correct)
    df['result'] = results
    df = df[fields + [l1, l2, MODEL_LABEL, 'result']]
    df.to_csv(filename)
    print(filename)
    print(df.groupby(['result']).size().reset_index(name='count'))


evaluate_models(
    'data/results_chinese_fce_incorrect_trigram_ud_unsmoothed.csv',
    ANNOTATED_FCE_FIELDS, CHINESE, ENGLISH)

evaluate_models(
    'data/results_chinese_fce_incorrect_trigram_ud_laplace.csv',
    ANNOTATED_FCE_FIELDS, CHINESE, ENGLISH)

evaluate_models(
    'data/results_chinese_fce_incorrect_trigram_ud_interpolation.csv',
    ANNOTATED_FCE_FIELDS, CHINESE, ENGLISH)


confusion_matrix(
    'data/results_chinese_fce_incorrect_trigram_ud_unsmoothed.csv',
    GOLD_LABEL, MODEL_LABEL,
    'figures/confusion_matrix_zhs_en_unsmoothed.png')

confusion_matrix(
    'data/results_chinese_fce_incorrect_trigram_ud_laplace.csv',
    GOLD_LABEL, MODEL_LABEL,
    'figures/confusion_matrix_zhs_en_laplace.png')

confusion_matrix(
    'data/results_chinese_fce_incorrect_trigram_ud_interpolation.csv',
    GOLD_LABEL, MODEL_LABEL,
    'figures/confusion_matrix_zhs_en_interpolation.png')
