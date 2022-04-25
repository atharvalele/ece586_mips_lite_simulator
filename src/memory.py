#!/usr/bin/env python3

"""
memory.py: Memory image and read/write functions

Author(s): Atharva Lele <atharva@pdx.edu>
"""

import config
import logging

class Memory:
    # byte array to hold memory contents
    mem = bytearray()
    
    # Initialize memory with given size
    def __init__(self, size=config.MEM_SIZE) -> None:
        self.size = size
        self.mem = bytearray(self.size)
        logging.debug("Initialized memory with size = " + str(len(self.mem)))

    # Read a byte from memory
    def read(self, addr: int) -> int:
        # Make sure address is within range
        assert addr < self.size, "Address out of range"
        # Return the data at addr
        return self.mem[addr]

    # Read n bytes from memory
    def read_n(self, addr: int, n: int) -> bytearray:
        # Make sure address is within range
        assert (addr+n) < self.size, "Address out of range"
        # Return the data at addr
        data = self.mem[addr:addr+n]
        return data
    
    # Write a byte to memory
    def write(self, addr: int, data: int) -> None:
        # Make sure address is within range
        assert addr < self.size, "Address out of range"
        # Make sure the data fits in a byte
        assert data <= 255, "Data is too big for a byte"
        # Write the byte into memory
        self.mem[addr] = data

    # Write n bytes to memory
    def write_n(self, addr: int, data: bytearray) -> None:
        l = len(data)
        # Make sure address is within range
        assert (addr+l) < self.size, "Address out of range"
        # Make sure data isn't larger than memory size
        assert l <= self.size
        # Write the bytearray into memory
        self.mem[addr:addr+len(data)] = data

