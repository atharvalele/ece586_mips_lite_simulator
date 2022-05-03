#!/usr/bin/env python3

"""
cpu.py: MIPS-Lite implementation

Author(s): Atharva Lele <atharva@pdx.edu>
"""

import config
import memory
import logging

from parser import parser

class Instruction:
    # Dictionaries to hold instructions
    R_type_instr = {
        'ADD': 0b000000,
        'SUB': 0b000010,
        'MUL': 0b000100,
        'OR': 0b000110,
        'AND': 0b001000,
        'XOR': 0b001010
    }

    I_type_instr = {
        'ADDI': 0b000001,
        'SUBI': 0b000011,
        'MULI': 0b000101,
        'ORI': 0b000111,
        'ANDI': 0b001001,
        'XORI': 0b001011,
        'LDW' : 0b001100,
        'STW': 0b001101,
        'BZ': 0b001110,
        'BEQ': 0b001111,
        'JR': 0b010000,
        'HALT': 0b010001
    }

    # Decoding Bitmasks
    OPCODE_BITMASK = 0xFC000000
    RS_BITMASK = 0x03E00000
    RT_BITMASK = 0x001F0000
    RD_BITMASK = 0x0000F800
    IMM_BITMASK = 0x000007FF

    def __init__(self, instr: int) -> None:
        self.instr = instr

    # Get 'key' for value
    def find_key(self, input_dict, value):
        for key, val in input_dict.items():
            if val == value: return key
        return 'None'

    # Override for print()
    def __str__(self):
        if self.opcode is not None:
            # format(): 2 characters taken for '0b', so add that to # of needed characters
            info = '\nInstruction: 0x%08x' % self.instr + ' : ' + format(self.instr, '#034b')
            info += '\nOpcode: ' + hex(self.opcode) + ' : ' + format(self.opcode, '#08b')
            info += '\nType: ' + self.type
            info += '\nRs: ' + hex(self.rs) + ' : ' + format(self.rs, '#07b')
            info += '\nRt: ' + hex(self.rt) + ' : ' + format(self.rt, '#07b')

            if self.type == 'R':
                info += '\nRd: ' + hex(self.rd) + ' : ' + format(self.rd, '#07b')
                info += '\nName: ' + self.find_key(self.R_type_instr, self.opcode)
            else:
                info += '\nImm: ' + hex(self.imm) + ' : ' + format(self.imm, '#013b')
                info += '\nName: ' + self.find_key(self.I_type_instr, self.opcode)
        else:
            info = 'Not decoded/Empty'
        
        return info

    def decode(self) -> None:
        # Grab the opcode
        self.opcode = (self.instr & Instruction.OPCODE_BITMASK) >> 26

        # Get the instruction details depending on the type
        if self.opcode in Instruction.R_type_instr.values():
            self.type = 'R' 
            self.rs = (self.instr & Instruction.RS_BITMASK) >> 21
            self.rt = (self.instr & Instruction.RT_BITMASK) >> 16
            self.rd = (self.instr & Instruction.RD_BITMASK) >> 11
            self.imm = None
        elif self.opcode in Instruction.I_type_instr.values():
            self.type = 'I' 
            self.rs = (self.instr & Instruction.RS_BITMASK) >> 21
            self.rt = (self.instr & Instruction.RT_BITMASK) >> 16
            self.rd = None
            self.imm = self.instr & Instruction.IMM_BITMASK
        else:
            logging.error('Invalid opcode: ' + bin(self.opcode))
            exit(1)



class MIPS_lite:
    # Init
    def __init__(self, mode: str, mem_fname: str, out_fname: str) -> None:
        # Save mode, memory image filename, and output filename
        self.mode = mode
        self.mem_fname = mem_fname
        self.out_fname = out_fname

        # Debugging print
        logging.debug('Starting simulator with the following config: ')
        logging.debug('Memory Image File: ' + self.mem_fname)
        logging.debug('Output File: ' + self.out_fname)
        logging.debug('Mode: ' + self.mode)

        # Clock cycle counter
        self.clk = 0

        # Register declaration
        self.pc = 0
        self.R = [0] * 32

        # Pipeline - initialized as a null list for now
        self.pipeline = [None, None, None, None, None]

        # Instantiate memory object
        self.mem = memory.Memory(config.MEM_SIZE)

        # Fill memory with data
        self.mem.write_n(0, parser(self.mem_fname))

    # Instruction fetch
    def fetch(self):
        # Get 4 bytes from memory
        d_array = self.mem.read_n(self.pc, 4)

        # 'big' here means that that first byte in the array is MSB
        data = int.from_bytes(bytes=d_array, byteorder='big', signed=False)
        logging.debug('IF: 0x%08x' % data)

        # Create an instruction object and add it to the pipeline
        self.pipeline[0] = Instruction(data)
        
    # Instruction decode
    def decode(self):
        if self.pipeline[1] is not None:
            self.pipeline[1].decode()
            logging.debug(self.pipeline[1])

    # Instruction execute
    def execute(self):
        # Placeholder
        pass

    # Instruction memory
    def memory(self):
        # Placeholder
        pass

    # Instruction writeback
    def writeback(self):
        # Placeholder
        pass


    # CPU Operation per clock cycle
    def do_cpu_things(self) -> None:
        # Shift instructions in the pipeline
        self.pipeline = [None] + self.pipeline[0:-1]

        # Debug print clock
        logging.debug('Clock: ' + str(self.clk))

        # 5-stage pipeline
        self.fetch()
        self.decode()
        self.execute()
        self.memory()
        self.writeback()

        # Increment PC
        self.pc += 4

        # Increment clock
        self.clk += 1
