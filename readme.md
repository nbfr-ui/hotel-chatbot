# Hotel booking chatbot

## Purpose
This project was developed within the scope of the Course: Project: AI Use Case (DLMAIPAIUC01)

## Requirements
This application was tested / developed exclusively on a Linux machine on a Chrome browser.

You need to install docker and python to execute the code.

In addition, a key for [openAI's ChatGPT API](https://platform.openai.com/docs/introduction) is required.

## Installation
Run 
`pip install -r requirements.txt`
to install all required python packages.

## Running the application
Execute
`python server.py`
to start the application.

The application will run a web server on port 8080.
In addition, it will run the docker image [rasa/duckling](https://hub.docker.com/r/rasa/duckling) on port 8000.

A file named 'openapi.key' must be created in the root folder of the project. 
The file content needs to be the openAI ChatGPT key.

Start the application by opening a browser and navigating to http://localhost:8080

## Fine-tuning

The application uses two separate models. 
The standard ChatGPT model and a fine-tuned model trained to returned structured data from chatbot.

You can run fine-tuning executing the following commands:
```
import openai

openai.api_key_path = './openapi.key'
response = openai.File.create(
  file=open("./training/structured-output.jsonl", "rb"),
  purpose='fine-tune'
)
```

Then use the file id returned
```
openai.FineTuningJob.create(training_file="FILE_ID_GOES_HERE", model="gpt-3.5-turbo", hyperparameters={ "n_epochs": 1 })
```

You can check the state of training using the returned job id:
```
openai.FineTuningJob.retrieve("ftjob-XYZ")
```

Oce the job has finished you can use the model when calling the ChatGPT api.

