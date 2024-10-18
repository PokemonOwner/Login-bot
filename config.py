import os

#Bot token @Botfather
BOT_TOKEN = os.environ.get("BOT_TOKEN", "6502269483:AAGSzIEpRMLH0BA0rCkTOHWizO131mWadh0")

#Your API ID from my.telegram.org
API_ID = int(os.environ.get("API_ID", "28304192"))

#Your API Hash from my.telegram.org
API_HASH = os.environ.get("API_HASH", "f82c0bafa1a0d59c8e31cd501791a5cc")

#Database 
DB_URI = os.environ.get("DB_URI", "mongodb+srv://cluster:efAbVEB6oUXUsJu7@cluster0.twhpwa4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
