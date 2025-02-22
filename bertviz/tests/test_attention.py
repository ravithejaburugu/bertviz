from bertviz.attention import get_attention_bert, get_attention
from bertviz.pytorch_transformers_attn import BertTokenizer, BertModel, BertConfig, GPT2Model, GPT2Tokenizer,\
    XLNetModel, XLNetTokenizer

import unittest
import torch

class TestAttention(unittest.TestCase):

    def test_bert_attn(self):
        self.config = BertConfig.from_json_file('fixtures/config.json')
        self.model = BertModel(self.config)
        self.tokenizer = BertTokenizer('fixtures/vocab.txt')
        sentence1 = 'The quickest brown fox jumped over the lazy dog'
        sentence2 = "the quick brown fox jumped over the laziest elmo"
        attn_data = get_attention_bert(self.model, self.tokenizer, sentence1, sentence2, include_queries_and_keys=False)
        tokens_1 = ['[CLS]', 'the', 'quick', '##est', 'brown', 'fox', 'jumped', 'over', 'the', 'lazy', 'dog', '[SEP]']
        tokens_2 = ['the', 'quick', 'brown', 'fox', 'jumped', 'over', 'the', 'la', '##zie', '##st', '[UNK]', '[SEP]']
        self.assertEqual(attn_data['all']['left_text'], tokens_1 + tokens_2)
        self.assertEqual(attn_data['all']['right_text'], tokens_1 + tokens_2)
        self.assertEqual(attn_data['aa']['left_text'], tokens_1)
        self.assertEqual(attn_data['aa']['right_text'], tokens_1)
        self.assertEqual(attn_data['ab']['left_text'], tokens_1)
        self.assertEqual(attn_data['ab']['right_text'], tokens_2)
        self.assertEqual(attn_data['ba']['left_text'], tokens_2)
        self.assertEqual(attn_data['ba']['right_text'], tokens_1)
        self.assertEqual(attn_data['bb']['left_text'], tokens_2)
        self.assertEqual(attn_data['bb']['right_text'], tokens_2)

        attn_all = attn_data['all']['attn']
        attn_aa = attn_data['aa']['attn']
        attn_ab = attn_data['ab']['attn']
        attn_ba = attn_data['ba']['attn']
        attn_bb = attn_data['bb']['attn']
        num_layers = len(attn_all)
        for layer in range(num_layers):
            attn_all_layer = torch.tensor(attn_all[layer])
            num_heads, seq_len, _ = attn_all_layer.size()
            # Check that probabilities sum to one
            sum_probs = attn_all_layer.sum(dim=-1)
            expected = torch.ones(num_heads, seq_len, dtype=torch.float32)
            self.assertTrue(torch.allclose(sum_probs, expected))
            # Reassemble attention from components and verify is correct
            attn_aa_layer = torch.tensor(attn_aa[layer])
            attn_ab_layer = torch.tensor(attn_ab[layer])
            attn_ba_layer = torch.tensor(attn_ba[layer])
            attn_bb_layer = torch.tensor(attn_bb[layer])
            top_half = torch.cat((attn_aa_layer, attn_ab_layer), dim=-1)
            bottom_half = torch.cat((attn_ba_layer, attn_bb_layer), dim=-1)
            whole = torch.cat((top_half, bottom_half), dim=-2)
            # assert self.assertAlmostEqual(torch.sum(torch.abs(whole - attn_all[layer])), 0)
            self.assertTrue(torch.allclose(whole, attn_all_layer))

    def test_gpt2_attn(self):
        model = GPT2Model.from_pretrained('gpt2')
        tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
        text = 'Bert is a yellow muppet character'
        attn_data = get_attention(model, tokenizer, text, include_queries_and_keys=False)['all']
        tokens = ['B', 'ert', 'is', 'a', 'yellow', 'm', 'uppet', 'character']
        self.assertEqual(attn_data['left_text'], tokens)
        self.assertEqual(attn_data['right_text'], tokens)
        seq_len = len(tokens)
        layer = 0
        head = 0
        att_matrix = attn_data['attn'][layer][head]
        for i in range(seq_len):
            for j in range(seq_len):
                if i >= j:
                    self.assertNotEqual(att_matrix[i][j], 0)
                else:
                    self.assertEqual(att_matrix[i][j], 0)
            sum_probs = sum(att_matrix[i])
            self.assertAlmostEqual(sum_probs, 1, 4)

    def test_xlnet_attn(self):
        tokenizer = XLNetTokenizer.from_pretrained('xlnet-large-cased')
        model = XLNetModel.from_pretrained('xlnet-large-cased')
        text = 'Bert is a yellow muppet character'
        attn_data = get_attention(model, tokenizer, text, include_queries_and_keys=False)['all']
        tokens =['Bert', 'is', 'a', 'yellow', '', 'm', 'up', 'pet', 'character']
        self.assertEqual(attn_data['left_text'], tokens)
        self.assertEqual(attn_data['right_text'], tokens)
        seq_len = len(tokens)
        layer = 0
        head = 0
        att_matrix = attn_data['attn'][layer][head]
        for i in range(seq_len):
            sum_probs = sum(att_matrix[i])
            self.assertAlmostEqual(sum_probs, 1, 4)


if __name__ == "__main__":
    unittest.main()

