import concurrent.futures
import logging
from functools import partial

import backoff
import openai


class ChatGptAdapter:
    """Implements an adapter to the ChatGPT API"""

    booking_model = "gpt-3.5-turbo-0613"
    structured_query_model = "ft:gpt-3.5-turbo-0613:personal::87fl6OLL"

    def chat_completion(self, messages, temperature=0.5, model='gpt-3.5-turbo-0613') -> str:
        """ calls the ChatGPT API with the messages given as parameters as input """
        try:
            logging.info('enter chat_completion')
            return self.__chat_completion_with_timeout(messages, temperature, model)
        except Exception as e:
            logging.error(e)
            logging.info('exit chat_completion with error')
            return "Sorry. There was an issue transmitting the message. Could you repeat please?"


    def __try_chat_completion(self, messages, temperature, model) -> str:
        # openAI expects to find a file openapi.key in the root folder of the project containing the API key
        openai.api_key_path = './openapi.key'

        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        response_message = response["choices"][0]["message"]
        logging.info('exit chat_completion')
        return response_message.content

    @backoff.on_exception(backoff.expo,
                          Exception,
                          max_tries=2)
    def __chat_completion_with_timeout(self, messages, temperature, model) -> str:
        """ Sadly, chatGPT 'hangs' sometimes and there is no response for many minutes
        As a workaround for this issue a request is aborted after some seconds and a retry performed.s
        """
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(partial(self.__try_chat_completion, messages, temperature, model))
            return future.result(timeout=5)
