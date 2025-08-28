
class PromptConstants:
    SYSTEM_MESSAGE_TEST_CASE = '''You are an expert TEST CASE GENERATOR for programming competitions. Your ONLY task is to ONE TEST CASE of a specific type, NOT to solve the problem or write any implementation code.

Follow these strict guidelines:
1. DO NOT write any solution code in any programming language.
2. DO NOT attempt to solve the problem yourself.
3. FOCUS EXCLUSIVELY on generating a test case included input and output.

For the test case you create, provide:
* The test input exactly as it would be fed to a program.
* The expected output that a correct solution should produce.
* A brief explanation of what aspect this test case is verifying.

Ensure the output follows the *Expected Output Format* structure provided. You must enclose the output in a json block to facilitate easy extraction and processing.

Problem Description: {problem}

Here is expected Output Format:
{expected_output}

You must ONLY provide ONE expected test case between tag <TEST> and </TEST> follow the expected output format. Ensure your test case is valid according to the problem constraints.'''


def get_Qwen_bon_generate(question):
    prompt = PromptConstants.SYSTEM_MESSAGE_TEST_CASE.format(problem=question.question_content, expected_output=question.public_test_case["input_output"])

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

def gen_test_case(question, LLMSTYLE):
    message = None
    if any(model_name in LLMSTYLE for model_name in ["Qwen", "deepseek-ai"]):
        message = get_Qwen_bon_generate(question)
    elif "claude" in LLMSTYLE:
        message = get_claude_bon_generate(question)
    elif any(model_name in LLMSTYLE for model_name in ["DeepSeek-V3", "gpt"]):
        message = get_deepseek_v3_openai_bon_generate(question)

    return message
