# textbase/backend.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from textbase.message import Message
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware
import sys
import logging
from typing import List
import importlib

logging.basicConfig(level=logging.INFO)

load_dotenv()

from .message import Message

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:4000",
    "http://localhost:5173",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chat_states = {"service": None, "display_menu": True, "valid_options": ["1","2","3"], "services": ["Talking Bot", "Book Recommendation","Personal Health Assistant"]}

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    The `read_root` function reads and returns the contents of an HTML file specified by the path
    "textbase/frontend/index.html".
    :return: The content of the "index.html" file located in the "textbase/frontend" directory is being
    returned.
    """
    with open("textbase/frontend/dist/index.html") as f:
        return f.read()


def get_module_from_file_path(file_path: str):
    """
    The function `get_module_from_file_path` takes a file path as input, loads the module from the file,
    and returns the module.

    :param file_path: The file path is the path to the Python file that you want to import as a module.
    It should be a string representing the absolute or relative path to the file
    :type file_path: str
    :return: the module that is loaded from the given file path.
    """
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@app.post("/chat", response_model=dict)
async def chat(messages: List[Message], state: dict = None):
    """
    The above function is a Python API endpoint that receives a list of messages and a state dictionary,
    loads a module from a file path, calls the on_message function from the module with the messages and
    state, and returns the bot messages generated by the module.

    :param messages: The `messages` parameter is a list of `Message` objects. It represents the messages
    exchanged between the user and the chatbot. Each `Message` object typically contains information
    such as the text of the message, the sender, the timestamp, etc
    :type messages: List[Message]
    :param state: The `state` parameter is a dictionary that stores the state of the conversation. It
    can be used to store information or context that needs to be maintained across multiple requests or
    messages in the conversation. The `state` parameter is optional and can be set to `None` if not
    needed
    :type state: dict
    :return: a list of `Message` objects.
    """

    global chat_states

    file_path = os.environ.get("FILE_PATH", None)
    logging.info(file_path)
    if not file_path:
        return []

    module = get_module_from_file_path(file_path)

    print("here", state)
    menu = ""
    for i in range(len(chat_states["services"])):
        menu += str(i+1)+"."+chat_states["services"][i]+" "
    menu += " .You can always exit from a service by entering 'EXIT'"
    if chat_states["display_menu"]:
        chat_states["display_menu"] = False
        display_menu = "🌟 Whether you're looking for a book recommendation, want to discuss your health goals, or simply need a friendly chat, I'm here to assist! Just let me know what you'd like to talk about, and we'll dive into an amazing conversation together!!. Select from " + menu 
        return {
            "botResponse": {
                "content": display_menu,
                "role": "assistant"
            }
        }
    else:
        service_opted = messages[-1].content.strip()
        if chat_states["service"] is None and not chat_states["display_menu"]:
            if service_opted in chat_states["valid_options"]:
                chat_states["service"] = service_opted
            else:
                invalid_message = "Please select from"+ menu
                return {
                    "botResponse": {
                        "content": invalid_message,
                        "role": "assistant"
                    }
                }
        elif service_opted.lower() == "exit":
            service_name = chat_states["services"][int(chat_states["service"])-1]
            menu = "You have exited from service "+ service_name +". " +" Select from "+menu+" to continue"
            chat_states["service"] = None
            return {
            "botResponse": {
                "content": menu,
                "role": "assistant"
            }
        }
        
    # Call the on_message function from the dynamically loaded module
    response = module.on_message(messages, chat_states["services"][int(chat_states["service"])-1], state)
    if type(response) is tuple:
        bot_response, new_state = response
        return {
            "botResponse": {"content": bot_response, "role": "assistant"},
            "newState": new_state,
        }
    elif type(response) is str:
        return {"botResponse": {"content": response, "role": "assistant"}}


# Mount the static directory (frontend files)
app.mount(
    "/assets",
    StaticFiles(directory="textbase/frontend/dist/assets", html=True),
    name="static",
)