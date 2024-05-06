# %% [markdown]
# ISA Assembler Design (Part 3) to take the **assembly code** given in part 1, detect any potential data hazards, and then rearrange the sequencing in such a way that data hazards are eliminated while still **maintaining the same computation and output**.

# %% [markdown]
# # Predefined Functions

# %% [markdown]
# ## Functions from previous parts

# %%
import re
import csv

# Function to read the assembly code file #
def read(filename):
    #read each line from a file
    asm_inst = list()
    with open(filename, 'r') as f:
        for line in f:
            asm_inst.append(line)
    return asm_inst


# Function to get the equivalent register's value
def get_reg_value(reg_name):
    #gets the equivalent value for the respective register name
    reg_abi = {"zero": 0,"ra": 1,"sp": 2,"gp": 3,"tp": 4,"t0": 5,"t1": 6,"t2": 7,
               "s0": 8,"s1": 9,"a0": 10,"a1": 11,"a2": 12,"a3": 13,"a4": 14,"a5": 15,
               "a6": 16,"a7": 17,"s2": 18,"s3": 19,"s4": 20,"s5": 21,"s6": 22,"s7": 23,
               "s8": 24,"s9": 25,"s10": 26,"s11": 27,"t3": 28,"t4": 29,"t5": 30,"t6": 31}
    if reg_name[0].lower() in 'x':
        return int(reg_name[1:])
    elif reg_name in reg_abi:
        return reg_abi[reg_name]
    elif reg_name.isdecimal():
        return int(reg_name)
    else:
        raise ValueError(f"Invalid register name/value: {reg_name}")


# FOR TESTING: Function to print the instructions
def print_asm_inst(instructions):
    #prints list of instructions
    print("Assembly Instructions:")
    if len(instructions) == 0:
        print(None)
    else:
        for line in instructions:
            print(line)


# FOR TESTING: Function to print the labels
def print_asm_labels(labels):
    # prints list of labels
    print("Assembly Labels:")
    if len(labels) == 0:
        print(None)
    else:
        max_len = max(5,max([len(label) for label in labels]))
        print(f"{'LABEL':<{max_len}} | {'VALUE':>5}")
        for label, val in labels.items():
            print(f"{label:<{max_len}} | {val:>5}")

def remove_comments(instructions):
    for i in range(len(instructions)):
        instructions[i] = re.sub('#.+', "", instructions[i], flags=re.DOTALL)
    return instructions


def split_arg(instructions):
    for i in range(len(instructions)):
        instructions[i] = re.findall('[a-zA-Z0-9_#:+-]+', instructions[i])
    return instructions


def remove_empty(instructions):
    return [line for line in instructions if len(line)>0]


def loadsave_arg_reorder(instructions):
    for i in range(len(instructions)):
        if instructions[i][0] == 'lw':
            tmp = instructions[i][3]
            instructions[i][3] = instructions[i][2]
            instructions[i][2] = tmp
        elif instructions[i][0] == 'sw':
            tmp = instructions[i][3]
            instructions[i][3] = instructions[i][2]
            instructions[i][2] = instructions[i][1]
            instructions[i][1] = tmp
        else:
            continue
    return instructions


# Gets the type for the respective instruction (removes need for external .csv)
def get_instruction_type(opcode):
  return next((inst_type for inst_type, opcodes in {
    'R': ['add', 'sub', 'mul', 'div', 'sll', 'srl', 'sra', 'or', 'and', 'xor'],
    'I': ['lw', 'addi', 'slli', 'srli', 'srli', 'ori', 'andi', 'xori', 'jalr'],
    'S': ['sw'], 'B': ['beq', 'bne', 'blt', 'bge'],
    'J': ['jal'], 'N': ['nop']}.items() if opcode in opcodes), None)

# %% [markdown]
# ## Task evaluation funcitons

# %%
PINK = '\033[95m'
BLUE = '\033[94m'
CYAN = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
END = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'

