import json
class PromptConstants:
    SYSTEM_MESSAGE_WITH_HISTORY = '''You are a helpful programming assistant and an expert in Python. The user has written code that contains errors. You will be provided with a Python programming problem, the user's code, revision history, an explanation, and directions for refinement. Your task is to debug and revise the code to correctly solve the problem.  
Generate a corrected version of the complete program, incorporating the explanation, refinement directions, and revision history.  
**Output only one corrected program enclosed within a single pair of code delimiters. Do not include any additional commentary or text.**
    '''

    SYSTEM_MESSAGE_WITH_HISTORY_WITHOUT_STRATEGY = '''You are a helpful programming assistant and an expert in Python. The user has written code that contains errors. You will be provided with a Python programming problem, the user's code and revision history. Your task is to debug and revise the code to correctly solve the problem. Generate a corrected version of the complete program.  
**Output only one corrected program enclosed within a single pair of code delimiters. Do not include any additional commentary or text.**
    '''


    SYSTEM_MESSAGE_WITHOUT_HISTORY_WITHOUT_STRATEGY = '''You are a helpful programming assistant and an expert in Python. The user has written code that contains errors. You will be provided with a Python programming problem, the user's code. Your task is to debug and revise the code to correctly solve the problem. Generate a corrected version of the complete program.  
**Output only one corrected program enclosed within a single pair of code delimiters. Do not include any additional commentary or text.**
        '''

    SYSTEM_MESSAGE_WITHOUT_HISTORY = '''You are a helpful programming assistant and an expert in Python. The user has written code that contains errors. You will be provided with a Python programming problem, the user's code, an explanation, and directions for refinement. Your task is to debug and revise the code to correctly solve the problem.  
Generate a corrected version of the complete program, incorporating the explanation and refinement directions.  
**Output only one corrected program enclosed within a single pair of code delimiters. Do not include any additional commentary or text.**
    '''

    DEBUG_SYSTEM_MESSAGE_WITH_HISTORY = '''You are an expert Python programmer. You will be given a question (problem specification) and intelligent directions that describes how to solve the problem. You will generate a correct Python program that matches said specification and tutorial and passes all tests. You will NOT return anything except for the program.\n\n
    '''

def get_check_prompt(metadata):

    metadata = json.loads(metadata)
    message = "Execution Results:\n"
    if "error_code" not in metadata:
        return ""
    if metadata["error_code"] == -1:
        # time limit exceeded
        message += f"The above code is incorrect and got the following compilation error.\n{metadata['error']}\n"
    elif metadata["error_code"] == -2:
        # wrong answer
        message += f"The above code is incorrect and got a wrong answer.\nInput: {metadata['inputs']}\nGenerated Output: {metadata['output']}\nExpected: {metadata['expected']}\n"
    elif metadata["error_code"] == -3:
        # time limit exceeded
        message += f"The above code is incorrect and got time limit exceeded.\n{metadata['error']}\nInput: {metadata['inputs']}\nExpected: {metadata['expected']}\n"
        pass
    elif metadata["error_code"] == -4:
        # runtime error
        message += f"The above code is incorrect and got a runtime error.\nInput: {metadata['inputs']}\nExpected: {metadata['expected']}\n{metadata['error']}\n"
    else:
        message += f"The above code is incorrect\n"
    return message


