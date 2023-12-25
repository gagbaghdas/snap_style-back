from langchain import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from streaming import chain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import HumanMessage, AIMessage, SystemMessage

import re
import os


class PromptProcessor:
    def __init__(self):
        self.llm = ChatOpenAI(
            temperature=1, model="gpt-4", verbose=True
        )

    def get_keywords(self, user_input: str, user_gender: str, user_age: str, styles: str , city: str, weather: str) -> list:
        promt_template = f"""
            Given the user prompt {user_input},
            Generate search terms based on the prompt, considering
            user gender: {user_gender},
            user age: {user_age},
            user preferred styles: {styles}.
            user city: {city},
            current weather temperature: {weather}°C.
            Search terms then should be used for searching clothes in online stores.
            You should generate 2 search terms for the outfit (upper and lower).
            Search terms should be relevant to each other , so the outfit is matching.
            Output format: [upper search term, lower search term]
            If the prompt is not relevant to searching clothes, return [].
            """
        response_string = self.run_llm(
            promt_template
        )
        response_list = response_string.strip('][').split(', ')
        return response_list
    
    def get_prompts(self, user_gender: str, user_age: str, styles: str , city: str, weather: str) -> list:
        promt_template = f"""
            Given the below information about user, location and weather,
            Generate 4 prompts for the user to choose from.
            user gender: {user_gender},
            user age: {user_age},
            user preferred styles: {styles}.
            user city: {city},
            current weather temperature: {weather}°C.
            Prompts should be relevant to the user and the current trends.
            Prompts should be short, containing information about outfit type, color, style, etc.
            You should generate 4 prompts separated by a '###' symbol.
            Output format: [prompt1###prompt2###prompt3###prompt4]
            Example:[Cocktail outfit for the weekend, Christmas Outfit, Crazy Look mixing colors, Serious Suite for Business Lunch]
            """
        
        response_string = self.run_llm(
            promt_template
        )
        response_list = response_string.strip('][').split(', ')
        return response_list

    def run_llm(self, template: str, *args, **kwargs) -> any:
        input_variables = list(kwargs.keys())

        prompt_template = PromptTemplate(
            input_variables=input_variables, template=template
        )

        chain = LLMChain(llm=self.llm, prompt=prompt_template)

        result = chain.run({},**kwargs)
        return result
    