#!/usr/bin/env python3

"""
cpu.py: MIPS-Lite implementation

Author(s): Atharva Lele <atharva@pdx.edu>
"""

import config
import memory
import logging

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

        # Instantiate memory object
        self.mem = memory.Memory(config.MEM_SIZE)

    # CPU Operation per clock cycle
    def do_cpu_things(self) -> None:
        # Placeholder function for now
        pass
