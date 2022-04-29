#!/usr/bin/env python3

"""
assembler.py: File for testing the project

Author(s): Ayush Srivastava <ayush@pdx.edu>
"""

import sys
def op_code_check(opcode: str):
    switcher = {
        # R Type Instructions
        "ADD": "000000",
        "SUB": "000010",
        "MUL": "000100",
        "OR" : "000110",
        "AND": "001000",
        "XOR": "001010",
        # I Type Instructions 
        "ADDI": "000001",
        "SUBI": "000011",
        "MULI": "000101",
        "ORI ": "000111",
        "ANDI": "001001",
        "XORI": "001011",
        "LDW ": "001100",
        "STW ": "001101",
        "BZ  ": "001110",
        "BEQ ": "001111",
        "JR  ": "010000",
        "HALT": "010001"
    }
    return switcher.get(opcode , "Invalid OP Code")

def convert_to_mem(output: str, command):
    # Extract tokens from list
    for i in command:
        op_list = i.split()
        op = op_code_check(op_list[0])
        print(op)
        


if __name__ == '__main__':
    # Start by checking length of parameters
    if (len(sys.argv) < 3):
        print("Too few arguments")
        exit(1)
    
    # Open the file taken as command line argument
    f = open(sys.argv[1], 'r')

    # Read all the lines as string 
    command_list = f.readlines()

    # Print to test all commands were picked up
    # print(command_list)

    # call function to putput to text file 
    convert_to_mem(sys.argv[2], command_list)