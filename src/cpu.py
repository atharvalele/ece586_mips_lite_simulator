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
    def __init__(self) -> None:
        # Clock cycle counter
        self.clk = 0

        # Instantiate memory object
        self.mem = memory.Memory(config.MEM_SIZE)

    # CPU Operation per clock cycle
    def do_cpu_things(self) -> None:
        # Placeholder function for now
        pass
