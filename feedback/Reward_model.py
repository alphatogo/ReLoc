from transformers import AutoModelForSequenceClassification, AutoTokenizer, AutoModelForCausalLM
import torch

class Reward_model():
    def __init__(self, args):
        self.args = args
        self.rm = AutoModelForSequenceClassification.from_pretrained(
            self.args.rm,
            torch_dtype=torch.bfloat16,
            device_map=self.args.device,
            attn_implementation="flash_attention_2",
            num_labels=1)
        self.rm_tokenizer = AutoTokenizer.from_pretrained(self.args.rm, use_fast=True)

    def reward(self, question, code_list):
        question_content  = question.question_content
        score_list = []
        for code in code_list:
            messages = [{"role": "user", "content": question_content},
                        {"role": "assistant", "content": code}]
            conv_formatted = self.rm_tokenizer.apply_chat_template(messages, tokenize=False,
                                                                    add_generation_prompt=False)

            conv_tokenized = self.rm_tokenizer(
                conv_formatted,
                return_tensors="pt",
                add_special_tokens=False,
            ).to(self.args.device)
            with torch.no_grad():
                score = self.rm(input_ids=conv_tokenized.input_ids).logits[0][0].item()
            score_list.append(score)

        return score_list




