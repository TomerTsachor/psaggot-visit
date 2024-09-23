import json
from typing import Dict

from flask import Flask, request, make_response

app = Flask(__name__)


def add_user(name: str, username: str, password: str) -> None:
    with open('../resources/users.json', 'r') as f:
        users = json.load(f)

    new_user = {
        name: {
            'username': username,
            'password': password
        }
    }

    users.update(new_user)

    with open('../resources/users.json', 'w') as f:
        json.dump(users, f)


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    name, username, password = data['name'], data['username'], data['password']
    add_user(name, username, password)

    return make_response(f'User \'{name}\' registered successfully', 200)


if __name__ == '__main__':
    app.run(port=1234)
