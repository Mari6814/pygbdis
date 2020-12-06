from typing import Dict, Set, Tuple, NewType, Callable, Pattern
from sys import stderr

from .context import PC, Disassembly, Context, Union

__all__ = ['DecodeAction', 'Disassembler', 'UnknownOpcodeException', 'NeedMoreBytesDecodeActionException']

DecodeAction = NewType('DecodeAction', Union[Callable[[Context], Disassembly], str])

class Disassembler:
    def __init__(self, data: bytes):
        self.data = data
        self.pcs: Set[PC] = set()
        self.disassembly: Dict[PC, Disassembly] = dict()
        self._instruction_decoder: Dict[bytes, DecodeAction] = dict()
        self.initialize_instructions()
        self.functions: Set[PC] = set()
        self.labels: Set[PC] = set()
        self.references: Set[PC] = set()

    def initialize_instructions(self):
        ' This should be overwritten by the user to initialize all actions. '
        raise NotImplementedError()

    def add_instruction(self, opcode: bytes, action: DecodeAction = 'more'):
        ''' Add an action that should be done if the opcode is decoded.

        Returns:
            Function that takes the context and returns a disassembly,
            or a string with the human readable disassembly, in case the instruction
            can be directly disassembled without using extra bytes or adding labels/jumps/functions/variables.
        '''
        if not isinstance(opcode, bytes):
            opcode = bytes([opcode])
        if opcode in self._instruction_decoder:
            raise ValueError('Instruction already added: %s' % opcode)
        if action == 'more':
            self._instruction_decoder[opcode] = _need_more_bytes
        else:
            self._instruction_decoder[opcode] = action

    def add_instruction_range(self, start: int, end: int, bytecount: int, action='more', step: int = 1):
        for i in range(start, end, step):
            ibytes = sum(reversed(
                bytes([i >> (c*8) & 0xFF])
                for c in range(bytecount)))

    def start(self, pc: PC):
        ' Starts the decoding at the given initial program counter. '
        self.pcs.add(pc)
        while self.pcs:
            pc = self.pcs.pop()
            if pc in self.disassembly:
                continue
            if pc >= len(self.data):
                print(f'err: End of stream: {pc}', file=stderr)
                continue
            opcode = b''
            action = None
            try:
                while True:
                    # Accumulate opcode
                    opcode += self.data[pc:pc+1]
                    # Create context
                    context = Context(pc, self.data, opcode=opcode)
                    # Get the action for this opcode
                    action = self._get_decode_action(opcode)
                    try:
                        # Apply action
                        if isinstance(action, str):
                            disassembly = Disassembly(action)
                        else:
                            disassembly = action(context)
                        disassembly.opcode = opcode
                    except NeedMoreBytesDecodeActionException:
                        # Increase pc in case the action requests so
                        pc += 1
                        continue
                    # If no exception was raised, stop accumulating the opcode
                    break
            except UnknownOpcodeException as err:
                print(pc, 'Unknown opcode:', opcode, file=stderr)
                continue
            except:
                print('opcode=', opcode, 'pc=', pc, 'action=', action)
                raise
            # print('0x{pc:04x}: {dis}'.format( pc=pc, dis=disassembly))
            self.disassembly[pc] = disassembly
            self.pcs.update(context.done())
            self.functions.update(context.functions)
            self.labels.update(context.labels)
            self.references.update(context.references)

    def _get_decode_action(self, opcode: bytes):
        ' Get the decoder action registered by the user for this opcode. '
        return self._instruction_decoder.get(opcode, _unknown_opcode)


class NeedMoreBytesDecodeActionException(Exception):
    pass


def _need_more_bytes(*args, **kwargs):
    raise NeedMoreBytesDecodeActionException()


class UnknownOpcodeException(Exception):
    pass


def _unknown_opcode(*args, **kwargs):
    raise UnknownOpcodeException()