def print_instructions(instructions, color="", end_index=-1, single_line=False,end="\n"):
  if color != "":
    print(color, end="")
  if single_line:
    print(instructions, end=end)
  else:
    for i, instruction in enumerate(instructions):
      print(instruction)
      if i == end_index:
        break
  print(END, end="")

def printSubsets(subsets, color=""):
  if color != "":
    print(color, end="")
  for i, subset in enumerate(subsets):
    print(str(i+1)+".", end="")
    for line in subset:
      print("\t"+str(line))
    print()
  print(END)

# %%
# FOR TESTING: Function to test task 1
def t1_test():
  instructions = [
    ['main:'],
    ['lw', 'x4', 'x0', '16'],
    ['add', 'x5', 'x2', 'x4'],
    ['sub', 'x7', 'x3', 'x6'],
    ['loop:'],
    ['sw', 'x5', 'x0', '32'],
    ['lw', 'x4', 'x0', '16'],
    ['addi', 'x9', 'x1', 'x4'],
    ['bne', 'x9', 'x1', 'x4'],
    ['lw', 'x4', 'x0', '16'],
    ['add', 'x5', 'x1', 'x4'],
    ['j', 'x5'],
    ['sw', 'x5', 'x0', '32']
  ]

  correct = [
    [['main:']],
    [['lw', 'x4', 'x0', '16'],
    ['add', 'x5', 'x2', 'x4'],
    ['sub', 'x7', 'x3', 'x6']],
    [['loop:']],
    [['sw', 'x5', 'x0', '32'],
    ['lw', 'x4', 'x0', '16'],
    ['addi', 'x9', 'x1', 'x4'],
    ['bne', 'x9', 'x1', 'x4']],
    [['lw', 'x4', 'x0', '16'],
    ['add', 'x5', 'x1', 'x4'],
    ['j', 'x5']],
    [['sw', 'x5', 'x0', '32']]
  ]

  print("Testing "+YELLOW+"splitAssemblyIntoSubsets()"+END+" with:"+PINK)
  for line in instructions:
    print("\t"+str(line))
  print(END+"\nCorrect answer: ")
  printSubsets(correct, GREEN)
  returned = splitAssemblyIntoSubsets(instructions)
  color = GREEN if returned == correct else RED
  print("Returned answer: ")
  printSubsets(returned, color)

# %%
# FOR TESTING: Function to test task 2
def t2_test():
  instructions = [
    ['lw', 'x4', 'x0', '16'],
    ['add', 'x5', 'x1', 'x4'],
    ['add', 'x5', 'x1', 'x4'],
    ['sw', 'x5', 'x0', '32']
  ]

  #test get_operands()
  print("Testing "+YELLOW+"get_operands()"+END+" with:")
  print_instructions(instructions[0], PINK, single_line=True)
  correct = "('x4', 'x0')"
  print("Correct answer: ")
  print_instructions(correct, GREEN, single_line=True)
  returned = get_operands(instructions[0])
  color = GREEN if str(returned) == correct else RED
  print("Returned answer: ")
  print_instructions(returned, color, single_line=True)
  print()

  #test get_rd()
  print("Testing "+YELLOW+"get_rd()"+END+" with:")
  print_instructions(instructions[0], PINK, single_line=True)
  correct = "x4"
  print("Correct answer: ")
  print_instructions(correct, GREEN, single_line=True)
  returned = get_rd(instructions[0])
  color = GREEN if str(returned) == correct else RED
  print("Returned answer: ")
  print_instructions(returned, color, single_line=True)
  print()


  #test get_rs()
  print("Testing "+YELLOW+"get_rs()"+END+" with:")
  print_instructions(instructions[0], PINK, single_line=True)
  correct = "x0"
  print("Correct answer: ")
  print_instructions(correct, GREEN, single_line=True)
  returned = get_rs(instructions[0])
  color = GREEN if str(returned) == correct else RED
  print("Returned answer: ")
  print_instructions(returned, color, single_line=True)
  print()


  #test are_data_dependent()
  print("Testing "+YELLOW+"are_data_dependent()"+END+" with:\n"+PINK, end="")
  print_instructions(instructions, PINK, 1)
  correct = "True"
  print("Correct answer: ")
  print_instructions(correct, GREEN, single_line=True)
  returned = are_data_dependent(instructions[0], instructions[1])
  color = GREEN if str(returned) == correct else RED
  print("Returned answer: ")
  print_instructions(returned, color, single_line=True)

