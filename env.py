import os
from dotenv import load_dotenv
load_dotenv()

try:
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    PORT = int(os.getenv('PORT', '5000'))
except:
    print(u"\u001b[31m在讀取環境變數值時發生錯誤！\u001b[0m")
    raise