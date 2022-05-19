#!/usr/bin/env python3

"""
main.py: Driver file for the entire project

Author(s): Atharva Lele <atharva@pdx.edu>
"""

import config
import cpu
import logging
import os
import sys

# main() - entry point for the simulator
if __name__ == '__main__':
    # Make sure number of arguments is correct
    if len(sys.argv) < 5:
        print("Error! Please run the program using the correct arguments: \n")
        print("./mips_sim <memory_image> <output_file> <debug_level> <mode>")
        print("\nDebug level can be: RELEASE, DEBUG, INFO")
        print("Mode can be: FUNC, NO-FWD, FWD")
        exit(1)

    # Grab memory image filename
    memory_image_fname = sys.argv[1]

    # Check if memory image file exists
    if not os.path.exists(memory_image_fname):
        print("Memory image file not found! Please check the path.")
        exit(1)
    
    # Grab output filename
    output_fname = sys.argv[2]

    # Setup logging configuration
    debug_arg = sys.argv[3].lower()

    # Set default debug level
    debug_level = logging.DEBUG
    
    if debug_arg == 'release':
        debug_level = logging.ERROR
    elif debug_arg == 'debug':
        debug_level = logging.DEBUG
    elif debug_arg == 'info':
        debug_level = logging.INFO
    else:
        print("Incorrect format for debug level. Please use: RELEASE, DEBUG or INFO")
        exit(1)
    
    # Set debugging level
    logging.basicConfig(format=config.LOG_FORMAT, level=debug_level)

    # Grab simulator mode
    modes = ['func', 'no-fwd', 'fwd']
    sim_mode = sys.argv[4].lower()
    if sim_mode not in modes:
        print("Incorrect format for mode. Please use: FUNC, NO-FWD, FWD")
        exit(1)

    # Instantiate CPU
    cpu_inst = cpu.MIPS_lite(sim_mode, memory_image_fname, output_fname)

    # Main loop
    while True:
        if (debug_arg == 'debug'):
            step = input('')
        
        # CPU Loop
        halt = cpu_inst.do_cpu_things()
        if halt == True:
            break