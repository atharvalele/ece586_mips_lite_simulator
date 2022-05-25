# Save address in R6
ADDI R6, R0, 1000

# Save jump location in R7
ADDI R7, R7, 20

# R5 = 0
ADDI R5, R5, 0

# R4 = 5
ADDI R5, R5, 5

# Decrement R4 by 1 and save in R3
SUBI R3, R4, 1

# Multiply 
MUL R2, R3, R4

# Decrement R3 by 1
SUBI R3, R3, 1

# R3 == 0, branch to store
BEQ R3, R5, 2

# Multiply and save result in R2
MUL R2, R2, R3

# jump to beginning
JR R7

# Addr 1000 = R2
STW R2, R6, 0

