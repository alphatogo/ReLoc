import re
def Qwen_runner_vllm(Qwen_model, Qwen_tokenizer, sampling_params, message, args, problem):

   
    prompt = Qwen_tokenizer.apply_chat_template(
        message,
        tokenize=False,
        add_generation_prompt=True,
        truncation=False,
        padding=False,
    )


    if type(prompt) != list:
        prompt = [prompt]

    outputs = Qwen_model.generate(prompt, sampling_params)



    token_consume = 0
    answer_inits = []
    for output in outputs:
        for generated_text in output.outputs:
            text = generated_text.text
            answer_inits.append(text)
            token_consume += len(generated_text.token_ids)
    return answer_inits, token_consume


def Qwen_runner_tf(Qwen_model, Qwen_tokenizer, sampling_params, message, generate_num):
    answer = []
    for _ in range(generate_num):
        text = Qwen_tokenizer.apply_chat_template(
            message,
            tokenize=False,
            add_generation_prompt=True
        )
        model_inputs = Qwen_tokenizer([text], return_tensors="pt").to(Qwen_model.device)

        generated_ids = Qwen_model.generate(
            **model_inputs,
            **sampling_params
        )
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]

        response = Qwen_tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

        answer.append(response)


    return answer


