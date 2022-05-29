#!/usr/bin/env python3

"""
cpu.py: MIPS-Lite implementation

Author(s): Atharva Lele <atharva@pdx.edu>
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

class MIPS_lite:
    # Init
    def __init__(self, mode: str, mem_fname: str, out_fname: str) -> None:
        # Save mode, memory image filename, and output filename
        self.mode = mode
        self.mem_fname = mem_fname
        self.out_fname = out_fname

        # Halt flag
        self.halt_flag = False

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
        self.num_clocks_to_stall = 0

        # Register declaration
        # npc = next program counter
        # A, B, imm, ALUout registers used for ALU operations in the execute stage
        self.pc = 0
        self.npc = 0
        self.A = numpy.int32(0)
        self.B = numpy.int32(0)
        self.imm = numpy.int32(0)
        self.R = [0] * 32

        # Pipeline - initialized as a null list for now
        self.pipeline = [None, None, None, None, None]

        # Forwarding Registers
        self.mem_out = numpy.int32(0)
        self.alu_out = numpy.int32(0)
      
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

    # Function to add to a list, and keep it unique
    def add_to_list(self, lst, reg):
        if reg not in lst:
            lst.append(reg)
            lst.sort()
        return lst

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

                    if self.mode == 'fwd':
                        if dest_reg == self.pipeline[1].rs:
                            self.pipeline[1].fwd_A = 1
                        elif dest_reg == self.pipeline[1].rt:
                            self.pipeline[1].fwd_B = 1
                        logging.debug(f'DH: fwdA: {self.pipeline[1].fwd_A}, fwdB: {self.pipeline[1].fwd_B}')

                        self.data_hazard = False
                        self.num_clocks_to_stall = 0
                    
                    else:
                        # Set flags - we don't need to check for conflicts
                        # with EX stage if we are going to stall for 1 cycle
                        self.data_hazard = True
                        self.num_clocks_to_stall = 1

            # Check if there are conflicts with the EX stage
            if self.pipeline[2] is not None:
                dest_reg = self.pipeline[2].get_dest_reg()
                  
                if dest_reg in source_regs:
                    logging.debug('DH: Hazard detected with EX stage')
                    logging.debug(f'DH: Dest: {dest_reg}, SRCS: {source_regs}')

                    if self.mode == 'fwd':
                        # Back to bacK LDW - STW
                        if self.pipeline[2].opcode == Instruction.I_type_instr.get('LDW') and \
                             self.pipeline[1].opcode == Instruction.I_type_instr.get('STW') and \
                                 self.pipeline[1].rt == dest_reg:
                            self.pipeline[1].mem_to_mem = 1


                        if self.pipeline[2].opcode != Instruction.I_type_instr.get('LDW'):
                            if dest_reg == self.pipeline[1].rs:
                                self.pipeline[1].fwd_A = 2
                            elif dest_reg == self.pipeline[1].rt:
                                self.pipeline[1].fwd_B = 2
                            logging.debug(f'DH: fwdA: {self.pipeline[1].fwd_A}, fwdB: {self.pipeline[1].fwd_B}')
                            self.data_hazard = False
                            self.num_clocks_to_stall = 0
                        else:
                            #If instruction is load and mode is fwd, stall for 1 cycle
                            self.data_hazard = True
                            self.num_clocks_to_stall = 1

                    else: 
                        self.data_hazard = True
                        self.num_clocks_to_stall = 2


    # Flushing pipeline
    def flush_pipeline(self):
        logging.debug('EX: Pipeline flushed')
        self.pipeline[0] = None
        self.pipeline[1] = None

    # Instruction fetch
    def fetch(self):
        # Do not fetch if hazard has been detected
        if self.hazard_flag == True:
            return

        # Do not fetch more if halt instruction is found
        if self.halt_flag == True:
            return
        
        # Get 4 bytes from memory
        d_array = self.mem.read_n(self.pc, 4)

        # 'big' here means that that first byte in the array is MSB
        data = int.from_bytes(bytes=d_array, byteorder='big', signed=False)
        logging.debug('IF: 0x%08x' % data)

        # Create an instruction object and add it to the pipeline
        self.pipeline[0] = Instruction(data)

        # Saving pc for every instruction fetch
        self.pipeline[0].pc = self.pc

        # Update PC to PC + 4
        self.npc = self.pc + 4
        
    # Instruction decode
    def decode(self):
        # Do not decode if hazard has been detected
        if self.hazard_flag == True and self.pipeline[1] is not None:

            # Check if *anything* needs to be read for a pending forward
            if self.pipeline[1].fwd_A == 1:
                self.pipeline[1].A = self.mem_out
                self.pipeline[1].fwd_A = 0
            elif self.pipeline[1].fwd_B == 1:
                self.pipeline[1].B = self.mem_out
                self.pipeline[1].fwd_B = 0
            # Check for hazards
            self.check_data_hazard()
            return
   
        # Do not decode if halt is true
        if self.halt_flag == True:
            return
        
        if self.pipeline[1] is not None:
            self.pipeline[1].decode()
            logging.debug(self.pipeline[1])

            # Grab register values stores in Rs, Rt
            self.pipeline[1].A = numpy.int32(self.R[self.pipeline[1].rs])
            self.pipeline[1].B = numpy.int32(self.R[self.pipeline[1].rt])
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
            # Increment instruction count
            self.instr_count += 1

            logging.debug(self.pipeline[2])

            #Grab operands with fwd
            if self.mode == 'fwd':
                if self.pipeline[2].fwd_A == 0:
                    self.A = self.pipeline[2].A
                elif self.pipeline[2].fwd_A == 1:
                    self.A = self.mem_out
                elif self.pipeline[2].fwd_A == 2:
                    self.A = self.alu_out
                
                if self.pipeline[2].fwd_B == 0:
                    self.B = self.pipeline[2].B
                elif self.pipeline[2].fwd_B == 1:
                    self.B = self.mem_out
                elif self.pipeline[2].fwd_B == 2:
                    self.B = self.alu_out

            # no-fwd
            else:
                # Grab imm, A, B operands
                self.A = self.pipeline[2].A
                self.B = self.pipeline[2].B

            self.imm = self.pipeline[2].imm_ext
            logging.debug(f'EX: A = {self.pipeline[2].A}, B = {self.pipeline[2].B}, Imm = {self.imm}')

            # Add and Add Immediate
            if self.pipeline[2].opcode == Instruction.R_type_instr.get('ADD'):
                self.pipeline[2].alu_out = self.A + self.B
                self.arithmetic_instr_count += 1
            elif self.pipeline[2].opcode == Instruction.I_type_instr.get('ADDI'):
                self.pipeline[2].alu_out = self.A + self.imm
                self.arithmetic_instr_count += 1
            
            # Sub and Sub Immediate
            elif self.pipeline[2].opcode == Instruction.R_type_instr.get('SUB'):
                self.pipeline[2].alu_out = self.A - self.B
                self.arithmetic_instr_count += 1
            elif self.pipeline[2].opcode == Instruction.I_type_instr.get('SUBI'):
                self.pipeline[2].alu_out = self.A - self.imm
                self.arithmetic_instr_count += 1
                
            # Mul and Mul Immediate
            elif self.pipeline[2].opcode == Instruction.R_type_instr.get('MUL'):
                self.pipeline[2].alu_out = self.A * self.B
                self.arithmetic_instr_count += 1
            elif self.pipeline[2].opcode == Instruction.I_type_instr.get('MULI'):
                self.pipeline[2].alu_out = self.A * self.imm
                self.arithmetic_instr_count += 1
            
            # AND and AND Immediate
            elif self.pipeline[2].opcode == Instruction.R_type_instr.get('AND'):
                self.pipeline[2].alu_out = self.A & self.B
                self.logical_instr_count += 1
            elif self.pipeline[2].opcode == Instruction.I_type_instr.get('ANDI'):
                self.pipeline[2].alu_out = self.A & self.imm
                self.logical_instr_count += 1

            # OR and OR Immediate
            elif self.pipeline[2].opcode == Instruction.R_type_instr.get('OR'):
                self.pipeline[2].alu_out = self.A | self.B
                self.logical_instr_count += 1
            elif self.pipeline[2].opcode == Instruction.I_type_instr.get('ORI'):
                self.pipeline[2].alu_out = self.A | self.imm
                self.logical_instr_count += 1
                
            # XOR and XOR Immediate
            elif self.pipeline[2].opcode == Instruction.R_type_instr.get('XOR'):
                self.pipeline[2].alu_out = self.A ^ self.B
                self.logical_instr_count += 1
            elif self.pipeline[2].opcode == Instruction.I_type_instr.get('XORI'):
                self.pipeline[2].alu_out = self.A ^ self.imm
                self.logical_instr_count += 1

            # LDW 
            elif self.pipeline[2].opcode == Instruction.I_type_instr.get('LDW'):
                self.pipeline[2].ref_addr = self.A + self.imm
                self.mem_instr_count += 1

            # STW
            elif self.pipeline[2].opcode == Instruction.I_type_instr.get('STW'):
                self.pipeline[2].ref_addr = self.A + self.imm
                self.mem_instr_count += 1

            #BZ
            elif self.pipeline[2].opcode == Instruction.I_type_instr.get('BZ'):
                if self.A == 0:
                    self.npc = self.pipeline[2].pc + (4 * self.imm)
                    self.flush_pipeline()
                self.cntrl_instr_count += 1
          
            #BEQ
            elif self.pipeline[2].opcode == Instruction.I_type_instr.get('BEQ'):
                if self.A == self.B:
                    self.npc = self.pipeline[2].pc + (4 * self.imm)
                    self.flush_pipeline()
                else :
                    self.npc = self.pc + 4
                self.cntrl_instr_count += 1
            
            #JR
            elif self.pipeline[2].opcode == Instruction.I_type_instr.get('JR'):
                self.npc = self.R[self.pipeline[2].rs]
                self.flush_pipeline()
                self.cntrl_instr_count += 1

            #HALT
            elif self.pipeline[2].opcode == Instruction.I_type_instr.get('HALT'):
                self.halt_flag = True
                self.flush_pipeline()
                self.hazard_flag = False
                self.num_clocks_to_stall = 0
                self.cntrl_instr_count += 1

            else:
                pass
            
            #Copy data to forwarding register
            self.alu_out = self.pipeline[2].alu_out
        else:
            logging.debug('EX: Empty')


    # Instruction memory
    def memory(self):
        if self.pipeline[3] is not None:
            logging.debug(self.pipeline[3])
            if self.pipeline[3].opcode == Instruction.I_type_instr.get('LDW'):
                # Extract data array from memory
                data_array = self.mem.read_n(self.pipeline[3].ref_addr, 4)
                data = int.from_bytes(bytes=data_array, byteorder='big', signed=True)
                self.pipeline[3].B = numpy.int32(data)
                self.mem_out = self.pipeline[3].B
                logging.debug(f'MEM: Loaded R{self.pipeline[3].get_dest_reg()} with {self.pipeline[3].B} from {self.pipeline[3].ref_addr}')
            elif self.pipeline[3].opcode == Instruction.I_type_instr.get('STW'):
                # Write data array to memory 
                if self.mode == 'fwd' and self.pipeline[3].mem_to_mem == 1:
                    int_data = self.mem_out
                else:
                    int_data = int(self.pipeline[3].B)

                tobyte = int_data.to_bytes(4, 'big')
                data_array = self.mem.write_n(self.pipeline[3].ref_addr, tobyte)
                logging.debug(f'MEM: Stored {int_data} to address {self.pipeline[3].ref_addr}')
                # Add to modified memory addrs
                if self.pipeline[3].ref_addr not in self.modified_addrs:
                    self.modified_addrs.append(self.pipeline[3].ref_addr)
            else:
                self.mem_out = self.pipeline[3].alu_out

    # Instruction writeback
    def writeback(self):
        if self.pipeline[4] is not None:
            if self.pipeline[4].opcode in Instruction.I_type_instr.values():
                if self.pipeline[4].opcode == Instruction.I_type_instr.get('LDW'):
                    self.R[self.pipeline[4].rt] = self.pipeline[4].B
                    logging.debug(f'WB: R{self.pipeline[4].rt} = {self.pipeline[4].B}')
                    # Add to modified reg list
                    if self.pipeline[4].rt not in self.modified_regs:
                        self.modified_regs.append(self.pipeline[4].rt)
                elif self.pipeline[4].opcode == Instruction.I_type_instr.get('STW'):
                    pass
                elif self.pipeline[4].opcode == Instruction.I_type_instr.get('BZ'):
                    pass
                elif self.pipeline[4].opcode == Instruction.I_type_instr.get('BEQ'):
                    pass
                elif self.pipeline[4].opcode == Instruction.I_type_instr.get('JR'):
                    pass
                else:
                    self.R[self.pipeline[4].rt] = self.pipeline[4].alu_out
                    logging.debug(f'WB: R{self.pipeline[4].rt} = {self.pipeline[4].alu_out}')
                    # Add to modified reg list
                    if self.pipeline[4].rt not in self.modified_regs:
                        self.modified_regs.append(self.pipeline[4].rt)
            else:
                self.R[self.pipeline[4].rd] = self.pipeline[4].alu_out
                logging.debug(f'WB: R{self.pipeline[4].rd} = {self.pipeline[4].alu_out}')
                # Add to modified reg list
                if self.pipeline[4].rd not in self.modified_regs:
                    self.modified_regs.append(self.pipeline[4].rd)


    # CPU Operation per clock cycle
    def do_cpu_things(self) -> None:
        # Shift instructions in the pipeline according to hazard conditions
        self.hazard_flag = self.data_hazard

        if (self.hazard_flag == True) and (self.num_clocks_to_stall > 0):
            # Pipeline will be blank at EX stage
            # [i0, i1, i2, i3, i4] --> [i0, i1, None, i2, i3]
            self.pipeline = self.pipeline[0:2] + [None] + self.pipeline[2:-1]

            # Decrement hazard stall clocks
            self.num_clocks_to_stall -= 1
            self.stall_count += 1

        else:
            # [i0, i1, i2, i3, i4] --> [None, i0, i1, i2, i3]
            self.pipeline = [None] + self.pipeline[0:-1]

        # Debug print clock
        logging.debug('\n\n---------- Clock: ' + str(self.clk) + '\tPC: ' + str(self.pc) + ' ----------')

        # 5-stage pipeline
        self.fetch()
        self.decode()
        self.execute()
        self.memory()
        self.writeback()

        # If in a hazard condition, read register values need to be updated
        # when the hazard condition is over
        if self.hazard_flag == True and self.num_clocks_to_stall == 0:
            self.data_hazard = False
            if self.pipeline[1] is not None:
                self.pipeline[1].A = numpy.int32(self.R[self.pipeline[1].rs])
                self.pipeline[1].B = numpy.int32(self.R[self.pipeline[1].rt])
                logging.debug('DH: Updated Operand Values = ' + str(self.pipeline[1].A) + ', ' + str(self.pipeline[1].B))

        # Set PC to updated value
        self.pc = self.npc

        # Print register contents
        logging.debug(f'Registers: {self.R}')

        # Increment clock
        self.clk += 1

        # Check if program should quit
        return self.pipeline.count(None) == len(self.pipeline)
