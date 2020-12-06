from typing import Dict, Set, NewType, Callable, Union
from io import StringIO
from pathlib import Path
from sys import stderr

from .context import Context
from .disassembly import Disassembly

Address = NewType('Address', int)
DecodeAction = NewType('DecodeAction', Union[Callable[[Context], Disassembly], str])
MoreDecodeAction = object()

class Disassembler:
    def __init__(self, data: bytes):
        self.data = data
        self.pcs: Set[Address] = set()
        self.disassembly: Dict[Address, Disassembly] = dict()
        self._instruction_decoder: Dict[bytes, DecodeAction] = dict()
        self.initialize_instructions()
        self.functions: Dict[Address, str] = dict()
        self.labels: Dict[Address, str] = dict()
        self.references: Dict[Address, str] = dict()

    def get_adr_name(self, adr: Address):
        name = None
        if adr in self.functions:
            name = self.functions.get(adr) or f'function{hex(adr)}'
        if adr in self.labels:
            name = self.labels.get(adr) or f'.label{hex(adr)}'
        if adr in self.references:
            name = self.references.get(adr) or f'reference{hex(adr)}'
        if name is None:
            return '\t'
        return f'\n{name}:\n\t'

    def save(self, path_or_stream: Union[Path, StringIO], outformat: str = '{adr:08x}: ({bytes:>8}) {dis}\n'):
        ' Dump the disassembly into a single file. '
        lines = (self.get_adr_name(adr) + outformat.format(adr=adr, bytes=dis.bytes.hex(), dis=dis.format(self.functions, self.labels, self.references)) for adr, dis in sorted(self.disassembly.items()))
        if isinstance(path_or_stream, Path):
            with open(path_or_stream, 'w') as fd:
                fd.writelines(lines)
        else:
            path_or_stream.writelines(lines)

    def initialize_instructions(self):
        ' This should be overwritten by the user to initialize all actions. '
        raise NotImplementedError()

    def add_instruction(self, opcode: Union[bytes, str, int], action: DecodeAction = MoreDecodeAction):
        ''' Add an action that should be done if the opcode is decoded.

        Parameter:
            opcode: Representation for the instruction's opcode as either an integer, hex string without 0x prefix or the bytes directly.
            action: An action that generates a disassembly from opcode and some context.

        Returns:
            Function that takes the context and returns a disassembly,
            or a string with the human readable disassembly, in case the instruction
            can be directly disassembled without using extra bytes or adding labels/jumps/functions/variables.
        '''
        if isinstance(opcode, int):
            opcode = format(opcode, '08x')
        if isinstance(opcode, str):
            opcode = bytes.fromhex(opcode).lstrip(b'\x00')
            if opcode == b'':
                opcode = b'\x00'
        if opcode in self._instruction_decoder:
            raise ValueError('Instruction already added: %s' % opcode)
        if action == MoreDecodeAction:
            self._instruction_decoder[opcode] = _need_more_bytes
        else:
            self._instruction_decoder[opcode] = action

    def add_instruction_range(self, start: Address, end: Address, action: DecodeAction = MoreDecodeAction, step: Address = 1):
        ''' Adds the given action to every opcodec between and including @start, excluding @end with a step size of @step.

        Parameters:
            start: Inclusive start opcode of the range.
            end: Exclusive end opcode of the range.
            action: The action to be performed on each of these opcodes.
            step: range stepsize
        '''
        for i in range(start, end, step):
            self.add_instruction(i, action)

    def disassemble(self, pc: Address):
        ' Starts the decoding at the given initial program counter. '
        self.pcs.add(pc)
        self.functions[pc] = 'Main'
        while self.pcs:
            pc = self.pcs.pop()
            if pc in self.disassembly:
                continue
            # Create context
            context: Context = Context(pc, self.data)
            try:
                while True:
                    # Accumulate opcode
                    context.opcode += bytes([context.pop8()])
                    # Get the action for this opcode
                    action = self._instruction_decoder.get(context.opcode, _unknown_opcode)
                    try:
                        # Apply action
                        if isinstance(action, str):
                            disassembly = Disassembly(action)
                        else:
                            disassembly = action(context)
                        disassembly.opcode = context.opcode
                        disassembly.bytes = context.bytes
                    except NeedMoreBytesDecodeActionException:
                        # Increase pc in case the action requests so
                        continue
                    # If no exception was raised, stop accumulating the opcode
                    break
            except UnknownOpcodeException as err:
                print(hex(context.pc0), 'Unknown instruction:', format(int.from_bytes(context.bytes, byteorder='big'), 'x'), file=stderr)
                continue
            self.disassembly[context.pc0] = disassembly
            self.pcs.update(context.done())
            self.functions.update(context.functions)
            self.labels.update(context.labels)
            self.references.update(context.references)


class NeedMoreBytesDecodeActionException(Exception):
    pass


def _need_more_bytes(*args, **kwargs):
    raise NeedMoreBytesDecodeActionException()


class UnknownOpcodeException(Exception):
    pass


def _unknown_opcode(*args, **kwargs):
    raise UnknownOpcodeException()

__all__ = ['DecodeAction', 'Disassembler', 'UnknownOpcodeException', 'NeedMoreBytesDecodeActionException', 'MoreDecodeAction']
