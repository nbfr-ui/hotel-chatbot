import logging

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

    @backoff.on_exception(backoff.expo,
                          Exception,
                          max_tries=3,
                          max_time=10)
    def _try_chat_completion(self, messages, functions=None, temperature=0.5,
                             model='gpt-3.5-turbo-0613') -> ChatGPTResponse:
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

    def chat_completion(self, messages, functions=None, temperature=0.5, model='gpt-3.5-turbo-0613') -> ChatGPTResponse:
        try:
            logging.info('enter chat_completion')
            return self._try_chat_completion(messages, functions, temperature, model)
        except Exception as e:
            logging.error(e)
            resp = ChatGPTResponse()
            resp.content = "Sorry. There was an issue transmitting the message. Could you repeat please?"
            logging.info('exit chat_completion with error')
            return resp
