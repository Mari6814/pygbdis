from typing import *
from collections import defaultdict
from .disassembly import Disassembly

__all__ = ['PC', 'Context']


class Context:
    def __init__(self, pc: int, data: bytes):
        # current pc
        self.pc: int = pc
        # pc of the first byte
        self.pc0: int = pc
        # rom data
        self.data: bytes = data
        # opcode buffer used by the instruction decoder
        self.opcode: bytes = b''
        # all bytes popped by this context
        self.bytes: bytes = b''
        # flag if true, then the program executes the instruction after this instruction
        # if false, then a jump was made and the following bytes may not be executable
        self.continues: bool = True
        # set of all jumps that this instruction does
        self.jumps: Set[int] = set()
        # set of functions that are jumped to
        self.functions: Dict[int, str] = dict()
        # set of labels that are jumped to 
        self.labels: Dict[int, str] = dict()
        # set of data referenced
        self.references: Dict[int, str] = dict()

    def done(self) -> Set[int]:
        ''' Call when done with this context.

        Returns:
            The set of program counters that this instruction could potentially reach.
        '''
        if self.continues:
            return self.jumps | { self.pc }
        return self.jumps

    def pop8(self):
        ' Pop one byte and increase the program counter. '
        if self.pc >= len(self.data):
            raise ValueError(f'Program counter is at end of rom: {self.pc} of {len(self.data)}')
        data = self.data[self.pc]
        self.bytes += bytes([data])
        self.pc += 1
        return data

    def pop8_signed(self):
        ''' Pop one byte and decode it as a signed integer.
        Increase the program counter. '''
        data = self.pop8()
        if data > 127:
            data = -(256 - data)
        return data

    def pop16_ls_first(self):
        ''' Pop two bytes, assemble them in reverse order,
        and increase the current program counter. '''
        a = self.pop8()
        ls = self.pop8()
        return ls << 8 | a
    
    def pop16(self):
        ' Pop two bytes and increase the program counter. '
        a = self.pop8()
        ls = self.pop8()
        return a << 8 | ls

    def reference(self, abs: int, offset: int = 0, read: bool = True, write: bool = True):
        ''' Remembers the reference to the data in ram

        Parameters:
            abs: Absolute address to the referenced byte.
            offset: Offset relative to the absolute address.
            read: Flag that marks the address as read by the instruction.
            write: Flag that marks the address as written to by the instruction.

        Returns:
            The referenced address.
        '''
        abs += offset
        self.references[abs] = None
        return abs

    def call(self, abs: int = None, offset: int = 0, conditional: bool = False):
        ''' Remembers the call to the called location.

        Parameters:
            abs: Absolute address of the called location. If abs is None, then the current pc will be used.
            offset: Offset relative to the given absolute address.
            conditional: Enables conditional call, but that doesnt habe an effect on the context.

        Returns:
            The address of the called location.
        '''
        if abs is None:
            abs = self.pc
        abs += offset
        self.jumps.add(abs)
        self.functions[abs] = None
        return abs

    def jump(self, abs: int = None, offset: int = 0, conditional: bool = False):
        ''' Remembers the address of the target label.

        Parameters:
            abs: Absolute address of the target label. If abs is None, then the current pc will be used.
            offset: Offset relative to the given absolute address.

        Returns:
            The address of the called label.
        '''
        if abs is None:
            abs = self.pc
        abs += offset
        self.jumps.add(abs)
        self.labels[abs] = None
        if not conditional:
            self.continues = False
        return abs

    def halt(self, dis: Disassembly):
        ''' The decoded instruction halts the program
        and the current program counter will not be executed.

        This is a passthrough function, where the arguments are returned directly.
        This function only changes the state of the context.

        Returns:
            Disassembly
        '''
        self.continues = False
        return dis

    def ret(self, dis: Disassembly):
        ''' The decoded instruction returns and the current program counter will not be executed.

        This is a passthrough function, where the arguments are returned directly.
        This function only changes the state of the context.

        Returns:
            Disassembly
        '''
        self.continues = False
        return dis
