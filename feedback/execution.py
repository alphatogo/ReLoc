
from .Compiler.compute_code_generation_metrics import *

def evaluation_per_problem(args, compiler_input, compiler_test_case):

    metrics_results_final_metadata, final_correct = codegen_metrics(
        compiler_test_case,
        compiler_input,
        num_process_evaluate=args.num_process_evaluate,
        timeout=args.timeout,
        debug=args.debug
    )
    metrics, results, final_metadata = metrics_results_final_metadata
    return metrics, results, final_metadata, final_correct

def execution(args, code, test_case):
    metrics, results, final_metadata, final_correct = evaluation_per_problem(args, [code], [test_case])
    return [[x, y] for x, y in zip(results[0], final_metadata[0])]