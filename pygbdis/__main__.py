from pathlib import Path
from argparse import ArgumentParser
from .disassembler import Disassembler
import os

parser = ArgumentParser()

AUTO_ENTRYPOINT = 'auto'

def entrypoint_type(i):
    if i is AUTO_ENTRYPOINT:
        return i
    return int(i)

parser.add_argument('input', type=Path)
parser.add_argument('--entrypoint', '-e', default=AUTO_ENTRYPOINT, type=entrypoint_type)
parser.add_argument('--arch', default='gbc', choices=['gbc'])
parser.add_argument('--gbc', action='store_const', const='gbc', dest='arch')
parser.add_argument('--output', '-o', default='out', type=Path, help="Path to directory in which the result will be stored.")
parser.add_argument('--format', '-f', default=None)

args = parser.parse_args()

rom = args.input.read_bytes()

print('rom size', len(rom) // 1024, 'kb')

if args.arch == 'gbc':
    if args.entrypoint == AUTO_ENTRYPOINT:
        args.entrypoint = 0x100
    from .gbc import GBC
    dis: Disassembler = GBC(rom)
    dis.disassemble(args.entrypoint)
    os.makedirs(args.output, exist_ok=True)
    outfile = (args.output / args.input.name).with_suffix('.asm')
    with open(outfile, 'w') as fd:
        if args.format:
            dis.save(fd, format_string=args.format)
        else:
            dis.save(fd)
