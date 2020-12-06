from typing import *
from collections import defaultdict

__all__ = ['PC', 'Disassembly', 'Context']

PC = NewType('ProgramCounter', bytes)

class Disassembly:
    def __init__(
        self,
        human_readable: str,
        **arguments):
        self.human_readable = human_readable
        self.arguments = arguments
        self.opcode = None

    def format(self):
        return self.human_readable.format(
            opcode=self.opcode,
            **self.arguments,
        )

    def __repr__(self):
        return self.format()


class Context:
    def __init__(self, pc: PC, data: bytes, opcode: bytes):
        # current pc
        self.pc: PC = pc
        # rom data
        self.data: bytes = data
        # opcode buffer used by the instruction decoder
        self.opcode: bytes = opcode
        # flag if true, then the program executes the instruction after this instruction
        # if false, then a jump was made and the following bytes may not be executable
        self.continues: bool = True
        # set of all jumps that this instruction does
        self.jumps: Set[PC] = set()
        # set of functions that are jumped to
        self.functions: Set[PC] = set()
        # set of labels that are jumped to 
        self.labels: Set[PC] = set()
        # set of data referenced
        self.references: Set[int] = set()

    def done(self) -> Set[PC]:
        ''' Call when done with this context.

        Returns:
            The set of program counters that this instruction could potentially reach.
        '''
        if self.continues:
            return self.jumps | { self.pc + 1 }
        return self.jumps

    def pop8(self):
        ' Pop one byte and increase the program counter. '
        self.pc += 1
        data = self.data[self.pc]
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

    def reference(self, abs: int, offset: int = 0):
        ''' Remembers the reference to the data in ram

        Parameters:
            abs: Absolute address to the referenced byte.

        Returns:
            The argument.
        '''
        self.references.add(offset + abs)
        return abs

    def call(self, abs: int):
        ''' The decoded instruction calls the absolute pc,
        but will return to the current pc later.

        Returns:
            The argument
        '''
        self.jumps.add(abs)
        self.functions.add(abs)
        return abs

    def call_rel(self, rel: int):
        ''' The decoded instruction calls the relative pc,
        but will return to the current pc later.

        Returns:
            The argument.
        '''
        self.jumps.add(rel + self.pc)
        self.functions.add(rel + self.pc)
        return rel

    def jump(self, abs: int):
        ''' The decoded instruction jumps to the absolute
        and does not return to the current pc.
        
        Returns:
            the argument
        '''
        self.jumps.add(abs)
        self.continues = False
        self.labels.add(abs)
        return abs

    def jump_rel(self, rel: int):
        ''' The decoded instruction jumps to the relative address
        and does not return to the current pc.

        Returns:
            The argument
        '''
        self.jumps.add(rel + self.pc)
        self.continues = False
        self.labels.add(rel + self.pc)
        return rel

    def jump_cond(self, abs: int):
        ''' The decoded instruction conditionally jumps to the absolute.

        Returns:
            The absolute jump address
        '''
        self.jumps.add(abs)
        self.labels.add(abs)
        return abs

    def jump_cond_rel(self, rel: int):
        ''' The decoded instruction conditionally jumps to the relative address.

        Returns:
            The relative jump address
        '''
        self.jumps.add(self.pc + rel)
        self.labels.add(self.pc + rel)
        return rel

    def halt(self, dis: Disassembly):
        ''' The decoded instruction halts the program
        and the current program counter will not be executed.

        Returns:
            dis for chaining
        '''
        self.continues = False
        return dis

    def ret(self, dis: Disassembly):
        ''' The decoded instruction returns
        and the current program counter will not be executed.

        Returns:
            dis for chaining
        '''
        self.continues = False
        return dis
