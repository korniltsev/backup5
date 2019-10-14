#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def parse(expr: bytes) -> list:
    # takes expressions like '1*3+12+7'
    additions = expr.split(b'+')
    products = []
    for i in additions:
        products.append(list(map(int, i.split(b'*'))))

    return products


class Register:
    def __init__(self, key: list, output_f: bytes):
        self.register = key
        self.branches = [64, 62, 61, 59, 52, 51, 49, 48, 45, 44, 39, 38, 37, 35,
                         32, 30, 27, 26, 23, 18, 14, 12, 11, 9, 7, 6, 3, 1]
        self.output_function = parse(output_f)

    @staticmethod
    def _clock_r(register: list, branches: list) -> list:
        new = 0
        for i in branches:
            new ^= register[i - 1]
        register = [new] + register[:-1]

        return register

    def next_bit(self) -> int:
        # get next bit
        additions = []
        for it in self.output_function:
            if len(it) > 1:
                tmp = 1
                for j in it:
                    tmp *= self.register[j]
                additions.append(tmp)
            else:
                additions.append(self.register[it[0]])
        res = 0
        for i in additions:
            res ^= i

        # clock register
        self.register = self._clock_r(self.register, self.branches)

        return res


class Cipher:
    def __init__(self, key: bytes, func: bytes, num_rounds: int):
        key = int.from_bytes(key, 'big')
        bin_key = bin(key)[2:].zfill(64)
        self.key = list(map(int, bin_key))
        self.func = func
        self.num_rounds = num_rounds

    def f(self, input_block: bytes) -> int:
        register = Register(self.key, self.func)
        key_int = 0
        for _ in range(64):
            key_int = key_int * 2 + register.next_bit()
        output_block = int.from_bytes(input_block, 'big') ^ key_int
        return output_block

    def feistel(self, left: bytes, right: bytes, mode: str) -> tuple:
        if mode == 'e':
            x = self.f(right)
            right1 = int.from_bytes(left, 'big') ^ x
            left1 = right
            return left1, right1.to_bytes(8, 'big')
        elif mode == 'd':
            x = self.f(left)
            left1 = int.from_bytes(right, 'big') ^ x
            right1 = left
            return left1.to_bytes(8, 'big'), right1

        return b'', b''

    def encrypt(self, plaintext: bytes) -> bytes:
        left_block = plaintext[:8]
        right_block = plaintext[8:]
        for _ in range(self.num_rounds):
            left_block, right_block = self.feistel(left_block, right_block, 'e')
            self.key = self.key[-1:] + self.key[:-1]
        return left_block + right_block

    def decrypt(self, ciphertext: bytes) -> bytes:
        left_block = ciphertext[:8]
        right_block = ciphertext[8:]
        for _ in range(self.num_rounds - 1):
            self.key = self.key[-1:] + self.key[:-1]
        for _ in range(self.num_rounds):
            left_block, right_block = self.feistel(left_block, right_block, 'd')
            self.key = self.key[1:] + self.key[:1]
        return left_block + right_block


if __name__ == '__main__':
    cipher_key = b'\x07' * 4 + b'\x77' * 4
    capsule = b'VolgaCTF{eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiJ9.eyJmbGFnIjoiYjkyM2JhMjdmYzhiZDU3OWM0NzQzMzBlZTBjMDkwOGUifQ.1sgtPeFnwvk_Ojij1Bg3IshDY-vsb00dL_rNUr5Hze_BUrw26LMuUNqawSZHupZfO7MSLqXpJkaJs5QbZ7StnA}'
    func = b'0+34+45'
    num_rounds = 2

    ciphertext = b''
    for block in range(0, len(capsule), 16):
        cipher = Cipher(cipher_key, func, num_rounds)
        ciphertext += cipher.encrypt(capsule[block:block + 16])

    recv_capsule = b''
    for block in range(0, len(ciphertext), 16):
        cipher = Cipher(cipher_key, func, num_rounds)
        recv_capsule += cipher.decrypt(ciphertext[block:block + 16])

    assert capsule == recv_capsule

