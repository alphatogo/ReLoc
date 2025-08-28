import json
class PromptConstants:

    SYSTEM_MESSAGE_WITHOUT_HISTORY = '''You are a helpful programming assistant and an expert in Python. The user has written code that contains errors. You will be provided with a Python programming problem and the user's code intended to solve it. Your task is to refer to the input code and revise it to correctly solve the problem.
Generate a corrected version of the complete program. 
**Output only one corrected program enclosed within a single pair of code delimiters. Do not include any additional commentary or text.**
'''

    SYSTEM_MESSAGE_WITH_HISTORY = '''You are a helpful programming assistant and an expert in Python. The user has written code that contains errors. You will be provided with a Python programming problem, the user's code and revision history. Your task is to refer to all the code and revise it to correctly solve the problem.
    Generate a corrected version of the complete program. 
    **Output only one corrected program enclosed within a single pair of code delimiters. Do not include any additional commentary or text.**
    '''



def get_check_prompt(metadata):

    metadata = json.loads(metadata)
    message = "Execution Results:\n"
    if "error_code" not in metadata:
        return ""
    if metadata["error_code"] == -1:
        # time limit exceeded
        message += f"The above code is incorrect and got the following compilation error.\n{metadata['error']}"
    elif metadata["error_code"] == -2:
        # wrong answer
        message += f"The above code is incorrect and got a wrong answer.\nInput: {metadata['inputs']}\nGenerated Output: {metadata['output']}\nExpected: {metadata['expected']}"
    elif metadata["error_code"] == -3:
        # time limit exceeded
        message += f"The above code is incorrect and got time limit exceeded.\n{metadata['error']}\nInput: {metadata['inputs']}\nExpected: {metadata['expected']}"
        pass
    elif metadata["error_code"] == -4:
        # runtime error
        message += f"The above code is incorrect and got a runtime error.\nInput: {metadata['inputs']}\nExpected: {metadata['expected']}\n{metadata['error']}"
    else:
        message += f"The above code is incorrect"
    return message


def get_Qwen_reflection_generate(question, node_list, debug_history):
    if debug_history:
        prompt = PromptConstants.SYSTEM_MESSAGE_WITH_HISTORY
    else:
        prompt = PromptConstants.SYSTEM_MESSAGE_WITHOUT_HISTORY

    prompt += f"\nQuestion:\n{question.question_content}\n\n"

    for index, node in enumerate(node_list):

        prompt += f"User's code {index+1}:\n```python\n{node.code_content}\n``` \n\n"
        prompt += get_check_prompt(node.metadata)


    if debug_history:
        for node in node_list:
            if node.parent:
                prompt += "\nHere is revision history for reference: \n"
                current = node.parent

                for _ in range(3):
                    if not current:
                        break
                    for parent in current:
                        if parent != node:
                            prompt += f"\n{parent.code_content}\n"
                            if not parent.execution_results_public:
                                prompt += get_check_prompt(node.metadata)
                            current = parent.parent
                            break
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

def gen_debug_GEN(question, node_list, LLMSTYLE, debug_history=False):
    message = None
    if any(model_name in LLMSTYLE for model_name in ["Qwen", "deepseek-ai"]):
        message = get_Qwen_reflection_generate(question, node_list, debug_history)
    elif "claude" in LLMSTYLE:
        message = get_claude_reflection_generate(question, node_list)
    elif any(model_name in LLMSTYLE for model_name in ["DeepSeek-V3", "gpt"]):
        message = get_deepseek_v3_openai_reflection_generate(question, node_list)
    return message