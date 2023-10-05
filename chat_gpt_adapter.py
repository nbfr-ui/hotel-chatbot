import logging
import openai


class ChatGptAdapter:
    """Implements an adapter to the ChatGPT API"""
    def chat_completion(self, messages, temperature = 1) -> str:
        try:
            # openAI expects to find a file openapi.key in the root folder of the project containing the API key
            openai.api_key_path = './openapi.key'
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0613",
                messages=messages,
                temperature=temperature
            )
            response_message = response["choices"][0]["message"]
            return response_message.content

        except Exception as e:
            logging.error(e)
            return "Sorry. There was an issue transmitting the message. Could you repeat please?"

