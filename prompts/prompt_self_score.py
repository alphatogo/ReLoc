import json
class PromptConstants:
    SYSTEM_MESSAGE_Score_Gen = '''You are a skilled code reviewer and evaluator. You are responsible for **scoring assistant responses to Python programming problems** based on the following criteria.

Given the python programming problem and  python code responses from the Assistant, follow the steps below to **evaluate and compare** the solutions.

## Correctness Evaluation Guide for Python Code

When evaluating Python code responses, focus **only on correctness**, based on the following four core dimensions:

---

### 1. **Does the code run without syntax or compile-time errors?**

- If the code cannot run at all due to syntax or indentation errors, **this is a critical failure**.
- Even if the logic looks fine, un-runnable code receives a **very low score**.

---

### 2. **Does the code crash during execution? (Runtime Errors)**

- If the code crashes (e.g. `IndexError`, `TypeError`, `ZeroDivisionError`, etc.), the correctness is compromised.
- A single, unhandled runtime error in typical input usage significantly reduces the score.
- If errors only appear in rare edge cases, deduct moderately.

---

### 3. **Does the code time out on large or worst-case inputs?**

- If the solution has poor time complexity and **fails to return within reasonable time**, it’s a major issue for correctness.
- Solutions must be **functionally correct *and* practically usable**.
- Timeout indicates failure under problem constraints, and results in a substantial score reduction.

---

### 4. **Does the code return correct outputs for all relevant inputs?**

- Fully correct output across normal and edge cases → high score.
- Partially correct logic (e.g. fails edge cases or special formats) → medium score.
- Wrong outputs for core functionality → low score.

---

### Final Scoring Logic

Score should reflect the **overall functional correctness** of the code, factoring in all of the above.

Use the following **score guidelines (0–10)**:

- **9–10**: Code runs successfully, no errors, returns correct results on all inputs including edge cases.
- **7–8**: Code works and returns correct output on most inputs; minor issues like one missed edge case.
- **5–6**: Code mostly works, but fails for several common or edge inputs, or has minor runtime issues.
- **3–4**: Code contains logic errors or crashes in common usage scenarios.
- **1–2**: Code does not produce correct results and crashes regularly; may contain multiple bugs.
- **0**: Code does not run at all due to syntax/compile errors or is completely unrelated.

---

### Output Format
Remember: output the score between <score> and </score>

At the end of your evaluation, return the score as follows:
For example:
```text
<score>7</score>
```
    '''

def get_Qwen_score_generate(question, Code):

    prompt =  f"Question:\n{question.question_content}\n\n"
    prompt += f"code```python\n{Code}\n``` \n\n"
    messages = [
        {"role": "system", "content": PromptConstants.SYSTEM_MESSAGE_Score_Gen},
        {"role": "user", "content": prompt},
    ]

    return messages

def get_deepseek_v3_openai_score_generate(question, Code, Gen_reward=False, execution_results=None):
    prompt = f"### Question:\n{question.question_content}\n\n"
    prompt += f"### code```python\n{Code}\n``` \n\n"

    messages = [
        {
            "role": "system",
            "content": PromptConstants.SYSTEM_MESSAGE_Score_Gen,
        },
    ]
    messages += [
        {
            "role": "user",
            "content": prompt,
        },
    ]
    return messages

def get_claude_score_generate(question, Code, Gen_reward=False, execution_results=None):

    prompt = f"### Question:\n{question.question_content}\n\n"
    prompt += f"### code```python\n{Code}\n``` \n\n"
    return PromptConstants.SYSTEM_MESSAGE_Score_Gen, prompt


def gen_score(question, code, LLMSTYLE):
    message = None
    if any(model_name in LLMSTYLE for model_name in ["Qwen", "deepseek-ai"]):
        message = get_Qwen_score_generate(question, code)
    elif "claude" in LLMSTYLE:
        message = get_claude_score_generate(question, code)
    elif any(model_name in LLMSTYLE for model_name in ["DeepSeek-V3", "gpt"]):
        message = get_deepseek_v3_openai_score_generate(question, code)

    return message