# %%
# FOR TESTING: Function to test task 3
def t3_test():
  instructions = [
    ['lw', 'x2', 'x0', '16'],
    ['addi', 'x4', 'x6', '37'],
    ['sub', 'x5', 'x1', 'x4'],
    ['add', 'x5', 'x1', 'x4'],
    ['sw', 'x5', 'x0', '32']
  ]

  instructions2 = [
    ['lw', 'x8', 'x9', '42'],
    ['add', 'x7', 'x7', 'x9'],
    ['sub', 'x8', 'x6', 'x10'],
    ['mul', 'x6', 'x0', 'x3'],
    ['add', 'x3', 'x1', 'x4'],
    ['beq', 'x2', 'x3', 'loop']
  ]

  #test find_above_instruction_without_dependencies()
  index = 2
  print("Testing "+YELLOW+"find_above_instruction_without_dependencies()"+END+" with:\n", end="")
  print_instructions(instructions, PINK, index)
  correct = 0
  if correct is not False:
    print("Correct answer: "+GREEN+str(correct)+END + " ("+str(instructions[correct])+")")
  else:
    print("Correct answer: "+GREEN+str(correct)+END)
  returned = find_above_instruction_without_dependencies(instructions, index)
  color = GREEN if returned is correct else RED
  if returned is not False:
    print("Returned answer: "+GREEN+str(returned)+END + " ("+str(instructions[returned])+")")
  else:
    print("Returned answer: "+GREEN+str(returned)+END)
  print()

  #test find_above_instruction_without_dependencies()
  index = 4
  print("Testing "+YELLOW+"find_above_instruction_without_dependencies()"+END+" with:\n", end="")
  print_instructions(instructions, PINK, index)
  correct = 0
  if correct is not False:
    print("Correct answer: "+GREEN+str(correct)+END + " ("+str(instructions[correct])+")")
  else:
    print("Correct answer: "+GREEN+str(correct)+END)
  returned = find_above_instruction_without_dependencies(instructions, index)
  color = GREEN if returned is correct else RED
  if returned is not False:
    print("Returned answer: "+GREEN+str(returned)+END + " ("+str(instructions[returned])+")")
  else:
    print("Returned answer: "+GREEN+str(returned)+END)
  print()

  #test find_above_instruction_without_dependencies()
  index = 1
  print("Testing "+YELLOW+"find_above_instruction_without_dependencies()"+END+" with:\n", end="")
  print_instructions(instructions, PINK, index)
  correct = False
  if correct is not False:
    print("Correct answer: "+GREEN+str(correct)+END + " ("+str(instructions[correct])+")")
  else:
    print("Correct answer: "+GREEN+str(correct)+END)
  returned = find_above_instruction_without_dependencies(instructions, index)
  color = GREEN if returned is correct else RED
  if returned is not False:
    print("Returned answer: "+color+str(returned)+END + " ("+str(instructions[returned])+")")
  else:
    print("Returned answer: "+GREEN+str(returned)+END)
  print()


  #test find_above_instruction_without_dependencies()
  index = 5
  print("Testing "+YELLOW+"find_above_instruction_without_dependencies()"+END+" with:\n", end="")
  print_instructions(instructions2, PINK, index)
  correct = 1
  if correct is not False:
    print("Correct answer: "+GREEN+str(correct)+END + " ("+str(instructions2[correct])+")")
  else:
    print("Correct answer: "+GREEN+str(correct)+END)
  returned = find_above_instruction_without_dependencies(instructions2, index)
  color = GREEN if returned is correct else RED
  if returned is not False:
    print("Returned answer: "+GREEN+str(returned)+END + " ("+str(instructions2[returned])+")")
  else:
    print("Returned answer: "+GREEN+str(returned)+END)

