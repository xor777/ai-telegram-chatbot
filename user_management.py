import json
import logging
import argparse
import os
from typing import List, Dict

class UserManager:
    def __init__(self, config_file: str = "allowed_users.json"):
        self.config_file = config_file
        self.allowed_users = self._load_users()
        
    def _load_users(self) -> List[Dict]:
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Error parsing {self.config_file}: {str(e)}")
                
        return self._initialize_admin()
    
    def _initialize_admin(self) -> List[Dict]:
        parser = argparse.ArgumentParser()
        parser.add_argument("-admin", help="specify admin username")
        args = parser.parse_args()
        
        admin_username = args.admin if args.admin else input("Enter bot admin telegram username: ")
        if not admin_username:
            raise ValueError("No admin specified. Use -admin argument or enter manually")
            
        admin_username = admin_username.lstrip("@")
        logging.info(f"Bot admin is {admin_username}")
        
        users = [{"username": admin_username}]
        self._dump_users(users)
        return users
    
    def _dump_users(self, users: List[Dict]) -> None:
        with open(self.config_file, "w") as file:
            json.dump(users, file)
    
    def is_user_allowed(self, message) -> bool:
        username = message.from_user.username
        is_allowed = any(user["username"] == username for user in self.allowed_users)
        
        if not is_allowed:
            logging.warning(f"[{username}] Unauthorized access attempt")
            
        return is_allowed
    
    def add_user(self, username: str) -> bool:
        username = username.lstrip("@")
        if any(user["username"] == username for user in self.allowed_users):
            logging.info(f"[{username}] User already in allowed list")
            return False
            
        self.allowed_users.append({"username": username})
        self._dump_users(self.allowed_users)
        logging.info(f"[{username}] Added new user to allowed list")
        return True 