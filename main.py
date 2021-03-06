#!/usr/bin/env python3

import json
import requests
import websocket


class TinychatClient(object):
    def __init__(self, room, nickname, account=None, password=None):
        self._room = room
        self._nickname = nickname
        self._account = account
        self._password = password

        self._ws = None
        self._req = 1
        self._users = {}

    def connect_room(self):
        """
        Connect to a room.
        """
        self._req = 1
        # This packet's structure MUST not be changed.
        self.send_msg({
            'tc': 'join',
            'useragent': 'tinychat-client-webrtc-chrome_win32-2.0.9-255',
            'token': self.get_token(),
            'room': self._room,
            'nick': self._nickname
        })

    def connect_socket(self):
        """
        Connect to the Tinychat websocket.
        """
        self._ws = websocket.WebSocket()

        header = [
            'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3040.0 Safari/537.36',
            'Accept-Language: en-US,en;q=0.8',
            'Accept-Encoding: gzip, deflate, sdch, br',
            'Sec-WebSocket-Extensions: permessage-deflate; client_max_window_bits'
        ]

        # This connect function's arguments MUST not be changed.
        self._ws.connect(
            "wss://wss.tinychat.com",
            header=header,
            host="wss.tinychat.com",
            origin="https://tinychat.com",
            subprotocols=["tc"]
        )

    def get_token(self):
        """
        Request a token from a Tinychat room.
        
        :return: Room token.
        :rtype: str
        """
        print('Making token request.')
        r = requests.get('https://tinychat.com/api/v1.0/room/token/{0}'.format(self._room))
        result = r.json()
        token = result['result']
        
        return token

    def mainloop(self):
        """
        Main receive/respond loop.
        """
        while True:
            msg = json.loads(self._ws.next())
            self.on_msg(msg)
    
    def on_join(self, msg):
        """
        Handles join messages from the server.
        
        :param msg: The message object.
        :type msg: dict
        """
        user_info = msg.copy()
        del user_info['tc']
        user_handle = user_info.pop('handle', None)
        self._users[user_handle] = user_info
        print([self._users[handle]['nick'] for handle in self._users])
    
    def on_msg(self, msg):
        """
        Main message handler.
        
        :param msg: The message object.
        :type msg: dict
        """
        print(msg)
        msg_type = msg['tc']
        if msg_type == 'join':
            self.on_join(msg)
        elif msg_type == 'nick':
            self.on_nick(msg)
        elif msg_type == 'ping':
            self.on_ping()
        elif msg_type == 'quit':
            self.on_quit(msg)
        elif msg_type == 'userlist':
            self.on_userlist(msg)

    def on_nick(self, msg):
        """
        Handles nick messages from the server.

        :param msg: The message object.
        :type msg: dict
        """
        user_handle = msg['handle']
        new_nick = msg['nick']
        self._users[user_handle]['nick'] = new_nick
        print([self._users[handle]['nick'] for handle in self._users])

    def on_ping(self):
        """
        Handles ping messages from the server.

        :param msg: The message object.
        :type msg: dict
        """
        self.send_msg({'tc': 'pong'})
    
    def on_quit(self, msg):
        """
        Handles quit messages from the server.

        :param msg: The message object.
        :type msg: dict
        """
        user_handle = msg['handle']
        del self._users[user_handle]
        print([self._users[handle]['nick'] for handle in self._users])

    def on_userlist(self, msg):
        """
        Handles userlist messages from the server.

        :param msg: The message object.
        :type msg: dict
        """
        for user in msg['users']:
            user_info = user.copy()
            user_handle = user_info.pop('handle', None)
            self._users[user_handle] = user_info
        print([self._users[handle]['nick'] for handle in self._users])
        
    def send_msg(self, msg):
        """
        Sends a json message to the Tinychat server.

        :param msg: The object to send. Must be serializable to json.
        :type msg: dict | object
        """
        msg['req'] = self._req
        self._ws.send(json.dumps(msg))

        self._req += 1


if __name__ == "__main__":
    room = input("What room? ")
    nickname = input("What is your nickname? ")

    client = TinychatClient(room, nickname)

    client.connect_socket()
    client.connect_room()
    client.mainloop()