# %%
def move_instruction_above_index(instructions, target_index, source_index):
  # Get the instruction to move
  instruction_to_move = instructions.pop(source_index)
  # Adjust the target index if necessary
  if target_index > source_index:
      target_index -= 1
  # Insert the instruction at the target index
  instructions.insert(target_index, instruction_to_move)
  return instructions


# FOR TESTING: Function to test task 4
def t4_test():
  instructions = [
    ['lw', 'x4', 'x0', '16'],
    ['add', 'x5', 'x1', 'x4'],
    ['add', 'x5', 'x1', 'x4'],
    ['sw', 'x5', 'x0', '32']
  ]

  #test move_instruction_above_index()
  target_idx, instr_to_move = 1,3
  print("Testing "+YELLOW+"get_operands()"+END+" with:")
  print_instructions(instructions, PINK)
  correct = [['lw', 'x4', 'x0', '16'], ['sw', 'x5', 'x0', '32'], ['add', 'x5', 'x1', 'x4'], ['add', 'x5', 'x1', 'x4']]
  print("\nCorrect answer:")
  print_instructions(correct, GREEN)
  returned = move_instruction_above_index(instructions, target_idx, instr_to_move)
  color = GREEN if returned == correct else RED
  print("\nReturned answer:")
  print_instructions(correct, color)
  print(END)

# %%
def t5_test():
  instructions = [
    ['lw', 'x1', 'x0', '0'],
    ['lw', 'x2', 'x0', '8'],
    ['add', 'x3', 'x1', 'x2'],
    ['sw', 'x3', 'x0', '24'],
    ['lw', 'x4', 'x0', '16'],
    ['add', 'x5', 'x1', 'x4'],
    ['sw', 'x5', 'x0', '32']
  ]

  #test reorder_instructions()
  print("Testing "+YELLOW+"reorder_instructions()"+END+" with:")
  print_instructions(instructions, PINK)
  correct = [['lw', 'x1', 'x0', '0'],['lw', 'x2', 'x0', '8'],['lw', 'x4', 'x0', '16'],['add', 'x3', 'x1', 'x2'],['add', 'x5', 'x1', 'x4'],['sw', 'x3', 'x0', '24'],['sw', 'x5', 'x0', '32']]
  print("\nCorrect answer:")
  print_instructions(correct, GREEN)
  returned = reorder_instructions(instructions)
  color = GREEN if returned == correct else RED
  print("\nReturned answer:")
  print_instructions(returned, color)
  print(END)

