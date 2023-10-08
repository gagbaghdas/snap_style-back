import os

from langchain import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain, ConversationChain
from ingestion import get_summary
import re
from langchain.memory import ConversationSummaryMemory, ConversationBufferMemory
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import HumanMessage, AIMessage, SystemMessage
import json


class GameInsightExtractor:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=1, model="gpt-3.5-turbo", verbose=True)
        self.game_information = get_summary()
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            input_key="question",
        )
        self.subject = ""

    def get_prompts(self, text: str) -> list:
        self.subject = self.get_subject(text)
        if len(self.subject) == 0:
            self.subject = text

        print(self.subject)

        promt_template = """
            Given the game details {game_information} and a text excerpt {subject} from the game design document,
            generate up to four insightful SHORT prompts to explore valuable ideas later on.
            Each prompt should:
            - be as short as possible while still being relevant and insightful)
            - be relevant to text excerpt (IMPORTANT)
            - be relevant to the game details, genre and platform
            Output the prompts separated by a '###' symbol.
            """
        response_string = self.run_llm(
            promt_template, include_game_info=True, subject=self.subject
        )
        response_list = response_string.split("###")
        response_list = self.remove_numbering(response_list)
        return response_list

    def get_ideas(self, text: str) -> dict:
        promt_template = """
            With the game details {game_information} and the given context {text},
            propose 1 alternative strategy to enhance the game.
            Include:
                - Description
                - Benefits 
                - Potential use cases inspired by similar games
            Output the above information in a following format:
            description: <description> ### benefits: <benefits> ### use_case: <use_case>
            """
        result_str = self.run_llm(promt_template, include_game_info=True, text=text)

        result_dict = {}
        for line in result_str.split("###"):
            pieces = line.split(":", 1)
            if len(pieces) == 2:
                key, value = pieces
                result_dict[key.strip()] = value.strip()
            else:
                print(f"Unexpected format: {line}")

        self.init_new_conversation(text, result_str)
        return result_dict

    def init_new_conversation(self, user_question: str, ai_response: str):
        self.memory.clear()
        self.memory.save_context(
            {"input": user_question, "question": user_question}, {"output": ai_response}
        )

    def get_best_insight(self, text: str, old_insight: str) -> dict:
        best_insight = self.get_marketing_insights(text)
        if len(best_insight) == 0:
            return {}

        prompt_template = """
            Given the game details {game_information} and the list of useful insights {best_insight},
            find the most valuable insight and return it.
            Include:
                - Insight Description
                - Benefits 
                - Use cases from similar games
                - Source EXACT link
            Output the above information in a following format:
            description: <description> ### benefits: <benefits> ### use_cases: <use_cases> ### source: <source>
            """
        result_str = self.run_llm(
            prompt_template, include_game_info=True, best_insight=best_insight
        )
        if len(old_insight) > 0 and not self.is_new_insight_differ(
            old_insight, result_str
        ):
            return {}
        # Now parse the result_str into a dictionary
        result_dict = {}
        for line in result_str.split("###"):
            pieces = line.split(":", 1)
            if len(pieces) == 2:
                key, value = pieces
                result_dict[key.strip()] = value.strip()
            else:
                print(f"Unexpected format: {line}")

        return result_dict

    def is_new_insight_differ(self, old_inights, new_insights) -> bool:
        if len(old_inights) == 0 or len(new_insights) == 0:
            return False
        prompt_template = """
            Given the old_inights {old_inights} and the new insights {new_insights} ,
            find if they have significant difference.
            If they have significant difference, return True, otherwise return False.
            """
        result_str = self.run_llm(
            prompt_template, old_inights=old_inights, new_insights=new_insights
        )
        return result_str == "True"

    def get_marketing_insights(self, text: str) -> list:
        marketing_subject = self.get_subject(text)
        if len(marketing_subject) == 0:
            return ""

        promt_template = """
            Given the game details {game_information} and the summary {subject} from the game design document,
            generate insights by researching similar games online.
            Include:
                - Insight Description
                - Benefits 
                - Use cases from similar games
                - Source EXACT link
            Output insights separated by '###' or return an empty string if no insights are found.
            """
        return self.run_llm(
            promt_template, include_game_info=True, subject=marketing_subject
        )

    def get_subject(self, text: str) -> list:
        promt_template = """
            Given the game details {game_information} and text excerpt {text} from the game design document,
            1. Identify the subject of the text excerpt.
            2. If relevant to the game details, extract key information, categorize, and summarize.
            Return an empty string if the subject is irrelevant.
            """
        return self.run_llm(promt_template, include_game_info=True, text=text)

    def run_llm(self, template: str, include_game_info=False, *args, **kwargs) -> any:
        input_variables = list(kwargs.keys())

        if include_game_info:
            input_variables.append("game_information")

        prompt_template = PromptTemplate(
            input_variables=input_variables, template=template
        )

        chain = LLMChain(llm=self.llm, prompt=prompt_template)

        if include_game_info:
            result = chain.run(game_information=self.game_information, **kwargs)
        else:
            result = chain.run(**kwargs)

        return result

    def run_llm_chat(self, question: str) -> any:
        messages = [
            SystemMessagePromptTemplate.from_template(
                """You are a Senior Game Designer.
                        You are working on a game with details {game_information}.
                        The subject of the current game design document on which is your focus is:{subject}
                        You are having a conversation with a colleague about the game.
                        """
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{question}"),
        ]

        prompt = ChatPromptTemplate(
            input_variables=["question", "game_information", "subject", "chat_history"],
            messages=messages,
        )

        messages = prompt.format_messages(
            game_information=self.game_information,
            subject=self.subject,
            question=question,
            chat_history=self.memory.buffer_as_messages,
        )

        prompt.messages = messages

        self.memory.input_key = "question"
        conversation = LLMChain(
            llm=self.llm, prompt=prompt, verbose=True, memory=self.memory
        )
        result = conversation(
            {
                "question": question,
                "chat_history": self.memory.buffer_as_messages,
                "game_information": self.game_information,
                "subject": self.subject,
            }
        )
        print(result)
        serialized_data = json.dumps(result, default=self.custom_serializer)
        return serialized_data

    def custom_serializer(self, obj):
        if isinstance(obj, HumanMessage):
            return {"content": obj.content, "type": "human"}
        elif isinstance(obj, AIMessage):
            return {"content": obj.content, "type": "ai"}
        elif isinstance(obj, SystemMessage):
            return {"content": obj.content}
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def remove_numbering(self, prompts_list):
        updated_prompts = []
        for prompt in prompts_list:
            updated_prompt = re.sub(r"(?:\n|^)\d+[\.\s]*", "", prompt)
            updated_prompts.append(updated_prompt.strip())
        return updated_prompts
