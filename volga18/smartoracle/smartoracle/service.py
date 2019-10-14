#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import rand
import argparse
import logging
import socket
import hashlib
import SocketServer
from utils import *
from eclib import *


"""
    Parameters and globals
"""

logger = None


"""
    Service connection handler
"""

class ForkingTCPServer(SocketServer.ForkingTCPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        SocketServer.TCPServer.server_bind(self)


class ServiceServerHandler(SocketServer.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)

    def handle(self):
        logger.info('[%s] Accepted connection', self.client_address[0])
        try:
            # handle commands
            while True:
                cmd = read_message(self.request)
                logger.info('[%s] Accepted command: %s', self.client_address[0], cmd)

                if cmd == 'PUSH':
                    logger.info('[%s] PUSH: Executing', self.client_address[0])
                    message = read_message(self.request)
                    curve_name, passphrase = message.split(':')
                    curve = curve_by_name(curve_name)
                    x = str_to_int(passphrase)
                    point = x * curve.g
                    r = rand.randint(1, curve.n)
                    point = r * point
                    s = point.compress()
                    send_message(self.request, s)

                    # close connection
                    send_message(self.request, b'+')

                elif cmd == 'EXIT':
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
    # parse cmd args
    #parser = argparse.ArgumentParser()
    #parser.add_argument('-a', type=str, default='0.0.0.0', help='Address, default is 0.0.0.0')
    #parser.add_argument('-p', type=int, default=8888, help='Port number, default is 8888')
    #parser.add_argument('-log', type=str, default=None, help='Path to log file, default is to output to stdout only')
    #args = parser.parse_args()

    # initialize logging
    logging.basicConfig(format='%(asctime)s [%(levelname)-5.5s]  %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.DEBUG)
    logger = logging.getLogger('service')
    #if args.log:
        #log_formatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
        #file_handler = logging.FileHandler(args.log)
        #file_handler.setFormatter(log_formatter)
        #file_handler.setLevel(logging.DEBUG)
        #logger.addHandler(file_handler)

    # initialize and spawn the server
    server = ForkingTCPServer(('0.0.0.0',  8777), ServiceServerHandler)
    server.serve_forever()