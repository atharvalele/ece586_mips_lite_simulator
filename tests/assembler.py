#!/usr/bin/env python3

"""
assembler.py: File for testing the project

Author(s): Ayush Srivastava <ayush@pdx.edu> Mehul Shah <mehul@pdx.edu>
"""

import sys

def op_code_check(opcode: str):
    r_type = {       
        "ADD": 0b000000,
        "SUB": 0b000010,
        "MUL": 0b000100,
        "OR" : 0b000110,
        "AND": 0b001000,
        "XOR": 0b001010
    }
    i_type = {
        "ADDI": 0b000001,
        "SUBI": 0b000011,
        "MULI": 0b000101,
        "ORI": 0b000111,
        "ANDI": 0b001001,
        "XORI": 0b001011,
        "LDW": 0b001100,
        "STW": 0b001101,
        "BZ": 0b001110,
        "BEQ": 0b001111,
        "JR": 0b010000,
        "HALT": 0b010001   
    }
    if opcode in r_type:
        return r_type.get(opcode), "R"
    elif opcode in i_type:
        return i_type.get(opcode), "I"
    else:
        exit(1)

def r_check(rd: str):
    reg_no = bin(int(rd[-1])).replace("0b","")

    r = str(reg_no)
    r = r.zfill(5)
    return r

def imm_check(imm: str):
    imm_val = int(imm)
    if (imm_val > 2**16 or imm_val < -(2**16)):
        print("Immediate Field Exceeded")
        exit(1)
    elif (imm_val < 0):
        return imm_val + (1<<16)
    else:
        return imm_val
    

def convert_to_mem(output: str, command):
    # Extract tokens from list
    o_file = open(output, 'w') 
    for i in command:
        op_list = i.split()
        op, instr_type = op_code_check(op_list[0])
        if (instr_type == "R"):
            # Determine Registers
            rd = r_check(op_list[1][:-1])
            rs = r_check(op_list[2][:-1])
            rt = r_check(op_list[3])  
            # Convert to the correct format for memory image
            trace = bin(op).replace("0b","").zfill(6) + rs + rt + rd
            trace = hex(int(trace.ljust(32, "0"),2)).replace("0x","").zfill(8)

            # Write to file 
            # Debug
            print(trace)
            trace = trace + "\n"
            # Write to file
            o_file.write(trace)

        elif (instr_type == "I"):
            # Determine Register and Value
            # HALT
            if op == 0b010001:
                rs = str(0).zfill(5)
                rt = str(0).zfill(5)
                imm = str(0).zfill(16)
            # JR
            elif op == 0b010000:
                rs = r_check(op_list[1])
                rt = str(0).zfill(5)
                imm = str(0).zfill(16)
            # BEQ
            elif op == 0b001111:
                rs = r_check(op_list[1][:-1])
                rt = r_check(op_list[2][:-1])
                imm = bin(imm_check(op_list[3])).replace("0b","").zfill(16)
            # BZ
            elif op == 0b001110:
                rs = r_check(op_list[1][:-1])
                rt = str(0).zfill(5)
                imm = bin(imm_check(op_list[2])).replace("0b","").zfill(16)
            # STW
            elif op == 0b001101:
                rs = r_check(op_list[2][:-1])
                rt = r_check(op_list[1][:-1])
                imm = bin(imm_check(op_list[3])).replace("0b","").zfill(16)
            # LDW
            elif op == 0b001100:
                rs = r_check(op_list[2][:-1])
                rt = r_check(op_list[1][:-1])
                imm = bin(imm_check(op_list[3])).replace("0b","").zfill(16)
            else:
                rs = r_check(op_list[2][:-1])
                rt = r_check(op_list[1][:-1])
                imm = bin(imm_check(op_list[3])).replace("0b","").zfill(16)
            # Convert to the correct format for memory image
            trace = bin(op).replace("0b","").zfill(6) + rs + rt + imm
            trace = hex(int(trace.ljust(32, "0"),2)).replace("0x","").zfill(8)

            # Write to file 
            # Debug
            print(trace)
            trace = trace + "\n"
            # Write to file
            o_file.write(trace)
    mem_occ = len(command)
    for i in range(mem_occ, 1023):
        o_file.write("00000000\n")
    o_file.write("00000000")
    o_file.close()
            
        
if __name__ == '__main__':
    # Start by checking length of parameters
    if (len(sys.argv) < 3):
        print("Too few arguments")
        exit(1)
    
    # Open the file taken as command line argument
    f = open(sys.argv[1], 'r')

    # Read all the lines as string -- skip blank lines
    command_list = [line for line in f.readlines() if line.strip() and not line.startswith('#')]

    # Print to test all commands were picked up
    print(command_list)

    # call function to putput to text file 
    convert_to_mem(sys.argv[2], command_list)

    # close input file 
    f.close()