# %%
def t6_test(filename):
  correct =[
    ['load_use1:'],
    ['lw', 't1', 't1', '12'],
    ['sub', 't8', 't6', 't7'],
    ['add', 't5', 't1', 't7'],
    ['or', 't9', 't6', 't7'],
    ['load_use2:'],
    ['lw', 't1', 't1', '12'],
    ['or', 't9', 't6', 't7'],
    ['add', 't5', 't1', 't7'],
    ['sub', 't1', 't6', 't7'],
    ['no_dep:'],
    ['lw', 't0', 't1', '12'],
    ['add', 't5', 't6', 't7'],
    ['sub', 't2', 't0', 's1'],
    ['or', 's5', 's6', 't6'],
    ['alu_then_branch:'],
    ['sub', 's3', 's3', 't0'],
    ['add', 't0', 't1', 't2'],
    ['sub', 't3', 't4', 't5'],
    ['beq', 't0', 't5', 'loop'],
    ['load_then_branch:'],
    ['add', 't4', 't6', 't7'],
    ['lw', 't0', 't1', '0'],
    ['sub', 't2', 't3', 's1'],
    ['beq', 't0', 't5', 'loop'],
    ['fix_no_steal:'],
    ['lw', 't0', 't1', '12'],
    ['add', 't5', 't0', 't7'],
    ['or', 's5', 't0', 't6'],
    ['sub', 't2', 't4', 't6'],
    ['add', 's3', 's5', 's6'],
    ['handshake:'],
    ['lw', 't0', 't1', '12'],
    ['sub', 's5', 't4', 't6'],
    ['or', 's5', 't7', 't6'],
    ['add', 't5', 't0', 't7'],
    ['add', 's3', 's5', 's6']]

  # catching up to where this would inject into Lab #03
  instructions = read(filename)
  instructions = remove_comments(instructions)
  instructions = split_arg(instructions)
  instructions = remove_empty(instructions)
  instructions = loadsave_arg_reorder(instructions)

  # split the instructions into subsets
  subsets = splitAssemblyIntoSubsets(instructions)

  # loop through the subsets and reorder the instructions to avoid data dependencies
  reordered_instructions = []
  for subset in subsets:
    # for labels or single or a pair of instructions
    if len(subset) <= 2:
      reordered_instructions += subset
    # subsets with more than two instructions
    else:
      reordered_instructions += reorder_instructions(subset)

  for line in reordered_instructions:
    print(line[0], ', '.join(line[1:]))

  # print("Original\t\t\tReordered")

  # for i in range(len(instructions)):
  #   print_instructions(instructions[i], PINK, single_line=True, end="")
  #   if instructions[i][0] in {"no_dep:", "load_use1:","load_use2:","handshake:"}: #i don't have time for this..
  #     print("\t\t\t", end="")
  #   elif len(''.join(str(instructions[i]))) < 24:
  #     print("\t\t", end="")
  #   else:
  #     print("\t", end="")
  #   color = GREEN if reordered_instructions[i] == correct[i] else RED
  #   print_instructions(reordered_instructions[i], color, single_line=True)
  # print()



# %%
#@title
filename = "example.asm" #@param {type:"string"}
# filename = "example.asm"

# %%
#@title Assembly Instructions loaded from `filename`
# catching up to where this would inject into the workflow of Lab #03
instructions = read(filename)
instructions = remove_comments(instructions)
instructions = split_arg(instructions)
instructions = remove_empty(instructions)
instructions = loadsave_arg_reorder(instructions)
# print instructions after processing from Lab #03 is performed
print_asm_inst(instructions)

# %% [markdown]
# The function `splitAssemblyIntoSubsets()` splits `instructions` into `subsets`, starting a new `subset` after instructions that **cannot** be reordered. These instructions include:
# - Branch instructions: `beq`, `bne`, `blt`, `bge`
# - Jump instructions: `j`, `jal`
# - Labels: `main:`, `loop:`, *etc.*
# <br><br>
# 
# ###<span style="color:black; background-color:#C5E0B4; border: 1px solid; padding: 5px;">***Complete the function `splitAssemblyIntoSubsets()`.***</span>

# %%
def splitAssemblyIntoSubsets(instructions):
  subsets = []
  subset = []

  for instruction in instructions:
    # your code here -------------------------------
    if re.search(":$", instruction[0]):
        if len(subset) > 0:
          subsets.append(list(subset))
          subset.clear()
          subset.append(instruction)
          subsets.append(list(subset))
          subset.clear()
          continue
        else:
          subset.append(instruction)
          subsets.append(list(subset))
          subset.clear()
          continue

    subset.append(instruction)
    if re.search("^b", instruction[0]) or re.search("^j", instruction[0]):
      subsets.append(list(subset))
      subset.clear()
  subsets.append(list(subset))
  # ----------------------------------------------

  # return list of subsets or original instructions if there were no subsets found
  return subsets if subsets else instructions

# %% [markdown]
# test output

# %%
t1_test()

# %% [markdown]
# The function `get_operands()` returns the `rd` and `rs` values of an instruction.
# 
# The function `are_data_dependent()` checks if `instruction_A` has data dependencies in `instruction_B`.<br><br>
# 
# ### <span style="color:black; background-color:#C5E0B4; border: 1px solid; padding: 5px;">**Complete the functions `get_operands()` and `are_data_dependent()`.**</span>

