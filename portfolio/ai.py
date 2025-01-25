import os
import functools
import tempfile
import base64

from dotenv import load_dotenv
from openai import OpenAI
import ollama
import os

from portfolio import logging

class AI():

    def __init__(self):
        self.prompts ={"default":""}
        with open(os.path.join(os.path.dirname(__file__),"data","default.prompt"),"r") as fh:
            self.prompts["default"] = fh.read()

    def ask(self, type, prompt:str = None , image_data = None):
        prompt = self.prompts["default"] if prompt is None else prompt
        if type == "chatgpt": 
            return self._ask_ChatGPT(prompt,image_data = image_data)
        elif type == "llama" or type=="llava": 
            return self._ask_Ollama(prompt,image_data = image_data, type=type)
        else:
            return ""

    def _ping_Llama(self):
        try:
            messages = [{'role': 'user', 'content': "what is the color of a rose?"}]
            response = ollama.chat(model='llama3.2', messages=messages)
            return response["message"]["content"]
        except Exception as e:
            logging.error(f"Error in ask_Llama: {e}")
            return ""

    def _ask_Ollama(self, prompt:str,image_data, type):
        try:
            model ="llava" if type=="llava" else 'llama3.2-vision'
            messages = [{'role': 'user', 'content': prompt, 'images': [image_data]}]
            response = ollama.chat(model=model, messages=messages)
            return response["message"]["content"]
        except Exception as e:
            logging.error(f"Error in ask_Llama: {e}")
            return ""

    def _ask_ChatGPT(self, prompt:str,image_data):
        try:
            load_dotenv()
            OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}, {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_data}"},
                    }]
                }]
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Error in ask_ChatGPT: {e}")
            return ""