import os
from time import sleep
import openai
from openai import OpenAI


def Openai_runner(client, client_kwargs, message):

    try:
        response = client.chat.completions.create(
            messages=message,
            **client_kwargs,
        )
    except (
            openai.APIError,
            openai.RateLimitError,
            openai.InternalServerError,
            openai.OpenAIError,
            openai.APIStatusError,
            openai.APITimeoutError,
            openai.InternalServerError,
            openai.APIConnectionError,
    ) as e:
        print("Exception: ", repr(e))
        print("Sleeping for 30 seconds...")
        print("Consider reducing the number of parallel processes.")
        sleep(30)
        return Openai_runner(client, client_kwargs, message)
    except Exception as e:
        print(f"Failed to run the model for {message}!")
        print("Exception: ", repr(e))
        raise e
    return [c.message.content for c in response.choices], response.usage.completion_tokens