#!/usr/bin/env python3

"""
main.py: Driver file for the entire project

Author(s): Atharva Lele <atharva@pdx.edu>
"""

import config
import cpu
import cpu_func
import logging
import os
import sys

# main() - entry point for the simulator
if __name__ == '__main__':
    # Make sure number of arguments is correct
    if len(sys.argv) < 4:
        print("Error! Please run the program using the correct arguments: \n")
        print("./mips_sim <memory_image> <debug_level> <mode>")
        print("\nDebug level can be: RELEASE, DEBUG, INFO")
        print("Mode can be: FUNC, NO-FWD, FWD")
        exit(1)

    # Grab memory image filename
    memory_image_fname = sys.argv[1]

    # Check if memory image file exists
    if not os.path.exists(memory_image_fname):
        print("Memory image file not found! Please check the path.")
        exit(1)

    # Setup logging configuration
    debug_arg = sys.argv[2].lower()

    # Set default debug level
    debug_level = logging.DEBUG
    
    if debug_arg == 'release':
        debug_level = logging.ERROR
    elif debug_arg == 'debug':
        debug_level = logging.DEBUG
    else:
        print("Incorrect format for debug level. Please use: RELEASE or DEBUG")
        exit(1)
    
    # Set debugging level
    logging.basicConfig(format=config.LOG_FORMAT, level=debug_level)

    # Grab simulator mode
    modes = ['func', 'no-fwd', 'fwd']
    sim_mode = sys.argv[3].lower()
    if sim_mode not in modes:
        print("Incorrect format for mode. Please use: FUNC, NO-FWD, FWD")
        exit(1)

    # Instantiate CPU
    if sim_mode == 'func':
        cpu_inst = cpu_func.MIPS_lite_func(memory_image_fname)
    else:
        cpu_inst = cpu.MIPS_lite(sim_mode, memory_image_fname)

    # Main loop
    while True:
        if (debug_arg == 'debug'):
            step = input('Press any key to run for 1 more clock cycle')
        
        # CPU Loop
        halt = cpu_inst.do_cpu_things()
        if halt == True:
            break

    # Sort modified lists
    cpu_inst.modified_addrs.sort()
    cpu_inst.modified_regs.sort()
    
    # Print instruction counts
    print('Instruction Counts:')
    print(f'\nTotal Instructions: {cpu_inst.instr_count}')
    print(f'Arithmetic Instructions: {cpu_inst.arithmetic_instr_count}')
    print(f'Logical Instructions: {cpu_inst.logical_instr_count}')
    print(f'Memory Access Instructions: {cpu_inst.mem_instr_count}')
    print(f'Control Transfer Instructions: {cpu_inst.cntrl_instr_count}')

    # Print modified registers
    print('\nFinal Register State:')
    print(f'PC: {cpu_inst.pc}')
    for reg in cpu_inst.modified_regs:
        print(f'R{reg}: {cpu_inst.R[reg]}')
    
    # Print stalls
    if sim_mode != 'func':
        print(f'\nTotal stalls: {cpu_inst.stall_count}')
        print(f'Number of Data Hazards: {cpu_inst.num_data_hazards}')

    # Print modified addresses
    print('\nModified Addresses:')
    for addr in cpu_inst.modified_addrs:
        # Get 4 bytes from memory
        d_array = cpu_inst.mem.read_n(addr, 4)

        # 'big' here means that that first byte in the array is MSB
        data = int.from_bytes(bytes=d_array, byteorder='big', signed=False)

        print(f'Addr: {addr}, Data: {data}')
    
    # Print total clock cycles
    if sim_mode != 'func':
        print(f'\nTotal clock cycles: {cpu_inst.clk}')