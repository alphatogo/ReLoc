from .Code_gen.LCB.lcb_code_generation import *
import os

from .benchmarks.get_execution_test_case import get_public_sample, get_private_sample

class TACO_Problem:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.question_content = self.question


def load_data(args):
    if args.dataset == "LCB":
        benchmark_v5 = load_dataset("livecodebench/code_generation_lite", split="test", version_tag="release_v5",trust_remote_code=True)
        data_v5 = [CodeGenerationProblem(**p) for p in benchmark_v5]

        benchmark_v2 = load_dataset("livecodebench/code_generation_lite", split="test",version_tag="release_v3", trust_remote_code=True)
        data_v2 = [CodeGenerationProblem(**p) for p in benchmark_v2]

        data = []
        for problem in data_v5:
            if problem not in data_v2:

                problem.public_test_case = get_public_sample(problem)
                problem.public_test_case["number"] = len(json.loads(problem.public_test_case['input_output'])['inputs'])
                problem.private_test_case = get_private_sample(problem)
                problem.private_test_case["number"] = len(json.loads(problem.private_test_case['input_output'])['inputs'])

                if args.task == 'Code_debug':

                    debug_data_path = os.path.join(args.debug_seed_code_path, args.dataset, f"{problem.question_title}.json")
                    if not os.path.exists(debug_data_path):
                        continue
                    with open(debug_data_path, "r") as f:
                        debug_data = json.load(f)

                    setattr(problem, 'debug_seed_code', [debug_data])
                    data.append(problem)

                else:
                    data.append(problem)


    elif args.dataset == "TACO":
        benchmark = load_dataset('BAAI/TACO')['test']
        data = []

        for problem in benchmark:
            problem = TACO_Problem(**problem)

            in_outs = json.loads(problem.input_output)

            public_test_case = {'input_output': json.dumps(
                {"inputs": in_outs["inputs"][:args.public_test_case_num], "outputs": in_outs["outputs"][:args.public_test_case_num],
                 "fn_name": in_outs["fn_name"] if "fn_name" in in_outs else None}), "number":args.public_test_case_num}

            private_test_case = {'input_output': json.dumps(
                {"inputs": in_outs["inputs"][args.public_test_case_num:],
                 "outputs": in_outs["outputs"][args.public_test_case_num:],
                 "fn_name": in_outs["fn_name"] if "fn_name" in in_outs else None}), "number":len(in_outs["outputs"][args.public_test_case_num:])}

            setattr(problem, 'public_test_case', public_test_case)
            setattr(problem, 'private_test_case', private_test_case)


            if args.task == 'Code_debug':
                debug_data_path = os.path.join(args.debug_seed_code_path, args.dataset, f"{problem.question_title}.json")
                if not os.path.exists(debug_data_path):
                    continue
                with open(debug_data_path, "r") as f:
                    debug_data = json.load(f)

                setattr(problem, 'debug_seed_code', [debug_data])
                data.append(problem)

            else:
                data.append(problem)


    return data




