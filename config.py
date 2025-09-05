import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN') or '7910995507:AAEoOR8OdaqkSFyWhr5mIFmGJ1wus-7fPUk'
    TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID') or '-1002275825444'
    TELEGRAM_SUPPORT_CHAT_ID = os.environ.get('TELEGRAM_SUPPORT_CHAT_ID') or '6170955463'