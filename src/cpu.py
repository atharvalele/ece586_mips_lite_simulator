#!/usr/bin/env python3

"""
cpu.py: MIPS-Lite implementation

Author(s): Atharva Lele <atharva@pdx.edu>
"""

import config
import memory
import logging

from parser import parser

# Get twos complement value
def get_twos_complement_val(val: int, bits: int) -> int:
    # Check if sign bit is set & compute negative value
    if val & (1 << (bits - 1)) != 0:
        val = val - (1 << bits)
    return val

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
        self.A = None
        self.B = None
        self.imm_ext = None
        self.ref_addr = None
        self.alu_out = None

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

    # Return Destination register
    def get_dest_reg(self):
        if self.opcode in self.R_type_instr:
            return self.rd
        else:
            return self.rt

    # Return source register
    def get_src_regs(self):
        src_regs = []

        # Rs is always a source register
        src_regs.append(self.rs)

        # Rt is a source reg if it is a R-type instruction
        if self.opcode in self.R_type_instr:
            src_regs.append(self.rt)

        return src_regs
    

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

        # Hazard flags
        self.hazard_flag = False
        self.data_hazard = False
        self.control_hazard = False
        self.num_clocks_to_stall = 0

        # Register declaration
        # npc = next program counter
        # A, B, imm, ALUout registers used for ALU operations in the execute stage
        self.pc = 0
        self.npc = 0
        self.A = 0
        self.B = 0
        self.imm = 0
        self.alu_out = 0
        self.R = [0] * 32

        # Pipeline - initialized as a null list for now
        self.pipeline = [None, None, None, None, None]

        # Instantiate memory object
        self.mem = memory.Memory(config.MEM_SIZE)

        # Fill memory with data
        self.mem.write_n(0, parser(self.mem_fname))

    # Data Hazard Check
    def check_data_hazard(self):
        if self.pipeline[1] is not None:
            dest_reg = None
            source_regs = self.pipeline[1].get_src_regs()

            # Check if there are conflicts with the MEM stage
            if self.pipeline[3] is not None:
                dest_reg = self.pipeline[3].get_dest_reg()

                if dest_reg in source_regs:
                    logging.debug('DH: Hazard detected with MEM stage')
                    logging.debug(f'DH: Dest: {dest_reg}, SRCS: {source_regs}')

                    # Set flags - we don't need to check for conflicts
                    # with EX stage if we are going to stall for 1 cycle
                    self.data_hazard = True
                    self.num_clocks_to_stall = 1

            # Check if there are conflicts with the EX stage
            elif self.pipeline[2] is not None:
                dest_reg = self.pipeline[2].get_dest_reg()

                if dest_reg in source_regs:
                    logging.debug('DH: Hazard detected with EX stage')
                    logging.debug(f'DH: Dest: {dest_reg}, SRCS: {source_regs}')

                    self.data_hazard = True
                    self.num_clocks_to_stall = 2

            # No conflicts found
            else:
                self.data_hazard = False
                self.num_clocks_to_stall = 0


    # Instruction fetch
    def fetch(self):
        # Do not fetch if hazard has been detected
        if self.hazard_flag == True:
            return
        
        # Get 4 bytes from memory
        d_array = self.mem.read_n(self.pc, 4)

        # 'big' here means that that first byte in the array is MSB
        data = int.from_bytes(bytes=d_array, byteorder='big', signed=False)
        logging.debug('IF: 0x%08x' % data)

        # Create an instruction object and add it to the pipeline
        self.pipeline[0] = Instruction(data)

        # Update PC to PC + 4
        self.npc = self.pc + 4
        
    # Instruction decode
    def decode(self):
        # Do not decode if hazard has been detected
        if self.hazard_flag == True:
            return
        
        if self.pipeline[1] is not None:
            self.pipeline[1].decode()
            logging.debug(self.pipeline[1])

            # Grab register values stores in Rs, Rt
            self.pipeline[1].A = self.R[self.pipeline[1].rs]
            self.pipeline[1].B = self.R[self.pipeline[1].rt]
            logging.debug('ID: Operand Values = ' + str(self.A) + ', ' + str(self.B))

            # Sign extend the immediate -- only applies to I type
            if self.pipeline[1].opcode in Instruction.I_type_instr.values():
                self.pipeline[1].imm_ext = get_twos_complement_val(self.pipeline[1].imm, 16)
                logging.debug('ID: Immediate value = ' + str(self.pipeline[1].imm_ext))

            # Check for hazards
            self.check_data_hazard()

    # Instruction execute
    def execute(self):
        if self.pipeline[2] is not None:
            # Grab imm, A, B operands
            self.A = self.pipeline[2].A
            self.B = self.pipeline[2].B
            self.imm = self.pipeline[2].imm_ext

            # Add and Add Immediate
            if self.pipeline[2].opcode == Instruction.R_type_instr.get('ADD'):
                self.R[self.pipeline[2].rd] = self.A + self.B
            elif self.pipeline[2].opcode == Instruction.I_type_instr.get('ADDI'):
                self.R[self.pipeline[2].rt] = self.A + self.imm
            
            # Sub and Sub Immediate
            elif self.pipeline[2].opcode == Instruction.R_type_instr.get('SUB'):
                self.R[self.pipeline[2].rd] = self.A - self.B
            elif self.pipeline[2].opcode == Instruction.I_type_instr.get('SUBI'):
                self.R[self.pipeline[2].rt] = self.A - self.imm
                
            # Mul and Mul Immediate
            elif self.pipeline[2].opcode == Instruction.R_type_instr.get('MUL'):
                self.R[self.pipeline[2].rd] = self.A * self.B
            elif self.pipeline[2].opcode == Instruction.I_type_instr.get('MULI'):
                self.R[self.pipeline[2].rt] = self.A * self.imm
            
            # AND and AND Immediate
            elif self.pipeline[2].opcode == Instruction.R_type_instr.get('AND'):
                self.R[self.pipeline[2].rd] = self.A & self.B
            elif self.pipeline[2].opcode == Instruction.I_type_instr.get('ANDI'):
                self.R[self.pipeline[2].rt] = self.A & self.imm

            # OR and OR Immediate
            elif self.pipeline[2].opcode == Instruction.R_type_instr.get('OR'):
                self.R[self.pipeline[2].rd] = self.A | self.B
            elif self.pipeline[2].opcode == Instruction.I_type_instr.get('ORI'):
                self.R[self.pipeline[2].rt] = self.A | self.imm
                
            # XOR and XOR Immediate
            elif self.pipeline[2].opcode == Instruction.R_type_instr.get('XOR'):
                self.R[self.pipeline[2].rd] = self.A ^ self.B
            elif self.pipeline[2].opcode == Instruction.I_type_instr.get('XORI'):
                self.R[self.pipeline[2].rt] = self.A * self.imm

            # LDW 
            #elif self.pipeline[2].opcode == Instruction.I_type_instr.get('LDW'):
                # = imm_val + self.A  

            # STW
            #elif self.pipeline[2].opcode == Instruction.I_type_instr.get('STW'):
                # self.R[self.A] 
                
            #BZ

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
        # Shift instructions in the pipeline according to hazard conditions
        self.hazard_flag = self.data_hazard or self.control_hazard

        if (self.hazard_flag == True) and (self.num_clocks_to_stall > 0):
            # Pipeline will be blank at EX stage
            # [i0, i1, i2, i3, i4] --> [i0, i1, None, i2, i3]
            self.pipeline = self.pipeline[0:2] + [None] + self.pipeline[2:-1]

            # Decrement hazard stall clocks
            self.num_clocks_to_stall -= 1
        else:
            self.pipeline = [None] + self.pipeline[0:-1]

        # Debug print clock
        logging.debug('Clock: ' + str(self.clk))

        # 5-stage pipeline
        self.fetch()
        self.decode()
        self.execute()
        self.memory()
        self.writeback()

        # Set PC to updated value
        self.pc += self.npc

        # Increment clock
        self.clk += 1