def get_Qwen_reflection_generate(question, node, expand_direction, debug_history, neighbor_strategy=True, exe_feedback=True):

    if neighbor_strategy and debug_history:
        prompt = PromptConstants.DEBUG_SYSTEM_MESSAGE_WITH_HISTORY
    elif neighbor_strategy and not debug_history:
        prompt = PromptConstants.SYSTEM_MESSAGE_WITHOUT_HISTORY

    elif not neighbor_strategy and debug_history:
        prompt = PromptConstants.SYSTEM_MESSAGE_WITH_HISTORY_WITHOUT_STRATEGY

    elif not neighbor_strategy and debug_history:
        prompt = PromptConstants.SYSTEM_MESSAGE_WITHOUT_HISTORY_WITHOUT_STRATEGY

    prompt += f"\nQuestion:\n{question.question_content}\n\n"
    prompt += f"user's code:\n```python\n{node.code_content}\n``` \n\n"

    if exe_feedback:
        prompt += get_check_prompt(node.metadata)

    if not debug_history:
        prompt += f"\nExplanation:\n{node.explanation}\n"



    prompt += f"Refinement direction:\n{expand_direction}\n"

    if debug_history and node.parent:
        prompt += "\nHere is revision history for reference: \n"
        current = node.parent

        for _ in range(3):
            if not current:
                break
            for parent in current:
                if parent != node:
                    prompt += f"\n{parent.code_content}\n"
                    if not parent.execution_results_public:
                        if exe_feedback:
                            prompt += get_check_prompt(node.metadata)
                    current = parent.parent
                    break

    prompt += "```python\n# YOUR CODE HERE\n```\n\n"


    messages = [
        {"role": "system", "content": "You are a helpful programming assistant and an expert in Python."},
        {"role": "user", "content": prompt},
    ]
    return messages


def get_deepseek_v3_openai_reflection_generate(question, node, expand_direction, debug_history):
    messages = None

    prompt = ""
    prompt += f"Question:\n{question.question_content}\n\n"
    prompt += f"user's code```python\n{node.code_content}\n``` \n\n"
    prompt += get_check_prompt(node.metadata)

    prompt += f"explanation\n{node.explanation}\n\n"

    prompt += f"refinement direction\n{expand_direction}\n\n"

    if debug_history and node.parent:
        prompt += "\n Revision history: \n"
        parent_node = node.parent
        debug_history_budget = 2
        while parent_node and debug_history_budget:
            debug_history_budget -= 1
            prompt += f"\n{parent_node.question_content}\n"
            if not parent_node.execution_results_public:
                prompt += "Execution Results:\n"
                prompt += get_check_prompt(node.metadata)

    prompt += "```python\n# YOUR CODE HERE\n```\n\n"

    SYSTEM_PROMPT = PromptConstants.SYSTEM_MESSAGE_WITH_HISTORY if debug_history else PromptConstants.SYSTEM_MESSAGE_WITHOUT_HISTORY

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
    ]
    messages += [
        {
            "role": "user",
            "content": prompt,
        },
    ]


    return messages

def get_claude_reflection_generate(question, node, expand_direction, debug_history):
    prompt = ""
    prompt += f"Question:\n{question.question_content}\n\n"
    prompt += f"user's code```python\n{node.code_content}\n``` \n\n"
    prompt += get_check_prompt(node.metadata)

    prompt += f"explanation\n{node.explanation}\n\n"

    prompt += f"refinement direction\n{expand_direction}\n\n"

    if debug_history and node.parent:
        prompt += "\nHere is revision history for reference: \n"
        parents_node = node.parent

        debug_history_budget = 2
        while parents_node and debug_history_budget:
            for parent_node in parents_node:
                debug_history_budget -= 1
                prompt += f"\n{parent_node.code_content}\n"
                if not parent_node.execution_results_public:
                    prompt += get_check_prompt(node.metadata)
                parents_node = parent_node.parent

    prompt += "```python\n# YOUR CODE HERE\n```\n\n"

    SYSTEM_PROMPT = PromptConstants.SYSTEM_MESSAGE_WITH_HISTORY if debug_history else PromptConstants.SYSTEM_MESSAGE_WITHOUT_HISTORY

    return SYSTEM_PROMPT, prompt

def gen_debug(question, node, LLMSTYLE, debug_history, neighbor_strategy=True, exe_feedback=True):
    message = None

    used_directions = node.used_direction
    expand_direction = next((d for d in node.expand_direction if d not in used_directions), "")

    if any(model_name in LLMSTYLE for model_name in ["Qwen", "deepseek-ai"]):
        message = get_Qwen_reflection_generate(question, node, expand_direction, debug_history, neighbor_strategy, exe_feedback)
    elif "claude" in LLMSTYLE:
        message = get_claude_reflection_generate(question, node, expand_direction, debug_history)
    elif any(model_name in LLMSTYLE for model_name in ["DeepSeek-V3", "gpt"]):
        message = get_deepseek_v3_openai_reflection_generate(question, node, expand_direction, debug_history)
    return message, expand_direction