# Save Address in R4
ADDI R4, R0, 1000

# Save jump location in R5
ADDI R5, R5, 20

# R1 = 0
ADDI R1, R1, 0

# R2 = 0
ADDI R2, R2, 0

# R3 = 11
ADDI R3, R3, 11

# R2 = R2 + R1
ADD R2, R2, R1

# R1 = R1 + 1
ADDI R1, R1, 1

# If R1 == 11, branch to STORE
BEQ R3, R1, 2

# Go back to beginning
JR R5

# Addr 1000 = R2
STW R2, R4, 0

# STOP
HALT