# %%
def get_operands(instruction):
  instruction_type = get_instruction_type(instruction[0])
  rd, rs = " ", " "

  # this could be rewritten using a match statement if Google used a recent python version..
  if instruction_type == 'I':
# your code here -------------------------------
    rd = instruction[1]
    rs = instruction[2]

  elif instruction_type == 'R': # Don't change
    rd = instruction[1]
    rs = [instruction[2], instruction[3]]

  elif instruction_type == 'S' or instruction_type == 'B': # Don't change
    rs = [instruction[1], instruction[2]]

  elif instruction_type == 'J': # Don't change
    rd = instruction[1]

# your code here -------------------------------

  return rd, rs

# wrapper function for get_operands()
def get_rd(instruction):
  return get_operands(instruction)[0]

# wrapper function for get_operands()
def get_rs(instruction):
  return get_operands(instruction)[1]


# check if rd of instructionA is in rs of instructionB
def are_data_dependent(instruction_A,instruction_B):
  # your code here -------------------------------
  return get_rd(instruction_A) in get_rs(instruction_B)


# %% [markdown]
# output of `get_operands()` and `are_data_dependent()`.

# %%
t2_test()

# %% [markdown]
# The function `find_above_instruction_without_dependencies()` scans a `subset` upward (from bottom to top) until an `instruction` with no data dependencies is found. This alone will not be enough to sufficiently check the `subset` for suitable instructions to swap, because when a suitable instruction is not found searching bottom to top, the search must be repeated from top to bottom. <br><br>
# 
# ### <span style="color:black; background-color:#C5E0B4; border: 1px solid; padding: 5px;">**Complete `find_above_instruction_without_dependencies()`.**</span>
# 
# <br><br>_**Note**: When checking whether or not an instruction is truly dependency-free, we must check in both directions (i.e., `instruction_A` against `instruction_B` **and** `instruction_B` against `instruction_A`._
# 
# _The bidirectional check only applies to the intermediate instructions (`intermediate_index`) but not the current instruction (`current_index`). The current instruction is always below the test instruction (`test_index`), even after swapping. Thus, you only need to compare the `rd` of the test instruction with the `rs` of the current instruction._

# %%
  # search instructions (upward from current index) for instruction with no data dependencies
def find_above_instruction_without_dependencies(instructions, current_index):
    # your code here -------------------------------
    a_inst = instructions[current_index]   # Get instructions

    for index_t in reversed(range(0, current_index - 1)):   # Iterate the instructions
      t_inst = instructions[index_t]
      if t_inst[0][0] in {'b', 'j'}: # Check if the instruction is jomp or branch
        continue # Continue if it is

      if are_data_dependent(t_inst, a_inst):  # check if register destination is used in current instruction
        continue  # Continue if it exist

      found_dependency = False
      for int_index in range(index_t + 1, current_index):
        intermediate_instruction = instructions[int_index]
        if are_data_dependent(intermediate_instruction, t_inst) or are_data_dependent(t_inst, intermediate_instruction):
          found_dependency = True # Dependency Found
          break
      # ----------------------------------------------
      # if no data dependency is found, test index is last index where instruction can be safely injected
      if not found_dependency:
        return index_t

    # if no safe index is found, return False
    return False

# %%


# %%
# search instructions (downward from current index) for instruction with no data dependencies
def find_below_instruction_without_dependencies(instructions, current_index):
  # get the instruction at prev index
  prev_instruction = instructions[current_index-1]

  # iterate over previous instructions from current index up to beginning of instructions
  for test_index in range(current_index + 1, len(instructions)):
    # get instruction to test if it has data dependencies
    test_instruction = instructions[test_index]

    # check if test instruction is a branch or jump
    if test_instruction[0][0] in {'b', 'j'}:
      continue

    # check if register destination of previous instruction is used in register sources of test instruction
    if are_data_dependent(prev_instruction, test_instruction):
      continue  # data dependency exists, continue searching

    # iterate over instructions between current instruction index (inclusive) and test index (exclusive) to check if there are data dependencies with test instruction
    found_dependency = False
    for intermediate_index in range(current_index, test_index):
      intermediate_instruction = instructions[intermediate_index]
      # if there are dependencies detected between instructions (in either direction), there is a dependency
      if are_data_dependent(intermediate_instruction, test_instruction) or are_data_dependent(test_instruction, intermediate_instruction):
        found_dependency = True
        break

    # if no data dependency is found, test index is last index where instruction can be safely injected
    if not found_dependency:
      return test_index

  # if no safe index is found, return False
  return False

