from vllm import LLM, SamplingParams
from openai import OpenAI
import os
from prompts.prompt_gen_bon import *
from prompts.prompt_gen_idea_search import *
from prompts.prompt_self_reflection import *
from prompts.prompt_self_reflection import *
from prompts.prompt_self_score import *
from prompts.prompt_self_debug import *
from prompts.prompt_gen_test_case import *

from prompts.prompt_self_debug_GEN import *
from LLM_runner.Qwen_runner import Qwen_runner_vllm, Qwen_runner_tf
import itertools
from LLM_runner.tools import *
import random
from transformers import AutoModelForCausalLM, AutoTokenizer
from LLM_runner.oai_runner import Openai_runner

from feedback.execution import *

class model():
    def __init__(self, args):
        self.args = args
        opensource_model = ["Qwen"]
        
        self.LLMSTYLE = args.model
       
        openai = "gpt"
        self.token_length = 0
        if any(model_name in self.LLMSTYLE for model_name in opensource_model):
            if args.Model_generate == "vllm":
                if "Qwen3-" in args.model:
                    self.llm = LLM(
                    model=self.LLMSTYLE,
                    gpu_memory_utilization=0.75,
                )
                else:
                    self.llm = LLM(
                        model=self.LLMSTYLE,
                        tensor_parallel_size=args.tensor_parallel_size,
                        max_model_len=args.max_tokens,
                        gpu_memory_utilization=0.75,
                    )
                self.lm_tokenizer = AutoTokenizer.from_pretrained(self.LLMSTYLE)
 
            elif args.Model_generate == "transformers":
                self.llm = AutoModelForCausalLM.from_pretrained(
                    self.LLMSTYLE,
                    torch_dtype="auto",
                    device_map="auto"
                )
                self.lm_tokenizer = AutoTokenizer.from_pretrained(self.LLMSTYLE)
        elif openai in args.model:
            self.llm = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"), base_url=os.environ.get("OPENAI_BASE_URL"))

    def runner(self, message, generate_num=1, args=None, problem=None):
        answer = None
        if any(model_name in self.LLMSTYLE for model_name in ["Qwen"]):
            if self.args.Model_generate == "vllm":
                sampling_params_gen_op = SamplingParams(
                    n=generate_num,
                    max_tokens=self.args.max_tokens,
                    temperature=self.args.temperature,
                    top_p=self.args.top_p
                )
                if "Qwen3-" in self.args.model:
                    sampling_params_gen_op = SamplingParams(
                        n=generate_num,
                        max_tokens=32768,
                        temperature=0.6,
                        top_p=0.95,
                        top_k=20,
                        min_p=0
                    )
                answer, token_consume = Qwen_runner_vllm(self.llm, self.lm_tokenizer, sampling_params_gen_op, message, self.args, problem)

                self.token_length += token_consume
            elif self.args.Model_generate == "transformers":
                sampling_params_gen_op = {
                    "max_length":self.args.max_tokens,
                    "do_sample":True,
                    "temperature":self.args.temperature,
                    "top_p":self.args.top_p,
                    "early_stopping":False
                }
                answer = Qwen_runner_tf(self.llm, self.lm_tokenizer, sampling_params_gen_op, message, generate_num)

        elif "gpt" in self.LLMSTYLE:
            client_kwargs = {
                "model": self.LLMSTYLE,
                "temperature": self.args.temperature,
                "max_tokens": self.args.max_tokens,
                "top_p": self.args.top_p,
                "n": 1,
                "timeout": self.args.openai_timeout,
            }
            answers = []
            for _ in range(generate_num):
                answer, token_consume = Openai_runner(self.llm, client_kwargs, message)
                self.token_length += token_consume
                answers += answer

            answer = answers

        return answer

    def reset_model(self):
        self.token_length = 0

    def seed_generate(self, problem, args=None):
        if self.args.gen_method == "random sampling":
            message = gen_bon_generate(problem, self.args.model)
            answer = []

            answer = self.runner(message, self.args.seed_num, args, problem)

            seed_code = code_extraction(answer)
            seed_code = list(set(seed_code))
            return seed_code


        elif self.args.gen_method == "idea search":
            seed_code = []
            Observations_prompts = gen_idea_search_generate(problem, self.args.model, gen_type="Observation")
            Observations = self.runner(Observations_prompts, 1)
            Observations = observations_extraction(Observations)

            Observations_subsets = list(itertools.combinations(range(len(Observations)), 2))

            Observations_subsets = random.sample(Observations_subsets, min(len(Observations_subsets), self.args.seed_num))
            for Observations_index in Observations_subsets:

                Backtranslation_prompts = gen_idea_search_generate(problem, self.args.model, gen_type="Backtranslation", Observations=[Observations[Observations_index[0]], Observations[Observations_index[1]]])


                answer = self.runner(Backtranslation_prompts,1)

                seed_code += code_extraction(answer)

            seed_code = list(set(seed_code))
            return seed_code

   


    def BON_debug_generate(self ,problem, args=None):
        if self.args.task == 'Code_debug':

            message = gen_bon_generate(problem, self.args.model)
            answer = []

            answer = self.runner(message, self.args.seed_num, args, problem)

            seed_code = code_extraction(answer)
            seed_code = list(set(seed_code))
            return seed_code


    def self_reflection(self, problem, selected_node):

        message = gen_reflection(problem, selected_node, self.args.model, self.args.debug_history, self.args.exe_feedback)
        if message:
            answer = self.runner(message, 1)[0]
            explanation, direction = relfection_extraction([answer])

            if self.args.task == 'Code_debug' and not self.args.config_path == "GEN":
                if direction[0] != None and len(direction[0]) > 1:
                    Observations_subsets = list(itertools.combinations(range(len(direction[0])), 2))
                    concatenated = [direction[0][subset[0]] + "\n" + direction[0][subset[1]] for subset in Observations_subsets]
                    direction[0] = concatenated

            if self.args.task == 'Code_debug' and self.args.config_path == "GEN":
                concatenated = []
                if direction[0] != None and len(direction[0]) > 1:
                    Observations_subsets = list(itertools.combinations(range(len(direction[0])), 2))
                    concatenated = [direction[0][subset[0]] + "\n" + direction[0][subset[1]] for subset in Observations_subsets]


                if direction[0] != None and len(direction[0]) > 2: 
                    Observations_subsets = list(itertools.combinations(range(len(direction[0])), 3))
                    concatenated += [
                        direction[0][subset[0]] + "\n" + direction[0][subset[1]] + "\n" + direction[0][subset[2]]
                        for subset in Observations_subsets]

                direction[0] += concatenated

            selected_node.modify_node(explanation[0], direction[0])


    def self_score(self, problem, code_content):
        message = gen_score(problem, code_content, self.args.model)
        answer = self.runner(message)[0]
        reward  = self_score_extraction(answer)
        return reward


    def self_debug(self, problem, selected_node, GEN=False):
        if GEN:
            message = gen_debug_GEN(problem, selected_node, self.args.model, debug_history=self.args.debug_history)
            answer_strategy_description = "GEN"
            for node in selected_node:
                node.used_direction.append(answer_strategy_description)
        else:
            message, answer_strategy_description = gen_debug(problem, selected_node, self.args.model, self.args.debug_history, self.args.neighbor_strategy)

        answer = self.runner(message, 1)
        answer = code_extraction(answer)

        return answer[0], answer_strategy_description

    def self_debug_debug(self, problem, node_list):

        refined_code_list = {}
        message_list = []
        output_index = {}
        count_message = 0
        for node in node_list:
            output_index[node] = [count_message]
            while node.expand_direction != []:
                count_message += 1
                message = gen_debug(problem, node, self.args.model)
                message_list.append(message)
            output_index[node].append(count_message)
        answer = self.runner(message_list, 1)
        answer = code_extraction_debug(answer)

        return answer, output_index

    def self_gen_test_case(self, problem, public=True):
        message = gen_test_case(problem, self.args.model)
        answer = self.runner(message, 5)
        answer = test_case_extraction_debug(answer)


        public_test_case = problem.public_test_case
        test_cases = json.loads(public_test_case["input_output"])
        if not public:
            test_cases["inputs"] = []
            test_cases["outputs"] = []

        for test_case in answer:
            test_case = json.loads(test_case)
            for index in range(len(test_case["inputs"])):
                if test_case["inputs"][index] not in test_cases["inputs"]:
                    test_cases["inputs"].append(test_case["inputs"][index])
                    test_cases["outputs"].append(test_case["outputs"][index])
                    public_test_case["number"] += 1



        public_test_case = {'input_output': json.dumps(
            test_cases), "number": public_test_case["number"]}

        return public_test_case
