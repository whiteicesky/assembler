import argparse
import json
import struct
import sys


class VirtualMachineAssembler:
    OPCODES = {
        'LOAD_CONST': 26,
        'LOAD_MEM': 28,
        'STORE_MEM': 1,
        'LESS_THAN': 15  
    }

    def __init__(self):
        self.instructions = []
        self.labels = {}
        self.binary_code = bytearray()

    def parse_instruction(self, line):
        line = line.strip()
        line = line.split(';')[0].strip()
        if not line:
            return None

        parts = line.split()
        opcode_name = parts[0]

        if opcode_name not in self.OPCODES:
            raise ValueError(f"Неизвестная инструкция: {opcode_name}")

        if opcode_name == 'LOAD_CONST' and len(parts) != 4:
            raise ValueError(f"Команда {opcode_name} требует 3 аргумента")
        if opcode_name == 'LESS_THAN' and len(parts) != 5:
            raise ValueError(f"Команда {opcode_name} требует 4 аргументов")

        instruction = {
            'opcode': self.OPCODES[opcode_name],
            'args': parts[1:]
        }
        print(f"Parsed instruction: {instruction}")
        return instruction

    def assemble(self, input_file, output_file, log_file):
        encodings = ['utf-8', 'cp1251', 'cp866', 'latin1']

        for encoding in encodings:
            try:
                with open(input_file, 'r', encoding=encoding) as f:
                    source_lines = f.readlines()
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError("Не удалось определить кодировку файла")

        for i, line in enumerate(source_lines):
            line = line.strip()
            if line.endswith(':'):
                self.labels[line[:-1]] = len(self.instructions)

        # Второй проход
        assembly_log = []
        for line in source_lines:
            line = line.strip()
            if not line or line.endswith(':'):
                continue

            instruction = self.parse_instruction(line)
            if instruction:
                binary_inst = self.encode_instruction(instruction)
                self.binary_code.extend(binary_inst)

                # логи
                log_entry = {
                    'instruction': line,
                    'opcode': instruction['opcode'],
                    'binary': binary_inst.hex()
                }
                assembly_log.append(log_entry)

        with open(output_file, 'wb') as f:
            f.write(self.binary_code)

        with open(log_file, 'w') as f:
            json.dump(assembly_log, f, indent=2)

    def encode_instruction(self, instruction):
        opcode = instruction['opcode']
        args = instruction['args']

        if opcode == 26:
            a, b, c = map(int, args)
            binary = struct.pack('>BBBBB', opcode, b, c >> 16 & 0xFF, c >> 8 & 0xFF, c & 0xFF)
            print(f"Encoding LOAD_CONST: args={args}, binary={binary.hex()}")
            return binary

        elif opcode == 15:
            a, b, c, d = map(int, args)
            binary = struct.pack('>BBBB', opcode, b, c, d)
            print(f"Encoding LESS_THAN: args={args}, binary={binary.hex()}")
            return binary

        raise ValueError("Unsupported instruction")


class VirtualMachineInterpreter:
    def __init__(self):
        self.memory = [0] * 256  # нули по умолчанию
        self.registers = [0] * 32  # Регистры
        self.output_memory = []

    def load_program(self, binary_file):
        """
        Загрузка бинарной программы из файла
        """
        with open(binary_file, 'rb') as f:
            binary_data = f.read()
        return binary_data

    def execute_program(self, binary_data, start_range, end_range):
        pc = 0
        while pc < len(binary_data):
            opcode = binary_data[pc]
            print(f"PC={pc}, Opcode={opcode}")

            if opcode == 26:
                b = binary_data[pc + 1]
                c = int.from_bytes(binary_data[pc + 2:pc + 5], 'big')
                self.registers[b] = c
                self.memory[b] = c
                print(f"LOAD_CONST: reg[{b}] = {c}, memory[{b}] = {c}")
                pc += 5

            elif opcode == 15:
                b = binary_data[pc + 1]
                c = binary_data[pc + 2]
                d = binary_data[pc + 3]

                addr_b = self.registers[b]
                addr_d = self.registers[d]

                memory_value = self.memory[addr_b + c] if 0 <= addr_b + c < len(self.memory) else 0
                result = 1 if addr_d < memory_value else 0

                self.output_memory.append(result)
                print(f"LESS_THAN: reg[{d}] = {result} (reg[{d}] < memory[{addr_b + c}] -> {memory_value})")
                pc += 4

            else:
                raise ValueError(f"Неизвестная инструкция с opcode={opcode} на PC={pc}")

        print(f"Final result in output_memory: {self.output_memory}")
        with open("result.json", "w") as f:
            json.dump(self.output_memory, f)
        return self.output_memory


def main():
    parser = argparse.ArgumentParser(description='УВМ Ассемблер и Интерпретатор')
    parser.add_argument('mode', choices=['assemble', 'interpret'])
    parser.add_argument('input_file')
    parser.add_argument('output_file')
    parser.add_argument('--log', help='Путь к файлу лога')
    parser.add_argument('--start', type=int, default=0, help='Начало диапазона памяти')
    parser.add_argument('--end', type=int, default=10, help='Конец диапазона памяти')

    args = parser.parse_args()

    if args.mode == 'assemble':
        assembler = VirtualMachineAssembler()
        assembler.assemble(args.input_file, args.output_file, args.log or 'assembly.log')
        print(f"Ассемблирование завершено. Результат: {args.output_file}")

    elif args.mode == 'interpret':
        interpreter = VirtualMachineInterpreter()
        binary_data = interpreter.load_program(args.input_file)
        result = interpreter.execute_program(binary_data, args.start, args.end)

        with open(args.output_file, 'w') as f:
            json.dump(result, f)
        print(f"Интерпретация завершена. Результат: {args.output_file}")


if __name__ == '__main__':
    main()