from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
from typing import Dict, List
import logging

class ChatHistory(BaseChatMessageHistory):
    def __init__(self):
        self.messages: List = []
    
    def add_message(self, message):
        self.messages.append(message)
    
    def clear(self):
        self.messages = []

class UserMemoryStore:
    def __init__(self):
        self.histories: Dict[str, ChatHistory] = {}
        
    def get_history(self, username: str) -> ChatHistory:
        if username not in self.histories:
            logging.info(f"[{username}] Creating new chat history")
            self.histories[username] = ChatHistory()
        return self.histories[username]
    
    def clear_history(self, username: str) -> None:
        if username in self.histories:
            self.histories[username].clear()
            logging.info(f"[{username}] Cleared conversation history") 