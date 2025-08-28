import os
import torch
import argparse


# codegeneration = "codegeneration"
# selfrepair = "selfrepair"
# testoutputprediction = "testoutputprediction"
# codeexecution = "codeexecution"

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--method",
        type=str,
        default="GPT4",
        help="how to solve problem",
    )

    parser.add_argument(
        "--config_path",
        type=str,
        default="ABLATION_Our",
        help="how to solve problem",
    )

    parser.add_argument(
        "--model",
        type=str,
        # default="Qwen/Qwen2.5-32B-Instruct",
        default="gpt",
        help="Name of the model to use matching `lm_styles.py`",
    )

    parser.add_argument(
        "--task",
        type=str,
        default="Code_gen",
        help="evaluation task",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="debug",
    )

    parser.add_argument(
        "--exe_feedback",
        action="store_false",
        help="debug",
    )

    parser.add_argument(
        "--neighbor_strategy",
        action="store_false",
        help="debug",
    )


    parser.add_argument(
        "--debug_seed_code_path",
        type=str,
        default="",
        help="debug_seed_code_path",
    )

    parser.add_argument(
        "--public_test_case_num",
        type=int,
        default=3,
        help="public_test_case_num",
    )


    parser.add_argument(
        "--dataset",
        type=str,
        default="LCB",
        help="Name of the dataset TACO/LCB",
    )

    parser.add_argument(
        "--Code_source",
        type=str,
        default="Qwen32B",
        help="Qwen32B",
    )

    parser.add_argument(
        "--stage",
        type=str,
        default="test",
        help="Name of the dataset TACO/LCB",
    )

    parser.add_argument(
        "--sampling_split",
        type=int,
        default=1,
        help="problem.index % 4 != sampling_split, continue",
    )

    parser.add_argument(
        "--debug_type",
        type=str,
        default="revise",
        help="the sequence of benchmark debug regular/revise ",
    )

    parser.add_argument(
        "--Model_generate",
        type=str,
        default="vllm",
        help="LLM load method vllm/transformers",
    )

    parser.add_argument(
        "--output_path",
        type=str,
        default="./output",
        help="Name of the model to use matching `lm_styles.py`",
    )

    parser.add_argument(
        "--gen_method",
        type=str,
        default="idea search",
        help="how to generate seed solutions, random sampling/idea search",
    )



    parser.add_argument(
        "--reflection_feedback",
        nargs='+',
        default=["public test case"],
        help="information to extend seed, self reflection/public test case",
    )

    parser.add_argument(
        "--choose_method",
        nargs='+',
        default=["reward model", "public test case"],
        help="how to choose next step node, reward model/public test case/self selection",
    )

    parser.add_argument(
        "--test case extend",
        action="store_true",
        help="whether extend test case by LLM",
    )

    parser.add_argument(
        "--debug_history",
        action="store_true",
        help="whether extend test case by LLM",
    )

    parser.add_argument(
        "--rm",
        type=str,
        default="",
        help="Name of the model to use matching `lm_styles.py`",
    )


    parser.add_argument(
        "--device",
        type=str,
        default="cuda:0",
        help="Name of the model to use matching `lm_styles.py`",
    )

    parser.add_argument(
        "--expand_budget", type=int, default=3, help="Number of samples to generate"
    )

    parser.add_argument(
        "--seed_num", type=int, default=3, help="Number of samples to seed solutions"
    )


    parser.add_argument(
        "--top_k",
        default=3,
        type=int,
        help="Number of local search topk to filter current code for revise",
    )


    parser.add_argument(
        "--search_budget",
        default=5,
        type=int,
        help="Number of local search topk to filter current code for revise",
    )


    parser.add_argument(
        "--trust_remote_code",
        action="store_true",
        help="trust_remote_code option used in huggingface models",
    )

    parser.add_argument(
        "--scenario",
        default="codegeneration",
        help="Type of scenario to run",
    )

    parser.add_argument(
        "--not_fast",
        action="store_true",
        help="whether to use full set of tests (slower and more memory intensive evaluation)",
    )
    parser.add_argument(
        "--release_version",
        type=str,
        default="release_v5",
        help="whether to use full set of tests (slower and more memory intensive evaluation)",
    )

    parser.add_argument(
        "--cot_code_execution",
        action="store_true",
        help="whether to use CoT in code execution scenario",
    )


    parser.add_argument(
        "--temperature", type=float, default=0.2, help="Temperature for sampling"
    )
    parser.add_argument("--top_p", type=float, default=0.95, help="Top p for sampling")
    parser.add_argument(
        "--max_tokens", type=int, default=8192, help="Max tokens for sampling"
    )



    parser.add_argument(
        "--stop",
        default="###",
        type=str,
        help="Stop token (use `,` to separate multiple tokens)",
    )

    parser.add_argument("--continue_existing", action="store_true")
    parser.add_argument("--continue_existing_with_eval", action="store_true")
    parser.add_argument(
        "--use_cache", action="store_true", help="Use cache for generation"
    )


    parser.add_argument(
        "--num_process_evaluate",
        type=int,
        default=20,
        help="Number of processes to use for evaluation",
    )
    parser.add_argument("--timeout", type=int, default=6, help="Timeout for evaluation")
    parser.add_argument(
        "--openai_timeout", type=int, default=90, help="Timeout for requests to OpenAI"
    )
    parser.add_argument(
        "--tensor_parallel_size",
        type=int,
        default=-1,
        help="Tensor parallel size for vllm",
    )
    parser.add_argument(
        "--enable_prefix_caching",
        action="store_true",
        help="Enable prefix caching for vllm",
    )

    parser.add_argument(
        "--custom_output_save_name",
        type=str,
        default=None,
        help="Folder name to save the custom output results (output file folder modified if None)",
    )
    parser.add_argument("--dtype", type=str, default="bfloat16", help="Dtype for vllm")

    args = parser.parse_args()

    args.stop = args.stop.split(",")

    if args.tensor_parallel_size == -1:
        args.tensor_parallel_size = torch.cuda.device_count()

    return args


def test():
    args = get_args()
    print(args)


if __name__ == "__main__":
    test()
