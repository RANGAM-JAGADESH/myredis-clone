import json
import os

FILE_NAME = "dump.json"


def save_data(data):
    with open(FILE_NAME, "w") as file:
        json.dump(data, file)


def load_data():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as file:
            return json.load(file)

    return {}