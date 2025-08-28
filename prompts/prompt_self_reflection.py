import json
class PromptConstants:
    FIRST_EXPLANATION_WITH_HISTORY = '''You are an expert in debugging Python code. You will be provided with a code snippet that requires debugging, along with a revision history for reference.
Your task is to begin by writing a brief textual explanation of the current code—summarize its intended behavior and any evident issues between [explanation] and [/explanation].
Next, propose three refinement directions that could help improve the code. Please put each direction between tag [direction] and [/direction].

Important: Do not include any Python code in your response—only the explanation and the three refinement directions.

Example:
[explanation] The feedback indicates that the main issue is the function returns only the first element of min-k and max-k, instead of the entire lists. [/explanation]
[direction] Modify the return statement to return the full min-k and max-k lists. [/direction]
[direction] Add logic to handle cases where K is greater than the length of the input tuple. [/direction]
[direction] Include input validation to ensure K is a non-negative integer. [/direction]
'''

    FIRST_EXPLANATION_WITHOUT_HISTORY = '''You are an expert in debugging Python code. You will be provided with a code snippet that requires debugging.
Your task is to begin by writing a brief textual explanation of the current code—summarize its intended behavior and any evident issues between [explanation] and [/explanation].
Next, propose three refinement directions that could help improve the code. Please put each direction between tag [direction] and [/direction].

Important: Do not include any Python code in your response—only the explanation and the three refinement directions.

Example:
[explanation] The feedback indicates that the main issue is the function returns only the first element of min-k and max-k, instead of the entire lists. [/explanation]
[direction] Modify the return statement to return the full min-k and max-k lists. [/direction]
[direction] Add logic to handle cases where K is greater than the length of the input tuple. [/direction]
[direction] Include input validation to ensure K is a non-negative integer. [/direction]
'''

    FOLLOWING_DIRECTION_EXPAND_WITH_HISTORY = '''You are an expert in debugging Python code. You will receive a code snippet that needs debugging, along with its revision history, explanation, and some reference directions.

    Your task is to suggest one new refinement direction that could help enhance the code.

    Important: Do not include any Python code in your response—only provide a single, clearly stated refinement direction.

    Example:
    [direction] Modify the return statement to return the full min-k and max-k lists. [/direction]
            '''

    FOLLOWING_DIRECTION_EXPAND_WITHOUT_HISTORY = '''You are an expert in debugging Python code. You will receive a code snippet that needs debugging, along with its explanation, and some reference directions.

    Your task is to suggest one new refinement direction that could help enhance the code.

    Important: Do not include any Python code in your response—only provide a single, clearly stated refinement direction.

    Example:
    [direction] Modify the return statement to return the full min-k and max-k lists. [/direction]
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

def get_Qwen_reflection_generate(question, node, SYSTEM_PROMPT, debug_history, exe_feedback):

    prompt = SYSTEM_PROMPT + f"\nQuestion:\n{question.question_content}\n\n"
    prompt += f"Code:\n```python\n{node.code_content}\n``` \n\n"
    if exe_feedback:
        prompt += get_check_prompt(node.metadata)

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

    messages = [
            {"role": "system", "content": "You are an expert in debugging Python code."},
            {"role": "user", "content": prompt},
        ]

    return messages


def get_deepseek_v3_openai_reflection_generate(question, node, SYSTEM_PROMPT, debug_history):

    prompt = f"Question:\n{question.question_content}\n\n"

    prompt += f"code```python\n{node.code_content}\n``` \n\n"

    if not node.execution_results_public:
        prompt += "Execution Results:\n"
        prompt += get_check_prompt(node.metadata)

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

def get_claude_reflection_generate(question, node, SYSTEM_PROMPT, debug_history):
    prompt = f"Question:\n{question.question_content}\n\n"

    prompt += f"user's code```python\n{node.code_content}\n``` \n\n"

    if not node.execution_results_public:
        prompt += "Execution Results:\n"
        prompt += get_check_prompt(node.metadata)

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

    return SYSTEM_PROMPT, prompt

def gen_reflection(question, selected_node, LLMSTYLE, debug_history=True, exe_feedback=True):
    message = None

    if selected_node.expand_direction == []:

        SYSTEM_PROMPT = PromptConstants.FIRST_EXPLANATION_WITH_HISTORY if selected_node.parent is not None and debug_history else PromptConstants.FIRST_EXPLANATION_WITHOUT_HISTORY

        if any(model_name in LLMSTYLE for model_name in ["Qwen", "deepseek-ai"]):
            message = get_Qwen_reflection_generate(question, selected_node, SYSTEM_PROMPT, debug_history, exe_feedback)
        elif "claude" in LLMSTYLE:
            message = get_claude_reflection_generate(question, selected_node, SYSTEM_PROMPT, debug_history)
        elif any(model_name in LLMSTYLE for model_name in ["DeepSeek-V3", "gpt"]):
            message = get_deepseek_v3_openai_reflection_generate(question, selected_node, SYSTEM_PROMPT, debug_history)


    return message