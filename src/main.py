#!/usr/bin/env python3

"""
main.py: Driver file for the entire project

Author(s): Atharva Lele <atharva@pdx.edu>
"""

import config
import cpu
import logging

from memory import Memory

# main() - entry point for the simulator
if __name__ == '__main__':
    # Setup logging configuration
    logging.basicConfig(format=config.LOG_FORMAT, level=logging.DEBUG)
    print("ECE586 MIPS-Lite Simulator")

    # Instantiate CPU
    cpu_inst = cpu.MIPS_lite()

    # Main loop
    # while True:
    #     cpu_inst.do_cpu_things()