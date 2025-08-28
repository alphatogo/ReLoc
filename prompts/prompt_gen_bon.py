
class PromptConstants:
    SYSTEM_MESSAGE_GENERIC = f"You are an expert Python programmer. You will be given a question (problem specification) and will generate a correct Python program that matches the specification and passes all tests. You will NOT return anything except for the program."


    FORMATTING_MESSAGE_WITH_STARTER_CODE = "You will use the following starter code to write the solution to the problem and enclose your code within delimiters."

    FORMATTING_WITHOUT_STARTER_CODE = "Read the inputs from stdin solve the problem and write the answer to stdout (do not directly test on the sample inputs). Enclose your code within delimiters as follows."


def get_Qwen_bon_generate(question):
    prompt = "You will be given a question (problem specification) and will generate a correct Python program that matches the specification and passes all tests. You will NOT return anything except for the program.\n\n"
    prompt += f"Question:\n{question.question_content}\n\n"
    if question.starter_code:
        prompt += f"{PromptConstants.FORMATTING_MESSAGE_WITH_STARTER_CODE}\n"
        prompt += f"```python\n{question.starter_code}\n```\n\n"
    else:
        prompt += f"{PromptConstants.FORMATTING_WITHOUT_STARTER_CODE}\n\n"
        prompt += f"```python\n# YOUR CODE HERE\n```\n\n"

    messages = [
        {"role": "system", "content": "You are an expert Python programmer."},
        {"role": "user", "content": prompt},
    ]
    return messages


def get_deepseek_v3_openai_bon_generate(question):
    prompt = f"### Question:\n{question.question_content}\n\n"
    if question.starter_code:
        prompt += (
            f"### Format: {PromptConstants.FORMATTING_MESSAGE_WITH_STARTER_CODE}\n"
        )
        prompt += f"```python\n{question.starter_code}\n```\n\n"
    else:
        prompt += f"### Format: {PromptConstants.FORMATTING_WITHOUT_STARTER_CODE}\n"
        prompt += "```python\n# YOUR CODE HERE\n```\n\n"
    prompt += f"### Answer: (use the provided format with backticks)\n\n"

    messages = [
        {
            "role": "system",
            "content": PromptConstants.SYSTEM_MESSAGE_GENERIC,
        },
    ]
    messages += [
        {
            "role": "user",
            "content": prompt,
        },
    ]
    return messages

def get_claude_bon_generate(question):
    prompt = f"### Question:\n{question.question_content}\n\n"
    if question.starter_code:
        prompt += (
            f"### Format: {PromptConstants.FORMATTING_MESSAGE_WITH_STARTER_CODE}\n"
        )
        prompt += f"```python\n{question.starter_code}\n```\n\n"
    else:
        prompt += f"### Format: {PromptConstants.FORMATTING_WITHOUT_STARTER_CODE}\n"
        prompt += "```python\n# YOUR CODE HERE\n```\n\n"
    prompt += f"### Answer: (use the provided format with backticks)\n\n"

    return [PromptConstants.SYSTEM_MESSAGE_GENERIC, prompt]

def gen_bon_generate(question, LLMSTYLE):
    message = None
    if any(model_name in LLMSTYLE for model_name in ["Qwen", "deepseek-ai"]):
        message = get_Qwen_bon_generate(question)
    elif "claude" in LLMSTYLE:
        message = get_claude_bon_generate(question)
    elif any(model_name in LLMSTYLE for model_name in ["DeepSeek-V3", "gpt"]):
        message = get_deepseek_v3_openai_bon_generate(question)

    return message
