# -*- coding: utf-8 -*-
import logging
import struct
import sqlite3


logger = logging.getLogger('service')


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
    received_buffer = b''

    while len(received_buffer) < to_receive:
        data = s.recv(to_receive - len(received_buffer))
        if len(data) == 0:
            raise InputUnderflowException('Failed to receive data: the pipe must have been broken')
        received_buffer += data
        if len(received_buffer) > max_input_length:
            raise InputOverflowException('Failed to receive data: accepted too much data')

    return received_buffer


def send_message(s, message: bytes):
    send_buffer = struct.pack('<Q', len(message)) + message
    s.sendall(send_buffer)


"""
    Database
"""


def create_database(db_file_path: str):
    conn = sqlite3.connect(db_file_path)
    with conn:
        try:
            cursor = conn.cursor()
            cursor.execute('CREATE TABLE data (id TEXT UNIQUE, c TEXT)')
        except sqlite3.OperationalError as ex:
            logger.error('Failed to create table: %s', ex)
    conn.close()


def save_data(db_file_path: str, data_id: str, c: bytes):
    conn = sqlite3.connect(db_file_path)
    try:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO data VALUES (?,?)', (data_id, c))
        conn.commit()
    finally:
        conn.close()


def retrieve_data(db_file_path: str, data_id: str) -> bytes:
    conn = sqlite3.connect(db_file_path)
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM data WHERE id=?', (data_id, ))
        row = cursor.fetchone()
        _, c = row
        return c
    finally:
        conn.close()
