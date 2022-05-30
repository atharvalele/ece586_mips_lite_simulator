#!/usr/bin/env python3

"""
instruction.py: MIPS-Lite implementation

Author(s): Atharva Lele <atharva@pdx.edu>
"""

import logging
import numpy

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
    IMM_BITMASK = 0x0000FFFF

    def __init__(self, instr: int) -> None:
        self.instr = instr

        # A = content of Rs, B = content of Rt, alu_out = ALU output
        # imm_ext = sign-extended immediate, ref_addr = Address for a LDW/STW
        # None would simply mean that it is not used
        self.A = numpy.int32(0)
        self.B = numpy.int32(0)
        self.imm_ext = numpy.int32(0)
        self.ref_addr = numpy.int32(0)
        self.alu_out = numpy.int32(0)
        self.mem_to_mem = 0
        self.dh_counted = False

        # Forwarding flags
        self.fwd_A = 0
        self.fwd_B = 0

    # Get 'key' for value
    def find_key(self, input_dict, value):
        for key, val in input_dict.items():
            if val == value: return key
        return 'None'

    # Get decoded instr
    def get_instr(self):
        if self.opcode is not None:
            if self.type == 'R':
                return  f'\n{self.find_key(self.R_type_instr, self.opcode)} R{self.rd}, R{self.rs}, R{self.rt}'
            else:
                return f'\n{self.find_key(self.I_type_instr, self.opcode)} R{self.rt}, R{self.rs}, {hex(self.imm)}'

    # Override for print()
    def __str__(self):
        if self.opcode is not None:
            # format(): 2 characters taken for '0b', so add that to # of needed characters
            info = '\nInstruction: 0x%08x' % self.instr + ' : ' + format(self.instr, '#034b')
            info += '\nOpcode: ' + hex(self.opcode) + ' : ' + format(self.opcode, '#08b')
            info += '\nType: ' + self.type
            # info += '\nRs: ' + hex(self.rs) + ' : ' + format(self.rs, '#07b')
            # info += '\nRt: ' + hex(self.rt) + ' : ' + format(self.rt, '#07b')

            if self.type == 'R':
                # info += '\nRd: ' + hex(self.rd) + ' : ' + format(self.rd, '#07b')
                # info += '\nName: ' + self.find_key(self.R_type_instr, self.opcode)
                info += f'\n{self.find_key(self.R_type_instr, self.opcode)} R{self.rd}, R{self.rs}, R{self.rt}'
            else:
                # info += '\nImm: ' + hex(self.imm) + ' : ' + format(self.imm, '#013b')
                # info += '\nName: ' + self.find_key(self.I_type_instr, self.opcode)
                info += f'\n{self.find_key(self.I_type_instr, self.opcode)} R{self.rt}, R{self.rs}, {hex(self.imm)}'
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

    # Return Destination register
    def get_dest_reg(self):
        if self.opcode in Instruction.R_type_instr.values():
            return self.rd
        else:
            return self.rt

    # Return source register
    def get_src_regs(self):
        src_regs = []

        # Rs is always a source register
        if self.rs != 0:
            src_regs.append(self.rs)

        # Rt is a source reg if it is a R-type instruction or BEQ
        if ((self.opcode in Instruction.R_type_instr.values()) or (self.opcode == Instruction.I_type_instr.get('BEQ'))):
            if self.rt != 0:
                src_regs.append(self.rt)

        return src_regs