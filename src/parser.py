#!/usr/bin/env python3

"""
parser.py: Parsing memory image

Author(s): Shivani Palkar <spalkar@pdx.edu>
"""

def parser(mem_image: str) -> bytearray:
    image = bytearray()
    mem_file = open(mem_image, "r")

    for string in mem_file:
        to_byte = bytearray.fromhex(string)
        image += to_byte
    
    # Close file
    mem_file.close()
    
    return image
