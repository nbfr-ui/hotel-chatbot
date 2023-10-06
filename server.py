import logging

import docker
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from chat_bot import ChatBot

app = FastAPI()
chat_bot = ChatBot()


class Message(BaseModel):
    text: str
    sessionId: str


class TextResponse(BaseModel):
    text: str
    flag: None | str


session_store = {}


@app.post("/chat/", response_model=TextResponse)
async def send_msg(msg: Message):
    """Received messages from the user and send a text response"""
    logging.info(f"/chat: {msg.text}")
    if len(msg.text) > 400:
        return {'text': "Your message is too long. Please provide a shorter text", 'flag': None}

    if msg.sessionId not in session_store:
        session_store[msg.sessionId] = []
    session_msg = session_store[msg.sessionId]
    session_msg.append({"role": "user", "content": msg.text})

    response = chat_bot.continue_chat(session_msg)
    session_msg.append({"role": "assistant", "content": response['text']})
    logging.info(f"/chat: response: {response}")
    return response


app.mount("/", StaticFiles(directory="static", html=True), name="static")


def stop_any_duckling_docker_container(client):
    """Stops any docker containers created fromm the rasa/duckling image which might still be running"""
    for container in client.containers.list():
        if str(container.image).find('rasa/duckling') > -1:
            logging.info("Found a running rasa/duckling container. Stopping container")
            container.stop()
            logging.info("Done.")


if __name__ == "__main__":
    container = None
    try:
        client = docker.from_env()
        stop_any_duckling_docker_container(client)
        logging.info("Starting duckling docker container on port 8000")
        container = client.containers.run("rasa/duckling", "", ports={8000: 8000}, detach=True)

        logging.info("Starting server on port 8080.")
        uvicorn.run("server:app", port=8080, host='0.0.0.0', reload=True, log_config='./log.ini')
    finally:
        if container is not None:
            try:
                logging.info("Stopping docker container...")
                container.stop()
                logging.info("Done...")
            except Exception as e:
                logging.error("Error stopping docker container", e)
                pass
