from typing import Dict, Set, NewType, Callable, Union
from io import StringIO
from pathlib import Path
from sys import stderr
import itertools

from .decoder import Decoder

DecodeAction = NewType('DecodeAction', Callable[[Decoder], str])

class Disassembler:
    def __init__(self, rom: bytes):
        self.rom = rom
        self.pcs: Set[int] = set()
        self.disassembly: Dict[int, Decoder] = dict()
        self._instruction_decoder: Dict[bytes, DecodeAction] = dict()
        self.initialize_instructions()

    def save(self, fd, format_string: str = '0x{address:04x}: ({bytes:8}) ({opcode:5}) {disassembly}\n', data_format: str = '0x{address:4x}: .db {byte:x}\n'):
        address = 0
        to_hex = lambda x: format(x, 'x')
        while address < len(self.rom):
            if address in self.disassembly:
                disassembly = self.disassembly[address]
                fd.write(format_string.format(address=address, opcode=' '.join(map(to_hex, disassembly.opcode)), bytes=' '.join(map(to_hex, disassembly.bytes)), disassembly=disassembly))
                address += len(disassembly.bytes)
            else:
                fd.write(data_format.format(address=address, byte=self.rom[address]))
                address += 1

    def initialize_instructions(self):
        ' This should be overwritten by the user to initialize all actions. '
        raise NotImplementedError()

    def add_instruction(self, opcode: Union[bytes, str, int], action: DecodeAction = None):
        if isinstance(opcode, int):
            opcode = format(opcode, '08x')
        if isinstance(opcode, str):
            opcode = bytes.fromhex(opcode).lstrip(b'\x00')
            if opcode == b'':
                opcode = b'\x00'
        if opcode in self._instruction_decoder:
            raise ValueError('Instruction already added: %s' % opcode)
        if action is None:
            self._instruction_decoder[opcode] = _need_more_bytes
        else:
            self._instruction_decoder[opcode] = action

    def add_instruction_range(self, start: int, end: int, action: DecodeAction = None, step: int = 1):
        for i in range(start, end, step):
            self.add_instruction(i, action)

    def disassemble(self, pc: int):
        self.pcs.add(pc)
        while self.pcs:
            pc = self.pcs.pop()
            if pc in self.disassembly:
                continue
            # Create context
            decoder: Decoder = Decoder(pc, self.rom)
            try:
                while True:
                    # Accumulate opcode
                    decoder.opcode += decoder.pop_bytes()
                    # Get the action for this opcode
                    action = self._instruction_decoder.get(decoder.opcode, _unknown_opcode)
                    try:
                        # Apply action
                        if isinstance(action, str):
                            decoder.human_readable = action
                        else:
                            decoder.human_readable = action(decoder)
                    except NeedMoreBytesDecodeActionException:
                        # Increase pc in case the action requests so
                        continue
                    # If no exception was raised, stop accumulating the opcode
                    break
                self.disassembly[pc] = decoder
            except UnknownOpcodeException as err:
                print(hex(pc), 'opcode', decoder.opcode, 'bytes', decoder.bytes)
            if decoder.continues:
                self.pcs.add(decoder.pc)
            self.pcs.update(decoder.jumps)


class NeedMoreBytesDecodeActionException(Exception):
    pass


def _need_more_bytes(*args, **kwargs):
    raise NeedMoreBytesDecodeActionException()


class UnknownOpcodeException(Exception):
    pass


def _unknown_opcode(*args, **kwargs):
    raise UnknownOpcodeException()

__all__ = ['Disassembler', 'UnknownOpcodeException', 'NeedMoreBytesDecodeActionException', 'MoreDecodeAction']
