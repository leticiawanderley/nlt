import time
import torch
import pandas as pd

from constant import GOLD_LABEL, MODEL_LABEL
from rnn import RNN
from rnn_data_preprocessing import get_all_tags, read_data, sequence_to_tensor
from rnn_helper_functions import category_from_output, Data, setup_data
from utils import get_structural_errors, time_since, power_of_ten_value, \
                  setup_train_test_data
from visualization_functions import confusion_matrix, losses


def run_training(rnn, data, categories, learning_rate, output_model):
    n_iters = data.size
    print_every = power_of_ten_value(n_iters * 0.05)
    plot_every = power_of_ten_value(n_iters * 0.01)
    start = time.time()
    current_loss = 0
    all_losses = []
    for iteration in range(1, n_iters + 1):
        category, sequence, category_tensor, sequence_tensor = \
            data.random_training_datapoint()
        output, loss = rnn.train_iteration(category_tensor, sequence_tensor,
                                           learning_rate)
        current_loss += loss

        # Print iteration number, loss, name and guess
        if iteration % print_every == 0:
            guess, guess_i = category_from_output(output, categories)
            correct = '✓' if guess == category else '✗ (%s)' % category
            print('%d %d%% (%s) %.4f %s / %s %s' % (iteration,
                                                    iteration / n_iters * 100,
                                                    time_since(start), loss,
                                                    sequence, guess, correct))

        # Add current loss avg to list of losses
        if iteration % plot_every == 0:
            all_losses.append(current_loss / plot_every)
            current_loss = 0
    torch.save(rnn.state_dict(), output_model)
    return all_losses


def train_rnn_model(training_data, categories, all_tags,
                    learning_rate, output_model, output_figure):
    data = Data(training_data, all_tags)
    rnn = RNN(len(all_tags), n_hidden, len(categories))
    all_losses = run_training(rnn, data, categories, learning_rate,
                              output_model)
    losses(all_losses, output_figure)
    return rnn


def test_datapoint(rnn, datapoint, categories, all_tags):
    sequence_tensor = sequence_to_tensor(datapoint,
                                         len(all_tags), all_tags)
    output = rnn.evaluate(sequence_tensor)
    guess, guess_i = category_from_output(output, categories)
    return guess


def test_nli_rnn(test_dataset, rnn, categories, n_tags, all_tags):
    test_df = pd.read_csv(test_dataset)
    nlt = []
    results = []
    structural_errors = get_structural_errors()
    for index, row in test_df.iterrows():
        if row['error_type'] == '_' or row['error_type'] in structural_errors:
            guess = test_datapoint(rnn, row['incorrect_trigram_ud'].split(),
                                   categories, all_tags)
            is_nlt = guess == 'zhs_ud'
            is_guess_correct = is_nlt == row[GOLD_LABEL]
            nlt.append(is_nlt)
            results.append(is_guess_correct)
        else:
            nlt.append('')
            results.append('')
    test_df[MODEL_LABEL] = nlt
    test_df['result'] = results
    print(test_df.groupby(['result']).size().reset_index(name='count'))
    output_filename = 'data/results_chinese_annotated_errors_rnn.csv'
    test_df.to_csv(output_filename)
    return output_filename


def nli(vocab_datasets, training_datasets, test_dateset, categories,
        n_hidden, saved_model_path, train_new_model=True):
    all_tags = get_all_tags(vocab_datasets)
    if train_new_model:
        training_data = read_data(training_datasets, categories)
        learning_rate = 0.0001
        rnn = train_rnn_model(training_data, categories, all_tags,
                              learning_rate, saved_model_path,
                              'all_losses_zhs_en_1.png')
    else:
        rnn = RNN(len(all_tags), n_hidden, len(categories))
        rnn.load_state_dict(torch.load(saved_model_path))
        rnn.eval()
    results_file = test_nli_rnn(test_dataset, rnn,
                                categories, len(all_tags), all_tags)
    confusion_matrix(results_file, GOLD_LABEL, MODEL_LABEL,
                     'confusion_matrix_zhs_en_rnn.png')


def test_nlt_rnn(test_data, rnn, categories, n_tags, all_tags):
    nlt = []
    results = []
    for index, row in test_data.iterrows():
        guess = test_datapoint(rnn, row['type_and_trigram_ud'].split(),
                               categories, all_tags)
        nlt.append(guess)
        results.append(guess == row[GOLD_LABEL])
    test_data[MODEL_LABEL] = nlt
    test_data['result'] = results
    output_filename = 'data/results_predict_nlt_annotated_FCE.csv'
    print(test_data.groupby(['result']).size().reset_index(name='count'))
    test_data.to_csv(output_filename)
    return output_filename


def predict_nlt(n_hidden, saved_model_path, train_new_model=True):
    training_data, test_data = setup_train_test_data(
                                'data/testing data/annotated_FCE/' +
                                'chinese_annotated_errors.csv', 0.1,
                                GOLD_LABEL)
    all_tags = get_all_tags(
                    ['data/training data/type_and_trigram_ud_0_vocab.csv'])
    columns = {True: True, False: False}
    categories = list(columns.keys())
    if train_new_model:
        data_dict = setup_data(training_data, columns, 'type_and_trigram_ud',
                               GOLD_LABEL)
        learning_rate = 0.25
        rnn = train_rnn_model(data_dict, categories, all_tags, learning_rate,
                              saved_model_path, 'all_losses_predict_nlt.png')
    else:
        rnn = RNN(len(all_tags), n_hidden, len(categories))
        rnn.load_state_dict(torch.load(saved_model_path))
        rnn.eval()
    results_file = test_nlt_rnn(test_data, rnn, categories,
                                len(all_tags), all_tags)
    confusion_matrix(results_file, GOLD_LABEL, MODEL_LABEL,
                     'confusion_matrix_predict_nlt.png')


if __name__ == "__main__":
    train_nli = False
    if train_nli:
        vocab_datasets = [
            'data/training data/globalvoices_vocabs/zhs_ud_0_vocab.csv',
            'data/training data/globalvoices_vocabs/en_ud_0_vocab.csv']
        training_datasets = [
            'data/training data/tagged_globalvoices_sentences.csv']
        test_dataset = 'data/testing data/annotated_FCE/' + \
                       'chinese_annotated_errors.csv'
        categories = ['en_ud', 'zhs_ud']
        n_hidden = 256
        saved_model_path = './saved_model_zhs_en_1.pth'
        nli(vocab_datasets, training_datasets, test_dataset,
            categories, n_hidden, saved_model_path, False)
    else:
        n_hidden = 128
        saved_model_path = 'saved_prediction_model.pth'
        predict_nlt(n_hidden, saved_model_path)
