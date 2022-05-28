#!/usr/bin/env python3

"""
cpu_func.py: MIPS-Lite Single cycle functional simulator

Author(s): Shivani Palkar <spalkar@pdx.edu>
"""

from re import L
import config
import memory
import logging
import numpy
from instruction import Instruction

from parser import parser

# Get twos complement value
def get_twos_complement_val(val: int, bits: int) -> int:
    # Check if sign bit is set & compute negative value
    if val & (1 << (bits - 1)) != 0:
        val = val - (1 << bits)
    return val

class MIPS_lite_func:
    #Init
    def __init__ (self, mem_fname: str, out_fname: str) -> None:
        # Save memory image filename, and output filename 
        self.mem_fname = mem_fname
        self.out_fname = out_fname

        # Debugging print
        logging.debug('Starting simulator with the following config: ')
        logging.debug('Memory Image File: ' + self.mem_fname)
        logging.debug('Output File: ' + self.out_fname)

       
        self.pc = 0
        self.npc = 0 
        self.rs = 0
        self.rt = 0
        self.R = [0] * 32

        # Instantiate memory object
        self.mem = memory.Memory(config.MEM_SIZE)

        # Fill memory with data
        self.mem.write_n(0, parser(self.mem_fname))

        # Variables needed for final output prints
        self.modified_regs = []
        self.modified_addrs = []
        self.instr_count = 0
        self.arithmetic_instr_count = 0
        self.logical_instr_count = 0
        self.mem_instr_count = 0
        self.cntrl_instr_count = 0
        self.stall_count = 0

    
    def do_cpu_things(self) -> None:
        # FETCH
        # Get 4 bytes from memory
        d_array = self.mem.read_n(self.pc, 4)

        # 'big' here means that that first byte in the array is MSB
        data = int.from_bytes(bytes=d_array, byteorder='big', signed=False)
        logging.debug('IF: 0x%08x' % data)

        # Creating instruction object 
        instr = Instruction(data)

        # Update PC to PC + 4
        self.npc = self.pc + 4

        # DECODE
        instr.decode()

        # Sign extend for I - type
        if instr.opcode in Instruction.I_type_instr.values():
            instr.imm_ext = get_twos_complement_val(instr.imm, 16)
            logging.debug('ID: Immediate value = ' + str(instr.imm_ext))


        # EXECUTE
        self.instr_count += 1

        if instr.opcode in Instruction.R_type_instr.values():
            if instr.rd not in self.modified_regs:
                self.modified_regs.append(instr.rd)
        else:
            if instr.rt not in self.modified_regs:
                self.modified_regs.append(instr.rt)

        
        # Add and Add Immediate
        if instr.opcode == Instruction.R_type_instr.get('ADD'):
            self.R[instr.rd] = self.R[instr.rs] + self.R[instr.rt]
            self.arithmetic_instr_count += 1
        elif instr.opcode == Instruction.I_type_instr.get('ADDI'):
            self.R[instr.rt] = self.R[instr.rs] + instr.imm_ext
            self.arithmetic_instr_count += 1
        
        # Sub and Sub Immediate
        elif instr.opcode == Instruction.R_type_instr.get('SUB'):
            self.R[instr.rd] = self.R[instr.rs] - self.R[instr.rt]
            self.arithmetic_instr_count += 1
        elif instr.opcode == Instruction.I_type_instr.get('SUBI'):
            self.R[instr.rt] = self.R[instr.rs] - instr.imm_ext
            self.arithmetic_instr_count += 1
            
        # Mul and Mul Immediate
        elif instr.opcode == Instruction.R_type_instr.get('MUL'):
            self.R[instr.rd] = self.R[instr.rs] * self.R[instr.rt]
            self.arithmetic_instr_count += 1
        elif instr.opcode == Instruction.I_type_instr.get('MULI'):
            self.R[instr.rt] = self.R[instr.rs] * instr.imm_ext
            self.arithmetic_instr_count += 1
        
        # AND and AND Immediate
        elif instr.opcode == Instruction.R_type_instr.get('AND'):
            self.R[instr.rd] = self.R[instr.rs] & self.R[instr.rt]
            self.logical_instr_count += 1
        elif instr.opcode == Instruction.I_type_instr.get('ANDI'):
            self.R[instr.rt] = self.R[instr.rs] & instr.imm_ext
            self.logical_instr_count += 1

        # OR and OR Immediate
        elif instr.opcode == Instruction.R_type_instr.get('OR'):
            self.R[instr.rd] = self.R[instr.rs] | self.R[instr.rt]
            self.logical_instr_count += 1
        elif instr.opcode == Instruction.I_type_instr.get('ORI'):
            self.R[instr.rt] = self.R[instr.rs] | instr.imm_ext
            self.logical_instr_count += 1
            
        # XOR and XOR Immediate
        elif instr.opcode == Instruction.R_type_instr.get('XOR'):
            self.R[instr.rd] = self.R[instr.rs] ^ self.R[instr.rt]
            self.logical_instr_count += 1
        elif instr.opcode == Instruction.I_type_instr.get('XORI'):
            self.R[instr.rt] = self.R[instr.rs] ^ instr.imm_ext
            self.logical_instr_count += 1

        # LDW 
        elif instr.opcode == Instruction.I_type_instr.get('LDW'):
            ref_addr = self.R[instr.rs] + instr.imm_ext
            # Extract data array from memory
            data_array = self.mem.read_n(ref_addr, 4)
            data = int.from_bytes(bytes=data_array, byteorder='big', signed=True)
            self.R[instr.rt] = numpy.int32(data)
            logging.debug(f'MEM: Loaded R{instr.rt} with {numpy.int32(data)} from {ref_addr}')
            self.mem_instr_count += 1

        # STW
        elif instr.opcode == Instruction.I_type_instr.get('STW'):
            ref_addr = self.R[instr.rs] + instr.imm_ext
            # Write data array to memory 
            int_data = int(self.R[instr.rt])
            tobyte = int_data.to_bytes(4, 'big')
            data_array = self.mem.write_n(ref_addr, tobyte)
            logging.debug(f'MEM: Stored {int_data} to address {ref_addr}')

            if ref_addr not in self.modified_addrs:
                self.modified_addrs.append(ref_addr)
            self.mem_instr_count += 1

        #BZ
        elif instr.opcode == Instruction.I_type_instr.get('BZ'):
            if self.R[instr.rs] == 0:
                self.npc = self.pc + (4 * instr.imm_ext)
            self.cntrl_instr_count += 1
        
        #BEQ
        elif instr.opcode == Instruction.I_type_instr.get('BEQ'):
            if self.R[instr.rs] == self.R[instr.rt]:
                self.npc = self.pc + (4 * instr.imm_ext)
            else :
                self.npc = self.pc + 4
            self.cntrl_instr_count += 1
        
        #JR
        elif instr.opcode == Instruction.I_type_instr.get('JR'):
            self.npc = self.R[instr.rs]
            self.cntrl_instr_count += 1

        #HALT
        elif instr.opcode == Instruction.I_type_instr.get('HALT'):
            self.cntrl_instr_count += 1

        # Set PC to updated value
        self.pc = self.npc

        # Print register contents
        logging.debug(f'Registers: {self.R}')


        return (instr.opcode == Instruction.I_type_instr.get('HALT'))
