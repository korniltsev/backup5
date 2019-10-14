#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import jwt
import time
import hashlib
import socket
import socketserver
from utils import *
from cipher import Cipher


"""
    Parameters and globals
"""


logger = None
func = b'0+34+45'
num_rounds = 2


class SignatureFailure(Exception):
    pass


"""
    Service connection handler
"""


class ForkingTCPServer(socketserver.ForkingTCPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        socketserver.TCPServer.server_bind(self)


class ServiceServerHandler(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        socketserver.BaseRequestHandler.__init__(self, request, client_address, server)

    def handle(self):
        logger.info('[%s] Accepted connection', self.client_address[0])
        try:
            # handle commands
            while True:
                cmd = read_message(self.request)
                logger.info('[%s] Accepted command: %s', self.client_address[0], cmd)

                if cmd == b'PUSH':
                    logger.info('[%s] PUSH: Executing', self.client_address[0])

                    capsule = read_message(self.request)
                    data_id = read_message(self.request)
                    signature = read_message(self.request)

                    with open('ec_public.pem', 'rb') as jwtkey:
                        key = jwtkey.read()
                    if jwt.decode(signature, key, algorithms='ES256')['message'] != 'It\'s me, Mario!':
                        raise SignatureFailure

                    key = read_message(self.request)
                    ciphertext = b''
                    for block in range(0, len(capsule), 16):
                        cipher = Cipher(key, func, num_rounds)
                        ciphertext += cipher.encrypt(capsule[block:block + 16])

                    save_data('storage.db', data_id, ciphertext)

                    # close connection
                    send_message(self.request, b'+')

                elif cmd == b'PULL':
                    logger.info('[%s] PULL: Executing', self.client_address[0])

                    data_id = read_message(self.request)
                    ciphertext = retrieve_data('storage.db', data_id)
                    send_message(self.request, ciphertext)
                    send_message(self.request, func)
                    send_message(self.request, num_rounds.to_bytes(4, 'big'))

                    # close connection
                    send_message(self.request, b'+')

                elif cmd == b'EXIT':
                    send_message(self.request, b'+')
                    break

                else:
                    raise Exception('[%s] Failed to process command: command %s is unknown', self.client_address[0], cmd)

        except Exception as ex:
            logger.error(str(ex), exc_info=True)

        finally:
            logger.info('[%s] Processed connection', self.client_address[0])


"""
    main
"""

if __name__ == '__main__':
    # initialize logging
    logging.basicConfig(format='%(asctime)s [%(levelname)-5.5s]  %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.DEBUG)
    logger = logging.getLogger('service')

    # initialize and spawn the server
    create_database('storage.db')
    server = ForkingTCPServer(('0.0.0.0',  8777), ServiceServerHandler)
    server.serve_forever()
