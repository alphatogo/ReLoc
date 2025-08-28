import json
def get_public_sample(problem):
    return {
        "input_output": json.dumps(
            {
                "inputs": [
                    t.input
                    for t in problem.public_test_cases
                ],
                "outputs": [
                    t.output
                    for t in problem.public_test_cases
                ],
                "fn_name": problem.metadata.get("func_name", None),
            }
        ),
    }

def get_private_sample(problem):
    return {
        "input_output": json.dumps(
            {
                "inputs": [
                    t.input
                    for t in problem.private_test_cases
                ],
                "outputs": [
                    t.output
                    for t in problem.private_test_cases
                ],
                "fn_name": problem.metadata.get("func_name", None),
            }
        ),
    }