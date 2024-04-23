# ISA Assembler Design (Part 2) to utilize the **pre-processed assembly code** obtained in part 1 and convert it to **machine code**.

# %%
import re
import csv

## Function to read .txt file with pre-processed assembly code
def read_processed(filename):
    '''read each line from a file'''
    asm_inst = list()
    with open(filename, 'r') as f:
        for line in f:
            asm_inst.append([(int(arg) if re.fullmatch("[+-]?[0-9]+",arg) else arg) for arg in line.split()])
    return asm_inst

## Function to print the instructions
def print_asm_inst(inst_asm):
    '''prints list of instructions'''
    print("Assembly Instructions:")
    if len(inst_asm) == 0:
        print(None)
    else:
        for line in inst_asm:
            print(line)

## Read csv file containing the format for each type of instruction
def get_isa(filename):
        isa = dict()
        with open(filename, newline='') as f:
            data = csv.reader(f)
            header = next(data)
            for row in data:
                isa[row[0]] = {header[1]: row[1], header[2]: row[2], header[3]: row[3], header[4]: row[4]}
        return isa

isa = get_isa('rv32im_isa.csv')

## Gets the encoding for the respective instruction
def get_inst_format(inst_name, isa=isa):
    '''gets the instruction's format based on its name'''
    try:
        val = isa[inst_name]['format']
    except:
        raise KeyError(f"Invalid instruction: {inst_name}")
    if val == 'None':
        raise ValueError(f"Instruction '{inst_name}' does not have a format")
    return val

def get_inst_opcode(inst_name, isa=isa):
    '''gets the instruction's opcode based on its name'''
    try:
        val = isa[inst_name]['opcode']
    except:
        raise KeyError(f"Invalid instruction: {inst_name}")
    if val == 'None':
        raise ValueError(f"Instruction '{inst_name}' does not have an opcode")
    return val

def get_inst_funct3(inst_name, isa=isa):
    '''gets the instruction's funct3 based on its name'''
    try:
        val = isa[inst_name]['funct3']
    except:
        raise KeyError(f"Invalid instruction: {inst_name}")
    if val == 'None':
        raise ValueError(f"Instruction '{inst_name}' does not have 'funct3'")
    return val

def get_inst_funct7(inst_name, isa=isa):
    '''gets the instruction's funct7 based on its name'''
    try:
        val = isa[inst_name]['funct7']
    except:
        raise KeyError(f"Invalid instruction: {inst_name}")
    if val == 'None':
        raise ValueError(f"Instruction '{inst_name}' does not have 'funct7'")
    return val



## Convert int to bin (signed 2's C or unsigned)
def get_2c_binary(integer:int, bits=32, is_signed=True):
        '''converts integert to binary size bits.
        If is_signed=True, then converts to 2's Complement binary;
        Otherwise, converts to unsigned binary'''
        limit = 2**(bits)
        if is_signed:
            if (int(integer) < -limit/2) or (int(integer) >= limit/2):
                raise ValueError(f"Value outside of range: {integer}.\nMust be between [{-limit/2}, {limit/2}).")
        else:
            if (int(integer) < 0) or (int(integer) >= limit):
                raise ValueError(f"Value outside of range: {integer}.\nMust be between [0, {limit}).")
        # if no issues:
        return format(int(integer) & (limit-1), f"0{bits}b")

# %%
 # list to store instructions
inst_asm = []

## reads assembly code and stores it in list of lists 'inst_asm' where axis 0 (rows) corresponds 
## to each line in the file and axis 1 (columns) corresponds to each argument in that instruction
filename = "example2_out1.txt"
inst_asm = read_processed(filename)
# inst_asm = [[arg for arg in line.split()] for line in inst_asm]
print_asm_inst(inst_asm)

# %% [markdown]
# function that converts the above instructions from `inst_asm` into machine code.
# 
# _**Note:** python indexing is <u>backwards</u> compared to how we conventionally index in hardware design. This is important to know when implementing the `imm` (immediate) field._
# 
# _**Note:** since immediate values can be <u>negative</u>, we must account for this when converting integers._

