#!/usr/bin/env python3

"""
cpu.py: MIPS-Lite implementation

Author(s): Atharva Lele <atharva@pdx.edu>
"""

import config
import memory
import logging

class Instruction:
    # R-type
    ADD = 0b000000
    SUB = 0b000010
    MUL = 0b000100
    OR = 0b000110
    AND = 0b001000
    XOR = 0b001010

    # I- type
    ADDI = 0b000001
    SUBI = 0b000011
    MULI = 0b000101
    ORI = 0b000111
    ANDI = 0b001001
    XORI = 0b001011
    LDW  = 0b001100
    STW = 0b001101
    BZ = 0b001110
    BEQ = 0b001111
    JR = 0b010000
    HALT = 0b010001

    # Lists to hold instructions
    R_type_instr = [ADD, SUB, MUL, OR, AND, XOR]
    I_type_instr = [ADDI, SUBI, MULI, ORI, ANDI, XORI, LDW, STW, BZ, BEQ, JR, HALT]

    # Decoding Bitmasks
    OPCODE_BITMASK = 0xFC000000
    RS_BITMASK = 0x03E00000
    RT_BITMASK = 0x001F0000
    RD_BITMASK = 0x0000F800
    IMM_BITMASK = 0x000007FF

    def __init__(self, instr: int) -> None:
        self.instr = instr

    def decode(self) -> None:
        # Grab the opcode
        self.opcode = (self.instr & Instruction.OPCODE_BITMASK) >> 26

        # Get the instruction details depending on the type
        if self.opcode in Instruction.R_type_instr:
            self.type = 'R' 
            self.rs = (self.instr & Instruction.RS_BITMASK) >> 19
            self.rt = (self.instr & Instruction.RT_BITMASK) >> 16
            self.rd = (self.instr & Instruction.RD_BITMASK) >> 11
            self.imm = None
        elif self.opcode in Instruction.I_type_instr:
            self.type = 'I' 
            self.rs = (self.instr & Instruction.RS_BITMASK) >> 19
            self.rt = (self.instr & Instruction.RT_BITMASK) >> 16
            self.rd = None
            self.imm = self.instr & Instruction.IMM_BITMASK
        else:
            logging.error ('Invalid opcode: ' + bin(self.opcode)) 



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

        # Instantiate memory object
        self.mem = memory.Memory(config.MEM_SIZE)

    # CPU Operation per clock cycle
    def do_cpu_things(self) -> None:
        # Placeholder function for now
        pass
