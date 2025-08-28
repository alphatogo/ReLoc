
class PromptConstants:
    SYSTEM_MESSAGE_Observation = f"You are an expert Python programmer. You will be given an competitive programming question(problem specification). You will return 5 useful, non-obvious, and correct observations about the problem, like hints to solve the problem. You will NOT return any code. Be as creative as possible, going beyond what you think is intuitively correct. For each observations should between tag [OBSERVATION] and [\OBSERVATION]."

    SYSTEM_MESSAGE_Backtranslation = f"You are an expert Python programmer. You will be given a question (problem specification) and intelligent observations that describes how to solve the problem. You will generate a correct Python program that matches said specification and tutorial and passes all tests. You will NOT return anything except for the program."

    FORMATTING_MESSAGE_WITH_STARTER_CODE = "You will use the following starter code to write the solution to the problem and enclose your code within delimiters."

    FORMATTING_WITHOUT_STARTER_CODE = "Read the inputs from stdin solve the problem and write the answer to stdout (do not directly test on the sample inputs). Enclose your code within delimiters as follows."


def get_Qwen_bon_generate(question, gen_type, Observations=None):
    prompt = None
    if gen_type == "Observation":
        prompt = "You are an expert Python programmer. You will be given an competitive programming question(problem specification). You will return 5 useful, non-obvious, and correct observations about the problem, like hints to solve the problem. You will NOT return any code. Be as creative as possible, going beyond what you think is intuitively correct. For each observations should between tag [OBSERVATION] and [\OBSERVATION]\n\n"

        prompt += f"Question:\n{question.question_content}\n\n"

    elif gen_type == "Backtranslation":
        prompt = "You are an expert Python programmer. You will be given a question (problem specification) and intelligent observations that describes how to solve the problem. You will generate a correct Python program that matches said specification and tutorial and passes all tests. You will NOT return anything except for the program.\n\n"

        prompt += f"Question:\n{question.question_content}\n\n"

        prompt += f"Here are the intelligent observations to help solve the problem:\n"
        for i,Observation in enumerate(Observations):
            prompt += f"Observation {i}:{Observation}\n"

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


def get_deepseek_v3_openai_bon_generate(question, gen_type, Observations=None):
    messages = None

    if gen_type == "Observation":
        prompt = f"### Question:\n{question.question_content}\n\n"

        messages = [
            {
                "role": "system",
                "content": PromptConstants.SYSTEM_MESSAGE_Observation,
            },
        ]
        messages += [
            {
                "role": "user",
                "content": prompt,
            },
        ]

    elif gen_type == "Backtranslation":
        prompt = f"### Question:\n{question.question_content}\n\n"

        prompt += f"### Here are the intelligent observations to help solve the problem:\n"
        for i, Observation in enumerate(Observations):
            prompt += f"### Observation {i}:{Observation}\n"

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
                "content": PromptConstants.SYSTEM_MESSAGE_Backtranslation,
            },
        ]
        messages += [
            {
                "role": "user",
                "content": prompt,
            },
        ]

    return messages

def get_claude_bon_generate(question, gen_type, Observations=None):
    if gen_type == "Observation":
        prompt = f"### Question:\n{question.question_content}\n\n"

        return PromptConstants.SYSTEM_MESSAGE_Observation, prompt

    elif gen_type == "Backtranslation":
        prompt = f"### Question:\n{question.question_content}\n\n"
        prompt += f"### Here are the intelligent observations to help solve the problem:\n"
        for i, Observation in enumerate(Observations):
            prompt += f"### Observation {i}:{Observation}\n"

        if question.starter_code:
            prompt += (
                f"### Format: {PromptConstants.FORMATTING_MESSAGE_WITH_STARTER_CODE}\n"
            )
            prompt += f"```python\n{question.starter_code}\n```\n\n"
        else:
            prompt += f"### Format: {PromptConstants.FORMATTING_WITHOUT_STARTER_CODE}\n"
            prompt += "```python\n# YOUR CODE HERE\n```\n\n"
        prompt += f"### Answer: (use the provided format with backticks)\n\n"

        return [PromptConstants.SYSTEM_MESSAGE_Backtranslation, prompt]





def gen_idea_search_generate(question, LLMSTYLE, gen_type="Observation", Observations = None):
    message = None
    if any(model_name in LLMSTYLE for model_name in ["Qwen", "deepseek-ai"]):
        message = get_Qwen_bon_generate(question, gen_type, Observations)
    elif "claude" in LLMSTYLE:
        message = get_claude_bon_generate(question, gen_type, Observations)
    elif any(model_name in LLMSTYLE for model_name in ["DeepSeek-V3", "gpt"]):
        message = get_deepseek_v3_openai_bon_generate(question, gen_type, Observations)

    return message