from gtts import gTTS
import playsound
import uuid
import os

def speak(text, folder="voices"):
    if not os.path.exists(folder):
        os.makedirs(folder)
    filename = f"{folder}/bot_reply_{uuid.uuid4()}.mp3"
    tts = gTTS(text=text, lang='en')
    tts.save(filename)
    playsound.playsound(filename)
