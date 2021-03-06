import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

import numpy as np

from model import NERModel
from train import train
import utils.evaluate as evaluate
import utils.prepare_data as prepare_data
from utils import radam
from config.params import *


if __name__ == '__main__':
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    torch.manual_seed(0)

    print(device)

    corpus_path = 'data/corpus.txt'
    # whole_data_path = 'data/digitoday/digitoday.2014.txt'
    train_data_path = 'data/digitoday/digitoday.2014.train.txt'
    dev_data_path = 'data/digitoday/digitoday.2014.dev.txt'
    test_data_path = 'data/digitoday/digitoday.2015.test.txt'
    wiki_data_path = 'data/digitoday/wikipedia.test.txt'

    whole_data_morph_path = 'utils/subword_segmentation/output/segmented/whole_vocab_segmented.txt'

    # whole_data = prepare_data.load_data(whole_data_path)
    train_data = prepare_data.load_data(train_data_path)
    dev_data = prepare_data.load_data(dev_data_path)
    test_data = prepare_data.load_data(test_data_path)
    wiki_data = prepare_data.load_data(wiki_data_path)


    whole_data_morphs = prepare_data.load_data_morphs(whole_data_morph_path)
    

    # add <start> and <end> token to each sentence
    train_data = prepare_data.add_start_end_sentence_tokens(train_data)
    dev_data = prepare_data.add_start_end_sentence_tokens(dev_data)
    test_data = prepare_data.add_start_end_sentence_tokens(test_data)
    wiki_data = prepare_data.add_start_end_sentence_tokens(wiki_data)


    weights_matrix = np.load('weights/embedding_weights_matrix_ft.npy')
    

    # CREATE INDICES
    # word2idx, idx2word, tag2idx, idx2tag, char2idx, idx2char = prepare_data.encode_data(corpus_path)
    # morph2idx, idx2morph = prepare_data.encode_data_morphs(whole_data_morphs)
    # word2morph = prepare_data.word_to_morph(whole_data_morphs)


    # # SAVE INDICES
    # prepare_data.save_obj(word2idx, 'weights/indices/word2idx')
    # prepare_data.save_obj(idx2word, 'weights/indices/idx2word')
    # prepare_data.save_obj(tag2idx, 'weights/indices/tag2idx')
    # prepare_data.save_obj(idx2tag, 'weights/indices/idx2tag')
    # prepare_data.save_obj(char2idx, 'weights/indices/char2idx')
    # prepare_data.save_obj(morph2idx, 'weights/indices/morph2idx')
    # prepare_data.save_obj(idx2morph, 'weights/indices/idx2morph')
    # prepare_data.save_obj(word2morph, 'weights/indices/word2morph')

    # LOAD INDICES
    word2idx = prepare_data.load_obj('weights/indices/word2idx')
    idx2word = prepare_data.load_obj('weights/indices/idx2word')
    tag2idx = prepare_data.load_obj('weights/indices/tag2idx')
    idx2tag = prepare_data.load_obj('weights/indices/idx2tag')
    char2idx = prepare_data.load_obj('weights/indices/char2idx')
    morph2idx = prepare_data.load_obj('weights/indices/morph2idx')
    idx2morph = prepare_data.load_obj('weights/indices/idx2morph')
    word2morph = prepare_data.load_obj('weights/indices/word2morph')


    indexed_data_train = prepare_data.data_to_idx(train_data, word2idx)
    indexed_tag_train = prepare_data.tag_to_idx(train_data, tag2idx)
    indexed_char_train = prepare_data.char_to_idx(train_data, char2idx)
    indexed_morph_train = prepare_data.morph_to_idx(train_data, morph2idx, word2morph)
    data_train = prepare_data.combine_data(indexed_data_train, indexed_tag_train, indexed_char_train, indexed_morph_train, MAX_SEQ_LENGTH)


    indexed_data_dev = prepare_data.data_to_idx(dev_data, word2idx)
    indexed_tag_dev = prepare_data.tag_to_idx(dev_data, tag2idx)
    indexed_char_dev = prepare_data.char_to_idx(dev_data, char2idx)
    indexed_morph_dev = prepare_data.morph_to_idx(dev_data, morph2idx, word2morph)
    data_dev = prepare_data.combine_data(indexed_data_dev, indexed_tag_dev, indexed_char_dev, indexed_morph_dev, MAX_SEQ_LENGTH)


    indexed_data_test = prepare_data.data_to_idx(test_data, word2idx)
    indexed_tag_test = prepare_data.tag_to_idx(test_data, tag2idx)
    indexed_char_test = prepare_data.char_to_idx(test_data, char2idx)
    indexed_morph_test = prepare_data.morph_to_idx(test_data, morph2idx, word2morph)
    data_test = prepare_data.combine_data(indexed_data_test, indexed_tag_test, indexed_char_test, indexed_morph_test, MAX_SEQ_LENGTH)


    indexed_data_wiki = prepare_data.data_to_idx(wiki_data, word2idx)
    indexed_tag_wiki = prepare_data.tag_to_idx(wiki_data, tag2idx)
    indexed_char_wiki = prepare_data.char_to_idx(wiki_data, char2idx)
    indexed_morph_wiki = prepare_data.morph_to_idx(wiki_data, morph2idx, word2morph)
    data_wiki = prepare_data.combine_data(indexed_data_wiki, indexed_tag_wiki, indexed_char_wiki, indexed_morph_wiki, MAX_SEQ_LENGTH)

    
    data_train = prepare_data.remove_extra(data_train, batch_size)
    data_dev = prepare_data.remove_extra(data_dev, batch_size)


    pairs_batch_train = DataLoader(dataset=data_train,
                    batch_size=batch_size,
                    shuffle=True,
                    collate_fn=prepare_data.collate,
                    pin_memory=True)

    pairs_batch_dev = DataLoader(dataset=data_dev,
                    batch_size=batch_size,
                    shuffle=True,
                    collate_fn=prepare_data.collate,
                    pin_memory=True)


    # initialize the model
    model = NERModel(word_embedding_dim, char_embedding_dim, morph_embedding_dim, word_hidden_size, char_hidden_size, morph_hidden_size, len(word2idx), 
                len(char2idx), len(morph2idx), len(tag2idx)+1, word_num_layers, char_num_layers, morph_num_layers, weights_matrix, dropout_prob).to(device)
    model.train()

    optimizer = radam.RAdam(model.parameters(), lr=learning_rate) 
    # optimizer = optim.Adam(model.parameters(), lr=learning_rate, amsgrad=True)
    print(model)
    
    total_trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print('The number of trainable parameters is: %d' % (total_trainable_params))



    # train the model
    if skip_training == False:
        train(model, word_num_layers, char_num_layers, morph_num_layers, num_epochs, pairs_batch_train, pairs_batch_dev, word_hidden_size, 
            char_hidden_size, morph_hidden_size, batch_size, optimizer, patience, device)
        model.load_state_dict(torch.load('weights/model.pt'))
    else:
        model.load_state_dict(torch.load('weights/model.pt'))

    model.eval()

    batch_size = 1
    

    print('\nVALIDATION DATA \n')
    all_predicted, all_true = evaluate.get_predictions(data_dev, model, word_num_layers, char_num_layers, morph_num_layers, word_hidden_size, 
                                                        char_hidden_size, morph_hidden_size, batch_size, device)
    evaluate.print_scores(all_predicted, all_true, tag2idx)
    # evaluate.evaluate_sentence(2, word_num_layers, char_num_layers, morph_num_layers, word_hidden_size, char_hidden_size, morph_hidden_size, batch_size, data_dev, model, idx2word, idx2tag, device)


    print('\nTEST DATA \n')
    all_predicted, all_true = evaluate.get_predictions(data_test, model, word_num_layers, char_num_layers, morph_num_layers, word_hidden_size, 
                                                        char_hidden_size, morph_hidden_size, batch_size, device)
    evaluate.print_scores(all_predicted, all_true, tag2idx)
    # evaluate.evaluate_sentence(1, word_num_layers, char_num_layers, morph_num_layers, word_hidden_size, char_hidden_size, morph_hidden_size, batch_size, data_test, model, idx2word, idx2tag, device)


    print('\nWIKI DATA \n')
    all_predicted, all_true = evaluate.get_predictions(data_wiki, model, word_num_layers, char_num_layers, morph_num_layers, word_hidden_size, 
                                                        char_hidden_size, morph_hidden_size, batch_size, device)
    evaluate.print_scores(all_predicted, all_true, tag2idx)