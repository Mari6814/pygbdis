

class Disassembly:
    ''' Container for disassembled and human readable instruction.
        Additionally, arguments, opcodes, location and all used bytes are also stored.
    '''
    def __init__(
        self,
        human_readable: str,
        **arguments):
        self.human_readable = human_readable
        self.arguments = arguments
        self.address: bytes = None
        self.opcode: bytes = None
        self.bytes: bytes = None

    def format(self):
        return self.human_readable.format(
            opcode=self.opcode,
            bytes=self.bytes,
            **self.arguments,
        )

    def __repr__(self):
        return self.format()


__all__ = ['Disassembly']
