# pygbdis

## Description

A simple disassembler written in Python for disassembling Game Boy-family ROMs (GB, GBC, GBA).
Currently, only **Game Boy (GBC)** is supported.

## Features

* Disassembles GBC ROMs to annotated `.asm` files
* Automatic or user-defined entrypoint support
* Optional output formatting
* Output to a chosen directory

## Requirements

* Python 3.7+

No external dependencies required.

## Installation

Clone the repository:

```bash
git clone https://github.com/Mari6814/pygbdis.git
cd pygbdis
```

## Usage

You can run the disassembler using Python's module interface:

```bash
python -m pygbdis path/to/game.gb [options]
```

### Example

```bash
python -m pygbdis mygame.gb --entrypoint 0x100 --output out/
```

### Arguments

| Argument             | Description                                                     |
| -------------------- | --------------------------------------------------------------- |
| `input`              | Path to the ROM file                                            |
| `--entrypoint`, `-e` | Start address for disassembly (`auto` by default, uses `0x100`) |
| `--arch`             | Target architecture (currently only `gbc` supported)            |
| `--gbc`              | Shortcut to set `--arch gbc`                                    |
| `--output`, `-o`     | Output directory (default: `out/`)                              |
| `--format`, `-f`     | Optional format string to customize the disassembly output      |

## Output

The disassembled `.asm` file will be saved to the specified output directory, with the same base name as the input ROM.

Example:
Disassembling `game.gb` with `--output out/` will produce:

```
out/game.asm
```

## License

MIT License
