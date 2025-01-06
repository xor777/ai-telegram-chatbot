import os
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from .memory_store import UserMemoryStore
import logging

class ChainManager:
    def __init__(self, api_key: str):
        self.llm = ChatOpenAI(
            model_name=os.environ.get("CHAT_MODEL", "deepseek-chat"),
            openai_api_key=api_key,
            max_tokens=int(os.environ.get("CHAT_MODEL_MAX_TOKENS", "1000")),
            base_url="https://api.deepseek.com/v1"
        )
        self.memory_store = UserMemoryStore()
        
        prompt_path = Path(__file__).parent / "prompts" / "system_prompt.txt"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read()
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])
        
        chain = self.prompt | self.llm
        
        self.chain_with_history = RunnableWithMessageHistory(
            chain,
            lambda username: self.memory_store.get_history(username),
            input_messages_key="input",
            history_messages_key="history"
        )
        
    def get_response(self, username: str, message: str) -> str:
        logging.info(f"[{username}] Processing message in chain")
        response = self.chain_with_history.invoke(
            {"input": message},
            config={"configurable": {"session_id": username}}
        )
        logging.info(f"[{username}] Chain processing completed")
        return response.content
    
    def clear_context(self, username: str) -> None:
        logging.info(f"[{username}] Clearing conversation history")
        self.memory_store.clear_history(username) 