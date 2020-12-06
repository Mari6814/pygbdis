

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

    def replace(self, *replacements):
        return {
            argname: next((
                r[argval]
                for r in replacements
                if argval in r), argval)
            for argname, argval in list(self.arguments.items())
        }

    def format(self, *replacements):
        replacement_args = self.replace(*replacements)
        return self.human_readable.format(
            opcode=self.opcode,
            bytes=self.bytes,
            **replacement_args,
        )

    def __repr__(self):
        return self.format()


__all__ = ['Disassembly']