# %%
def get_machine_code(inst_asm):
    '''converts the assembly code to machine code'''
    inst_bin = [] # holds the final result after calling the appropriate functions

    for line in inst_asm:
        inst_name = line[0]
        match (get_inst_format(inst_name)):
            
            # R-type
            case 'R':
                # get fields
                opcode = get_inst_opcode(inst_name)
                ## ... add the other fields here ... ##
                funct7 = get_inst_funct7(inst_name)
                funct3 = get_inst_funct3(inst_name)
                rd = get_2c_binary(line[1], 5, is_signed=False)
                rs1 = get_2c_binary(line[2], 5, is_signed=False)
                rs2 = get_2c_binary(line[3], 5, is_signed=False)
                # assemble instruction
                code = str(funct7) + str(rs2) + str(rs1) + str(funct3) + str(rd) + str(opcode)
                #print(code)  ## ... concat the fields into the correct format ... ##
                inst_bin.append(code)  # append machine code to result

            case 'I':
                # get fields
                opcode = get_inst_opcode(inst_name)
                ## ... add the other fields here ... ##
                # funct7 = get_inst_funct7(inst_name)
                funct3 = get_inst_funct3(inst_name)
                rd = get_2c_binary(line[1], 5, is_signed=False)
                rs1 = get_2c_binary(line[2], 5, is_signed=False)
                imm = get_2c_binary(line[3], 12, is_signed=True)
                # assemble instruction
                code = str(imm) + str(rs1) + str(funct3) + str(rd) + str(opcode)
                #print(code)  ## ... concat the fields into the correct format ... ##
                inst_bin.append(code)  # append machine code to result

            case 'S':
                # get fields
                opcode = get_inst_opcode(inst_name)
                ## ... add the other fields here ... ##
                # funct7 = get_inst_funct7(inst_name)
                funct3 = get_inst_funct3(inst_name)
                imm = get_2c_binary(line[3], 12)
                rs1 = get_2c_binary(line[1], 5, is_signed=False)
                rs2 = get_2c_binary(line[2], 5, is_signed=False)
                # assemble instruction
                code = str(imm[0:7]) + str(rs2) + str(rs1) + str(funct3) + str(imm[7:12]) + str(opcode)
                #print(code)  ## ... concat the fields into the correct format ... ##
                inst_bin.append(code)  # append machine code to result

            case 'B':
                # get fields
                opcode = get_inst_opcode(inst_name)
                ## ... add the other fields here ... ##
                # funct7 = get_inst_funct7(inst_name)
                funct3 = get_inst_funct3(inst_name)
                imm = get_2c_binary(line[3], 13)
                rs1 = get_2c_binary(line[1], 5, is_signed=False)
                rs2 = get_2c_binary(line[2], 5, is_signed=False)
                # assemble instruction
                code = str(imm[0:7]) + str(rs2) + str(rs1) + str(funct3) + str(imm[7:12]) + str(opcode)
                #print(code)  ## ... concat the fields into the correct format ... ##
                inst_bin.append(code)  # append machine code to result

            case 'J':
                # get fields
                opcode = get_inst_opcode(inst_name)
                ## ... add the other fields here ... ##
                # funct7 = get_inst_funct7(inst_name)
                # funct3 = get_inst_funct3(inst_name)
                imm = get_2c_binary(line[2], 21)
                rd = get_2c_binary(line[1], 5, is_signed=False)
                # assemble instruction
                code = str(imm[0:20]) + str(rd) + str(opcode)
                #print(code)  ## ... concat the fields into the correct format ... ##
                inst_bin.append(code)  # append machine code to result


            case _:  # Other (default)
                code = "0" * 32  # assemble instruction: NOP
                inst_bin.append(code)  # append machine code to result

    return inst_bin


inst_bin = get_machine_code(inst_asm)
print_asm_inst(inst_bin)

# %% [markdown]
# function to save the processed assembly code to a `.bin` file

# %%
def save_bin(inst_bin, filename):

    '''save each machine code to a file'''
    with open(filename, 'w') as bin_file:
        # Write each binary string to a new line in the file
        for binary_string in inst_bin:
            bin_file.write(binary_string + '\n')

  
save_bin(inst_bin, filename[:-5]+"2.bin")
print("Saved machine code to: ", filename[:-5] + "2.bin")


