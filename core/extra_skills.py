import time
import re
import wikipedia
from core.text_to_speech import speak

def repeat_after_me(command):
    if "repeat after me" in command:
        to_repeat = command.split("repeat after me", 1)[-1].strip()
    elif "say" in command:
        to_repeat = command.split("say", 1)[-1].strip()
    else:
        return False

    if to_repeat:
        speak(to_repeat)
        return True

    return False


def tell_about_topic(command):
    trigger_phrases = ["do you know about", "tell me about", "who is", "what do you know about"]
    for phrase in trigger_phrases:
        if phrase in command.lower():
            try:
                topic = command.lower()
                for p in trigger_phrases:
                    topic = topic.replace(p, "")
                topic = topic.strip()
                summary = wikipedia.summary(topic, sentences=2)
                speak(summary)
            except wikipedia.exceptions.DisambiguationError:
                speak(f"There are multiple entries for {topic}. Please be more specific.")
            except wikipedia.exceptions.PageError:
                speak(f"I couldn't find any information about {topic}.")
            return True
    return False


def explain_meaning(command):
    trigger_phrases = ["what do you mean by", "define", "explain", "what is"]
    for phrase in trigger_phrases:
        if phrase in command.lower():
            try:
                topic = command.lower()
                for p in trigger_phrases:
                    topic = topic.replace(p, "")
                topic = topic.strip()
                summary = wikipedia.summary(topic, sentences=2)
                speak(summary)
            except wikipedia.exceptions.DisambiguationError:
                speak(f"There are multiple meanings of {topic}. Can you be more specific?")
            except wikipedia.exceptions.PageError:
                speak(f"I couldn't find the meaning of {topic}.")
            return True
    return False


def set_timer(command):
    pattern = r"timer for (\d+)\s*(seconds|second|minutes|minute)"
    match = re.search(pattern, command.lower())
    if match:
        value = int(match.group(1))
        unit = match.group(2)

        seconds = value if "second" in unit else value * 60
        speak(f"Timer set for {value} {unit}")
        time.sleep(seconds)
        speak(f"Time's up! Your {value} {unit} timer has finished.")
    else:
        speak("Sorry, I couldn't understand the timer duration.")


def tell_about_person(command):
    name = command.replace("tell me about", "").replace("who is", "").strip()
    try:
        summary = wikipedia.summary(name, sentences=2)
        speak(summary)
    except wikipedia.exceptions.DisambiguationError:
        speak(f"There are multiple people named {name}. Please be more specific.")
    except wikipedia.exceptions.PageError:
        speak(f"I couldn't find any information about {name}.")
