import unittest
import struct
import os
from assembler import VirtualMachineAssembler, VirtualMachineInterpreter


class TestVirtualMachineAssembler(unittest.TestCase):
    def setUp(self):
        self.assembler = VirtualMachineAssembler()

    def test_parse_instruction_load_const(self):
        instruction = self.assembler.parse_instruction("LOAD_CONST 1 2 65535")
        expected = {'opcode': 26, 'args': ['1', '2', '65535']}
        self.assertEqual(instruction, expected)

    def test_parse_instruction_invalid_opcode(self):
        with self.assertRaises(ValueError):
            self.assembler.parse_instruction("INVALID_OPCODE 1 2 3")

class TestVirtualMachineInterpreter(unittest.TestCase):
    def setUp(self):
        self.interpreter = VirtualMachineInterpreter()

    def test_load_program(self):
        binary_data = struct.pack('>BBBBB', 26, 1, 2, 0xFF, 0xFF)  # Example binary program
        binary_file = "test_program.bin"
        with open(binary_file, 'wb') as f:
            f.write(binary_data)

        loaded_data = self.interpreter.load_program(binary_file)
        self.assertEqual(loaded_data, binary_data)

        # Clean up
        os.remove(binary_file)

    def test_execute_program_less_than(self):
        binary_data = (
                struct.pack('>BBBBB', 26, 1, 2, 0, 10) +  # LOAD_CONST 1 2 10
                struct.pack('>BBBBB', 26, 2, 3, 0, 5) +  # LOAD_CONST 2 3 5
                struct.pack('>BBBB', 15, 1, 0, 2)  # LESS_THAN 1 0 2
        )
        result = self.interpreter.execute_program(binary_data, 0, 10)
        self.assertEqual(result, [0])  # 10 is not less than 5

    def test_execute_program_unknown_opcode(self):
        binary_data = struct.pack('>B', 99)  # Invalid opcode
        with self.assertRaises(ValueError):
            self.interpreter.execute_program(binary_data, 0, 10)


if __name__ == '__main__':
    unittest.main()