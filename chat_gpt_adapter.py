import concurrent.futures
import logging
from functools import partial

import backoff
import openai


class FunctionCall:
    name: str
    arguments: str


class ChatGPTResponse:
    content: str
    function_call: FunctionCall | None


class ChatGptAdapter:
    """Implements an adapter to the ChatGPT API"""

    booking_model = "gpt-3.5-turbo-0613"
    structured_query_model = "ft:gpt-3.5-turbo-0613:personal::87KC7xOH"

    def _try_chat_completion(self, messages, functions, temperature, model) -> ChatGPTResponse:
        # openAI expects to find a file openapi.key in the root folder of the project containing the API key
        openai.api_key_path = './openapi.key'

        args = {
            'model': model,
            'messages': messages,
            'temperature': temperature
        }
        if functions is not None:
            args['functions'] = functions
            args['function_call'] = 'auto'
        response = openai.ChatCompletion.create(**args)
        response_message = response["choices"][0]["message"]
        logging.info('exit chat_completion')
        return response_message

    @backoff.on_exception(backoff.expo,
                          Exception,
                          max_tries=2)
    def _chat_completion_with_timeout(self, messages, functions, temperature, model) -> ChatGPTResponse:
        """ Sadly, chatGPT 'hangs' sometimes and there is no response for many minutes
        As a workaround for this issue a request is aborted after 10 seconds and a retry performed.s
        """
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(partial(self._try_chat_completion, messages, functions, temperature, model))
            return future.result(timeout=5)

    def chat_completion(self, messages, functions=None, temperature=0.5, model='gpt-3.5-turbo-0613') -> ChatGPTResponse:
        try:
            logging.info('enter chat_completion')
            return self._chat_completion_with_timeout(messages, functions, temperature, model)
        except Exception as e:
            logging.error(e)
            resp = ChatGPTResponse()
            resp.content = "Sorry. There was an issue transmitting the message. Could you repeat please?"
            logging.info('exit chat_completion with error')
            return resp
