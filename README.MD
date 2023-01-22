
Telegram bot interface to GPT-3  

To run it, create .env file into the project directory and set an environment variables:  
  
% touch .env  
% echo OPEN_AI_KEY=<YOUR OPEN AI API KEY> > .env  
% echo TELEGRAM_BOT_KEY=<YOUR TELEGRAM BOT KEY> >.env  
  
modify allowed_users. only allowed users can use the bot  
each authorised user can add new user with /add_user command  
example: /add_user xor777  
you should specify telegram monicker without "@"  

