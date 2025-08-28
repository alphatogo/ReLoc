from tqdm import tqdm
from parser import *
import numpy as np
from data.load_datas import *
from runner import Runner
import yaml
from datetime import datetime
from LLM_runner.tools import *
import traceback
from feedback.execution import execution
args = get_args()
for arg, value in vars(args).items():
    print(f"{arg}: {value}")


class CustomJSONizer(json.JSONEncoder):
    def default(self, obj):
        return super().encode(bool(obj)) \
            if isinstance(obj, np.bool_) \
            else super().default(obj)


def main():

    benchmark = load_data(args)

    config_path = os.path.join("./config", args.config_path+".yaml")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)


    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(args.output_path, args.task, args.dataset, args.Code_source, args.method, f"exp_{timestamp}_{args.config_path}")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    args_dict = vars(args)
    with open(os.path.join(output_dir, 'args.json'), 'w') as f:
        json.dump(args_dict, f, indent=2, cls=CustomJSONizer)


    with open(os.path.join(output_dir, 'config.yaml'), 'w') as f:
        yaml.dump(config, f)

    output_path = os.path.join(output_dir, "sampling_per_problem")
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    runner = Runner(args, config)
    for problem in tqdm(benchmark):
        try:
            filename = f"{problem.question_title}.json"
            question_title = problem.question_title
            output_path_per_problem = os.path.join(output_path, filename)
            if os.path.exists(output_path_per_problem):
                print(f"{question_title}.json exists")
                continue
            runner.selection_method.selection_method_reset()
            runner.model.reset_model()

            final_commit_node = runner.search(problem)
            save_nodes_to_json(final_commit_node, runner.selection_method, output_path_per_problem, runner.model.token_length)
            print(f"\n\n\nSaved {question_title} to JSON file\n\n\n")

        except Exception as e:
            print(f"\n\n=== Error occurred while processing {question_title} ===")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            if str(e)=="CUDA error: device-side assert triggered" or str(e) in "CUDA error: device-side assert triggered" or "CUDA error: device-side assert triggered" in str(e):
                runner.model.reset_model()
            print("\nFull traceback:")
            traceback.print_exc()
            print(f"=== End of error report for {question_title} ===\n\n")
            continue







def save_nodes_to_json(final_commit_node, selection_method, output_path, token_length):

    nodes_data = {}

    nodes_data["token_length"] =  token_length
    nodes_data["node_num"] = len(selection_method.all_node)


    nodes_data["commit_node"] = []
    for node in final_commit_node:
        node_data = {
            'code_content': node.code_content,
            'reward': node.reward,
            'metadata': node.metadata,
            'self reward': node.self_score,
            'execution_results_public': getattr(node, 'execution_results_public', None),
            'execution_results_private': getattr(node, 'execution_results_private', None)
        }
        nodes_data["commit_node"].append(node_data)

    nodes_data["all_node"] = []
    for node in selection_method.all_node:
        node_data = {
            'code_content': node.code_content,
            'reward': node.reward,
            'metadata': node.metadata,
            'self reward': node.self_score,
            'execution_results_public': getattr(node, 'execution_results_public', None),
            'execution_results_private': getattr(node, 'execution_results_private', None)
        }
        nodes_data["all_node"].append(node_data)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(nodes_data, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    main()
