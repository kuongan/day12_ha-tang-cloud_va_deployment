"""
Mock LLM responses for local development and labs.
"""
import random
import time

RESPONSES = {
    "default": [
        "Day 12 production agent is running correctly.",
        "Your request was processed successfully by the AI service.",
        "This is a mock response. Replace with real LLM provider in production.",
    ],
    "docker": ["Docker packages app and dependencies into consistent runtime units."],
    "redis": ["Redis stores shared state so multiple app instances remain stateless."],
    "deploy": ["Deployment moves tested code into a reliable production environment."],
}


def ask(question: str, delay: float = 0.05) -> str:
    time.sleep(delay + random.uniform(0, 0.05))
    lower = question.lower()
    for keyword, values in RESPONSES.items():
        if keyword in lower:
            return random.choice(values)
    return random.choice(RESPONSES["default"])


def ask_stream(question: str):
    response = ask(question, delay=0.0)
    for token in response.split():
        time.sleep(0.03)
        yield token + " "
