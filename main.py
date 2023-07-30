import textbase
from textbase.message import Message
from textbase import models
import os
from typing import List
from question_data import questions_dict

# Load your OpenAI API key
models.OpenAI.api_key = "<--INSERT YOUR OPEN API KEY-->"
# or from environment variable:
# models.OpenAI.api_key = os.getenv("OPENAI_API_KEY")

@textbase.chatbot("talking-bot")
def on_message(message_history: List[Message], service_name: str, state: dict = None):
    """Your chatbot logic here
    message_history: List of user messages
    service_name: The name of the service, e.g., "Talking Bot", "Book Recommendation", "Personal Health Assistant"
    state: A dictionary to store any stateful information

    Return a string with the bot_response or a tuple of (bot_response: str, new_state: dict)
    """

    try:
        if state is None:
            state = {
                "counter": 0,
                "service_name": service_name,
                "questions": questions_dict[service_name][2:],  # Exclude the initial system prompt from questions
                "answers": []
            }

        loop_length = len(state["questions"])
        if state["counter"] < loop_length:
            question = state["questions"][state["counter"]]
            if state["counter"] == 0:
                state["counter"] += 1
                return questions_dict[service_name][1] + " " + question, state
            state["counter"] += 1
            return question, state

        # Get the initial system prompt based on the service_name
        SYSTEM_PROMPT = questions_dict[state["service_name"]][0]

        # Generate GPT-3.5 Turbo response
        bot_response = models.OpenAI.generate(
            system_prompt=SYSTEM_PROMPT,
            message_history=message_history,
            model="gpt-3.5-turbo",
            max_tokens=200  # Increase max_tokens to accommodate the entire response
        )



        # Update the questions list in state to an empty list to prevent repetition
        state["questions"] = []
        state["counter"] = 0
        state["answers"] = []
        return bot_response, state

    except Exception as e:
        # Handle exceptions and errors gracefully
        error_message = "An error occurred: {}".format(str(e))
        return error_message, state
