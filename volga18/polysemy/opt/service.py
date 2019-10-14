#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import logging
import binascii
import socket
import socketserver
from polysemy.utils import InputOverflowException, InputUnderflowException
from polysemy.utils import read_message, send_message, unpack_message, pack_message
from polysemy.cpkc import CryptoOperations, CryptoException, int_to_str, str_to_int
from polysemy.db_driver import DBDriver


logger = None
db_object = None


class PolysemyTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        socketserver.TCPServer.server_bind(self)


class PolysemyServerHandler(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        socketserver.BaseRequestHandler.__init__(self, request, client_address, server)

    def handle(self):
        logger.info('[%s] Accepted connection', self.client_address[0])
        try:
            packed_msg = read_message(self.request)
            logger.debug('Accepted message from {0}'.format(self.client_address[0]))

            # unpack the message
            unpacked_msg = unpack_message(packed_msg)
            logger.debug('Command {0} from {1}'.format(unpacked_msg['cmd'], self.client_address[0]))

            # process the command
            if unpacked_msg['cmd'] == 'push':
                message1 = binascii.hexlify(unpacked_msg['message1'])
                message2 = binascii.hexlify(unpacked_msg['message2'])
                bs = unpacked_msg['bs']
                rec_id = unpacked_msg['id']

                crypto_object = CryptoOperations.create_keypair(bit_length=8*(2*bs+1))
                h, q = crypto_object.public_key
                f, g, g2, _ = crypto_object.private_key2

                e_parts = []
                for i in range(0, len(message1), 2*bs):
                    m1 = str_to_int(message1[i:i+2*bs])
                    m2 = str_to_int(message2[i:i+2*bs])
                    e = crypto_object.encrypt(m1, m2)
                    e_parts.append(int_to_str(e))

                e_str = ':'.join(e_parts)
                h_str, q_str = int_to_str(h), int_to_str(q)
                f_str, g_str, g2_str = int_to_str(f), int_to_str(g), int_to_str(g2)
                db_object.insert_new_entry(rec_id, e_str, h_str, q_str, f_str, g_str, g2_str)

                msg = {'e': e_str, 'h': h_str, 'q': q_str, 'f': f_str, 'g': g_str, 'g2': g2_str}
                packed_msg = pack_message(msg)
                send_message(self.request, packed_msg)

            elif unpacked_msg['cmd'] == 'pull':
                rec_id = unpacked_msg['id']
                rec_id, e, h, q, f, g, g2 = db_object.select_by_id(rec_id)

                msg = {'e': e, 'h': h, 'q': q}
                packed_msg = pack_message(msg)
                send_message(self.request, packed_msg)

            else:
                logger.debug('Unknown command {0} from {1}'.format(unpacked_msg['cmd'], self.client_address[0]))
                send_message(self.request, pack_message(0))

        except CryptoException as ex:
            logger.error(ex)

        except (InputOverflowException, InputUnderflowException) as ex:
            logger.error(ex)

        except Exception as ex:
            logger.error(str(ex), exc_info=True)

        finally:
            logger.info('Processed connection from {0}'.format(self.client_address[0]))


"""
    Main
"""

if __name__ == '__main__':
    # parse input arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=str, default='service.db', help='path to the database file')
    parser.add_argument('--address', type=str, default='0.0.0.0', help='address')
    parser.add_argument('-p', type=int, default=8888, help='port')
    parser.add_argument('-v', action='store_true', default=False, help='be verbose')
    args = parser.parse_args()

    # initialize logging
    logging_level = logging.DEBUG if args.v else logging.INFO
    logging.basicConfig(level=logging_level,
                        format='[%(asctime)s %(levelname)s]: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger(__name__)

    # create database
    db_object = DBDriver(args.database)
    db_object.open_db()

    # serve
    server = PolysemyTCPServer((args.address, args.p), PolysemyServerHandler)
    logger.info('Serving indefinitely at {0}:{1}'.format(args.address, args.p))
    server.serve_forever()
