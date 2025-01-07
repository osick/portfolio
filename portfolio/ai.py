import os
import functools
import tempfile
import base64

from dotenv import load_dotenv
from openai import OpenAI
import ollama

from portfolio import logging

class AI():

    user_prompt = """
    You are a Stock Trader specializing in Technical Analysis at a top financial institution and you are avoing higher risks and you have a long term mindset.
    Analyze the stock chart's technical indicators and provide a buy/hold/sell recommendation.
    Base your recommendation only on chart and the displayed technical indicators. 
    First, provide the recommendation, then, provide your detailed reasoning.
    Finally provied the expected target price for the stock. The Price forecast should be given for at least 2 - 3 months.
    Your response should be given as correct markdown (smaller font)
    """
    
    def ask(self, type, prompt:str = None , image_data = None):
        prompt = AI.user_prompt if prompt is None else prompt
        if type == "ChatGPT": 
            return self._ask_ChatGPT(prompt,image_data = image_data)
        elif type == "Llama": 
            return self._ask_Llama(prompt,image_data = image_data)
        else:
            return ""
            
    def _ask_Llama(self, prompt,image_data):
        try:
            messages = [{'role': 'user', 'content': prompt, 'images': image_data}]
            response = ollama.chat(model='llama3.2-vision', messages=messages)
            return response["message"]["content"]
        except Exception as e:
            logging.error(f"Error in ask_Llama: {e}")
            return ""

    def _ask_ChatGPT(self, prompt,image_data):
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