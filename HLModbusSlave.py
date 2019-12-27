# coding:utf-8
from threading import Thread
from queue import Queue
from enum import Enum, auto
from time import sleep
from typing import Callable, List, Any
from HLModbusMaster import ModbusCheckCalc


class ModbusRegister:
    def __init__(self,
                 start: int = 0,
                 length: int = 0,
                 reg: List[int] = None,
                 dev: Any = None,
                 read: Callable[[List[int], Any], None] = None,
                 write: Callable[[List[int], Any], None] = None):
        self.start, self.length = start, length
        self.reg, self.dev = reg, dev
        self.read, self.write = read, write


class ModbusSlave:
    def __init__(self, address: int, regs: List[ModbusRegister], sender: Callable[[bytes], None]):
        self.regs = regs
        self.address = address
        self.send = sender

    @staticmethod
    def frame_valid(data: bytes):
        if len(data) < 4:
            return False
        check = (data[-2] << 8) + data[-1]
        return check == ModbusCheckCalc(data, len(data) - 2)

    def read_registers(self, addr: int, sz: int):
        """
        0x03 function
        :return: True/False, Value
        """
        for reg in self.regs:
            if reg.start <= addr < reg.start + reg.length:
                if reg.read:
                    reg.read(reg.reg, reg.dev)
                    offset = addr - reg.start
                    return True, reg.reg[offset: offset + sz]

    def write_register(self, addr: int, value: int):
        """
        0x06 function
        :return: True/False, Value
        """
        for reg in self.regs:
            if reg.start <= addr < reg.start + reg.length:
                if reg.write:
                    reg.reg[addr - reg.start] = value
                    reg.write(reg.reg, reg.dev)
                    return True, 0

    def write_registers(self, addr: int, sz: int, data: bytes):
        """
        0x10 function
        the [addr, addr+sz) should in the range of a ModbusRegister
        :return: True/False, Value
        """
        for reg in self.regs:
            if reg.start <= addr and addr + sz < reg.start + reg.length:
                if reg.write:
                    reg.reg[addr - reg.start:] = data[:]
                    reg.write(reg.reg, reg.dev)
                    return True, 0

    def deal(self, data: bytes):
        if data[0] != 0x00 and data[0] != self.address:
            return False
        if data[1] == 0x03:
            self.read_registers(data[2] * 256 + data[3], data[4] * 256 + data[5])

    def receive(self, data: bytes):
        """
        call this while received data
        :param data: bytes
        """
        pass

    def receive_ascii(self, data: str):
        """
        modbus ascii protocol
        :return: True/False, Value
        """
        if not data.startswith(":") or not data.endswith("\r\n") or len(data) % 2 == 0:
            return False
        mdata = bytearray.fromhex(data[1:-2])
        if sum(mdata) % 0x100 != 0:
            return False
        self.deal(mdata[:-1])


def rd(a, b):
    print(f"read {a} {b}")


def wt(a, b):
    print(f"write {a} {b}")


def s(n):
    print(n)


r = [1, 2, 3]
d = [4, 5, 6]


def test():
    regs = [ModbusRegister(0, 4, r, d, rd, wt)]
    a = ModbusSlave(1, regs, s)
    a.read_registers(1, 1)
    a.write_registers(1, 2, [5, 6])
    a.receive_ascii(":010300000001FB\r\n")


if __name__ == '__main__':
    test()
