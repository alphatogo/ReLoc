import json
class PromptConstants:


    SYSTEM_MESSAGE_WITHOUT_HISTORY = '''You are a helpful programming assistant and an expert in Python. The user has written code that contains errors. Your task is to debug and revise the code to correctly solve the problem.  
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


def get_Qwen_reflection_generate(question, node, debug_history):

    prompt = PromptConstants.SYSTEM_MESSAGE_WITHOUT_HISTORY
    prompt += f"\nQuestion:\n{question.question_content}\n\n"
    prompt += f"user's code:\n```python\n{node.code_content}\n``` \n\n"
    prompt += get_check_prompt(node.metadata)


    prompt += "```python\n# YOUR CODE HERE\n```\n\n"


    messages = [
        {"role": "system", "content": "You are a helpful programming assistant and an expert in Python."},
        {"role": "user", "content": prompt},
    ]
    return messages


def get_deepseek_v3_openai_reflection_generate(question, node, debug_history):
    messages = None

    prompt = ""
    prompt += f"Question:\n{question.question_content}\n\n"
    prompt += f"user's code```python\n{node.code_content}\n``` \n\n"
    prompt += get_check_prompt(node.metadata)

    prompt += "```python\n# YOUR CODE HERE\n```\n\n"

    SYSTEM_PROMPT = PromptConstants.SYSTEM_MESSAGE_WITHOUT_HISTORY

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

def get_claude_reflection_generate(question, node,debug_history):
    prompt = ""
    prompt += f"Question:\n{question.question_content}\n\n"
    prompt += f"user's code```python\n{node.code_content}\n``` \n\n"
    prompt += get_check_prompt(node.metadata)

    prompt += "```python\n# YOUR CODE HERE\n```\n\n"

    SYSTEM_PROMPT = PromptConstants.SYSTEM_MESSAGE_WITHOUT_HISTORY

    return SYSTEM_PROMPT, prompt

def gen_debug(question, node, LLMSTYLE, debug_history):
    message = None

    if any(model_name in LLMSTYLE for model_name in ["Qwen", "deepseek-ai"]):
        message = get_Qwen_reflection_generate(question, node, debug_history)
    elif "claude" in LLMSTYLE:
        message = get_claude_reflection_generate(question, node, debug_history)
    elif any(model_name in LLMSTYLE for model_name in ["DeepSeek-V3", "gpt"]):
        message = get_deepseek_v3_openai_reflection_generate(question, node, debug_history)
    return message