# %% [markdown]
# output of `find_above_instruction_without_dependencies()`.

# %%
t3_test()

# %% [markdown]
# 

# %%
def move_instruction_above_index(instructions, target_index, source_index):
  # Get the instruction to move
  instruction_to_move = instructions.pop(source_index)
  # Adjust the target index if necessary
  if target_index > source_index:
      target_index -= 1
  # Insert the instruction at the target index
  instructions.insert(target_index, instruction_to_move)
  return instructions

# %% [markdown]
# The above function moves the dependency-free `instruction` we found between the two instructions found to have a data dependency
# 
# test output of `move_instruction_above_index()`.

# %%
t4_test()

# %% [markdown]
# The function `reorder_instructions()` reorders instructions in a `subset` to avoid data hazards and stalls.
# 
# <br>In order to accomplish this, the function must:
# - loop through the `subset` in reverse (bottom to top)
# - during each iteration of the loop:
#   - check if the instructions at the **current** and **previous** index `are_data_dependent()`<br>_(i.e., if the current instruction has a data dependency on the instruction above it)_
#   - if you discover an `instruction` with a data dependency during your traversal:
#     -  `find_above_instruction_without_dependencies()` in the **remaining** `subset`
#     - if an `instruction` without dependencies is found:
#       - `move_instruction_above_index()` of the `instruction` with the data dependency
#     - if an `instruction` without dependencies is **not** found:
#       - from the top of the`subset`, `find_below_instruction_without_dependencies()` until just before the **current** index
# 
# - once the loop has completed, return the reordered `subset`
# <br><br>
# 
# 
# ### <span style="color:black; background-color:#C5E0B4; border: 1px solid; padding: 5px;">**Complete the function `reorder_instructions()`.**</span>
# 
# 
# 
# <br/><br/>**_Note:_**
# _Searching **top to bottom** will use a truncated version of the `subset`, i.e., `instructions[:max_index]`_
# 
# _Recall that when indexing through the `subset` of instructions that `0` is a possible index._
# 
# _Recall that python treats `False` and `0` as equivalent values. e.g., `print(0==False)` returns `True`._

# %%
def reorder_instructions(instructions):
  # variable to store truncation point
  max_index = len(instructions)

  for current_index in reversed(range(1, len(instructions))):
# your code here -------------------------------
    current_instruction = instructions[current_index]
    previous_instruction = instructions[current_index - 1]

    if are_data_dependent(previous_instruction, current_instruction):
      test_instruction_index = find_above_instruction_without_dependencies(instructions, current_index)

      if test_instruction_index is False: # If not found
        test_instruction_index = find_below_instruction_without_dependencies(instructions[:max_index], current_index)

      if test_instruction_index is not False: # If one is found
        instructions = move_instruction_above_index(instructions, current_index, test_instruction_index)
        max_index = current_index - 1 # Update
# ----------------------------------------------

  return instructions

# %% [markdown]
#  output of `reorder_instructions()`.

# %%
t5_test()

# %% [markdown]
# 

# %% [markdown]
# The function below loops through all `subsets` and runs `reorder_instructions()` from Task 5 on each `subset` until the entire original set of instructions loaded from `fiilename` has been processed.
# 
# 

# %%
#@title
filename = "example.asm" #@param {type:"string"}
# filename = "example.asm"

# %%
t6_test(filename)

# %%
!pwd
!ls

# %%



