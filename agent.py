
import openai
from openai import OpenAI

import anthropic

import os 
import config 


class DoctorAgent(object):
    """Doctor Agent Class"""

    def __init__(self,
                 model = "gpt-3.5-turbo",
                 system_instruction = "You are a doctor asking a patient about their medical history over an online chat interface. \
                You know nothing about the patient in advance. Respond in single turn dialogue\
                If the patient asks a question, be sure to answer it appropriately. Do not reveal you are an AI assistant.\
                Do not tell the patient to see a healthcare provider",
                api_key = "")
        
        self.model = model
        self.api_key = api_key

        if "gpt" in self.model:
            self.gpt = OpenAI(config.openai_api_key)
        
        elif "claude" in self.model:
            self.claude = anthropic.Anthropic(config.claude_api_key)
        
        








            
    )