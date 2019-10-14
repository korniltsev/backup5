# -*- coding: utf-8 -*-
import struct


"""
    Communication
"""

class InputOverflowException(Exception):
    pass


class InputUnderflowException(Exception):
    pass


def read_message(s, max_input_length=4196):
    received_buffer = s.recv(8)
    if len(received_buffer) < 8:
        raise InputUnderflowException('Failed to receive data: the received length is less than 8 bytes long')
    to_receive = struct.unpack('<Q', received_buffer[0:8])[0]
    if to_receive > max_input_length:
        raise InputOverflowException('Failed to receive data: requested to accept too much data')
    received_buffer = ''

    while len(received_buffer) < to_receive:
        data = s.recv(to_receive - len(received_buffer))
        if len(data) == 0:
            raise InputUnderflowException('Failed to receive data: the pipe must have been broken')
        received_buffer += data
        if len(received_buffer) > max_input_length:
            raise InputOverflowException('Failed to receive data: accepted too much data')

    return received_buffer


def send_message(s, message):
    send_buffer = struct.pack('<Q', len(message)) + message
    s.sendall(send_buffer)