from pathlib import Path
from argparse import ArgumentParser
from .disassembler import Disassembler

parser = ArgumentParser()

parser.add_argument('input', type=Path)
parser.add_argument('--entrypoint', '-e', default=0x0, type=int)
parser.add_argument('--arch', default='gbc', choices=['gbc'])
parser.add_argument('--gbc', action='store_const', const='gbc', dest='arch')

args = parser.parse_args()

with open(args.input, 'rb') as fd:
    rom = fd.read()

print('rom size', len(rom) // 1024, 'kb')

if args.arch == 'gbc':
    from .gbc import GBC
    dis: Disassembler = GBC(rom)
    dis.start(args.entrypoint)
