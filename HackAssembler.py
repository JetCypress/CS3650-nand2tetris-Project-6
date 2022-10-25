import os
import sys


class Parser:

    def __init__(self, file_name: str):
        #opens file and removes coments, empty lines, and whitespace.
        self.cmd = ""
        self.current = -1
        self.commands = []
        file = open(file_name)
        for line in file:
            line = line.partition("//")[0]
            line = line.strip()
            line = line.replace(" ", "")
            if line:
                self.commands.append(line)
        file.close()

    def hasMoreCommands(self) -> bool:
        return (self.current + 1) < len(self.commands)

    def advance(self) -> None:
        self.current += 1
        self.cmd = self.commands[self.current]

    def restart(self) -> None:
        self.cmd = ""
        self.current = -1

    def commandType(self) -> str:
        if self.cmd[0] == "@":
            return "A"
        elif self.cmd[0] == "(":
            return "L"
        else:
            return "C"

    def symbol(self) -> str:
        if self.commandType() == "A":
            return self.cmd[1:]
        if self.commandType() == "L":
            return self.cmd[1:-1]
        return ""

    def dest(self) -> str:
        if self.commandType() == "C":
            if "=" in self.cmd:
                return self.cmd.partition("=")[0]
        return ""

    def comp(self) -> str:
        if self.commandType() == "C":
            tmp = self.cmd
            if "=" in tmp:
                tmp = tmp.partition("=")[2]
            return tmp.partition(";")[0]
        return ""

    def jump(self) -> str:
        if self.commandType() == "C":
            tmp = self.cmd
            if "=" in tmp:
                tmp = tmp.partition("=")[2]
            return tmp.partition(";")[2]
        return ""


class Code:
    #converts the symbols to machine code.

    def __init__(self):
        #table for destinations.
        self.d_table = {
            "": "000",
            "M": "001",
            "D": "010",
            "MD": "011",
            "A": "100",
            "AM": "101",
            "AD": "110",
            "AMD": "111"
        }

        #table for comparisons.
        self.c_table = {
            "0": "0101010",
            "1": "0111111",
            "-1": "0111010",
            "D": "0001100",
            "A": "0110000",
            "M": "1110000",
            "!D": "0001101",
            "!A": "0110001",
            "!M": "1110001",
            "-D": "0001111",
            "-A": "0110011",
            "-M": "1110011",
            "D+1": "0011111",
            "A+1": "0110111",
            "M+1": "1110111",
            "D-1": "0001110",
            "A-1": "0110010",
            "M-1": "1110010",
            "D+A": "0000010",
            "D+M": "1000010",
            "D-A": "0010011",
            "D-M": "1010011",
            "A-D": "0000111",
            "M-D": "1000111",
            "D&A": "0000000",
            "D&M": "1000000",
            "D|A": "0010101",
            "D|M": "1010101"
        }

        #table for jumps.
        self.j_table = {
            "": "000",
            "JGT": "001",
            "JEQ": "010",
            "JGE": "011",
            "JLT": "100",
            "JNE": "101",
            "JLE": "110",
            "JMP": "111"
        }

    def dest(self, mnemonic: str) -> str:
        #returns the 3 bit binary code of the dest mnemonic.
        return self.d_table[mnemonic]

    def comp(self, mnemonic: str) -> str:
        #returns the 7 bit binary code of the comp mnemonic.
        return self.c_table[mnemonic]

    def jump(self, mnemonic: str) -> str:
        #returns the 3 bit binary code of the jump mnemonic.
        return self.j_table[mnemonic]


class SymbolTable:

    #symbol labels and values.

    def __init__(self):
        #creates a new symbol table.
        self.table = {
            "R0": 0,
            "R1": 1,
            "R2": 2,
            "R3": 3,
            "R4": 4,
            "R5": 5,
            "R6": 6,
            "R7": 7,
            "R8": 8,
            "R9": 9,
            "R10": 10,
            "R11": 11,
            "R12": 12,
            "R13": 13,
            "R14": 14,
            "R15": 15,
            "SCREEN": 16384,
            "KBD": 24576,
            "SP": 0,
            "LCL": 1,
            "ARG": 2,
            "THIS": 3,
            "THAT": 4
        }

    def addEntry(self, symbol: str, value: int) -> None:
        #adds new symbol and value to the symbol table.
        self.table[symbol] = value

    def contains(self, symbol: str) -> bool:
        #checks if symbol is in the symbol table
        return symbol in self.table

    def getAddress(self, symbol: str) -> int:
        #returns the value of the symbol.
        return self.table[symbol]


def main():

    #check for file name.
    if len(sys.argv) != 2:
        print("Error: Hack assembly file required.")
        print("Usage: python " + os.path.basename(__file__) + " [file.asm]")
        return

    #create a parser with input file.
    input_file_name = sys.argv[1]
    parser = Parser(input_file_name)

    #initiate symbol table.
    symbols = SymbolTable()

    #scan input file for labels and add them to symbol table.
    counter = 0
    while parser.hasMoreCommands():
        parser.advance()
        #if command is label, add to symbol table.
        #otherwise increase program line counter.
        if parser.commandType() == "L":
            symbols.addEntry(parser.symbol(), counter)
        else:
            counter += 1

    #restart file parser.
    parser.restart()

    #initiate the binary coder.
    coder = Code()

    #open output file with same name but .hack extension.
    output_file_name = input_file_name.replace(".asm", ".hack")
    file = open(output_file_name, "w")

    #user defined variables starts from memory position 16.
    variable = 16
    while parser.hasMoreCommands():
        parser.advance()
        #check for command type and convert command into binary code.
        #A-Commands can be a constant, a symbol, or a variable declaration.
        if parser.commandType() == "A":
            num = 0
            symbol = parser.symbol()
            #constant
            if symbol.isdecimal():
                num = int(symbol)
            #symbol
            #either label or previously declared variable.
            elif symbols.contains(symbol):
                num = symbols.getAddress(symbol)
            #variable declaration
            else:
                num = variable
                symbols.addEntry(symbol, num)
                variable += 1
            file.write(format(num, "016b"))
            file.write("\n")
        #C-Commands made of a destination, a comparison, and a jump part.
        elif parser.commandType() == "C":
            #get binary code from the coder and write it in output file.
            comp = coder.comp(parser.comp())
            dest = coder.dest(parser.dest())
            jump = coder.jump(parser.jump())
            file.write("111" + comp + dest + jump)
            file.write("\n")
        else:
            #hack file only contains the binary codes of A-Commands and C-Commands.
            pass
    file.close()


if __name__ == "__main__":
    main()