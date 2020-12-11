from typing import *


class Decoder:
    def __init__(self, pc: int, rom: bytes):
        # current pc
        self.pc: int = pc
        # pc of the first byte
        self.pc0: int = pc
        # rom data
        self.rom: bytes = rom
        # all bytes popped by this context
        self.bytes: bytes = b''
        # opcode accumulator
        self.opcode: bytes = b''
        # flag if true, then the program executes the instruction after this instruction
        # if false, then a jump was made and the following bytes may not be executable
        self.continues: bool = True
        # set of all jumps that this instruction does
        self.jumps: Set[int] = set()
        # Human readable disassembly
        self.human_readable: str = None

    def __repr__(self) -> str:
        return self.human_readable

    def pop_bytes(self, n: int = 1) -> bytes:
        ' Pop n bytes and increase the program counter. '
        if self.pc + n > len(self.rom):
            raise ValueError(f'Program counter is at end of rom: {self.pc + n} of {len(self.rom)}')
        data = self.rom[self.pc:self.pc+n]
        self.bytes += data
        self.pc += n
        return data

    def pop(self, size: int = 1, signed: bool = False, byteorder='little') -> int:
        ' Pop size bytes and convert them to an integer. '
        data = self.pop_bytes(size)
        return int.from_bytes(data, byteorder=byteorder, signed=signed)

    def jump(self, address: int = None, offset: int = 0, returns: bool = False, conditional: bool = False):
        if address is None:
            address = self.pc
        address += offset
        self.jumps.add(address)
        if returns:
            # function
            # Continue even if not conditional
            self.continues = True
        else:
            # label
            # Continue if conditional
            self.continues = conditional
        return address

    def ret(self, arg):
        self.continues = False
        return arg

    def halt(self, arg):
        self.continues = False
        return arg

__all__ = ['Decoder']
