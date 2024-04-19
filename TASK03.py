# -----------------------------------------------------------------------------------------------------------------------
# Name: Alina Hasan
# Group: Ruby
# Task: 03 [Completed using Python]
# -----------------------------------------------------------------------------------------------------------------------
import binascii
import hashlib
import hmac
import random
import secrets
import sys
from collections import deque, Counter

from tabulate import tabulate


class Error:
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return "\n".join(["ERROR: ", self.message])


# Error Instances
class Errors:
    InvalidLength = Error("You need to provide at least 3 moves to create a game.\nExample: Rock Paper Scissors")
    InvalidNumber = Error("You need to provide an odd number of moves.")
    RepeatedMoves = Error("You need to provide distinct moves.")
    InvalidResponse = Error("Invalid Response. If you would like to play another round enter 'Y' otherwise, 'N'.")
    InvalidOption = Error("Option Unavailable. Please select an option provided in the table.")
    InvalidRequest = Error("Invalid Request.")
    InvalidInputForm = Error("Invalid Input Form.\nTo make a move, enter a (non-zero) number provided in the "
                             "table.\nEnter '?' for help.\nEnter '0' to exit game.")


class KeyGeneration:
    @staticmethod
    def generate_key():
        return secrets.token_hex(32)  # 32 bytes = 256 bits


class HMAC:
    @staticmethod
    def calculate_hmac(move, key_hex):
        move_bytes = move.encode('utf-8')
        key_bytes = binascii.unhexlify(key_hex)
        hmac_hex = hmac.new(key_bytes, move_bytes, hashlib.sha3_256).hexdigest()  # Calculate HMAC using SHA3-256
        return hmac_hex

    @staticmethod
    def verify_hmac(move, key_hex, expected_hmac):
        hmac_hex = HMAC.calculate_hmac(move, key_hex)
        if hmac_hex == expected_hmac:
            print("HMAC verification successful!")
        else:
            print("HMAC verification failed!")
            print(f"Expected HMAC: {expected_hmac}")
            print(f"Actual HMAC: {hmac_hex}")


class GameRules:
    def __init__(self, moves):
        self.moves = moves
        self.help_data = self.compute_rules()

    def compute_rules(self):
        length = len(self.moves)
        half = length // 2
        help_data = [["" for _ in range(length)] for _ in range(length)]

        # Set "Draw", "Win", "Lose" for the First Row
        help_data[0][0] = "Draw"
        help_data[0][1:half + 1] = ["Win"] * half
        help_data[0][half + 1:] = ["Lose"] * half

        # Shift Previous Row Right Once and Replace Next Row
        for i in range(1, length):
            help_data[i] = self.shift_right(help_data[i - 1])

        return help_data

    def shift_right(self, help_data_row):
        help_data_row = deque(help_data_row)
        help_data_row.rotate(1)
        return list(help_data_row)


class Game(GameRules):
    def __init__(self, moves):
        super().__init__(moves)
        self.key_hex = ""
        self.hmac_hex = ""
        self.computer_move = ""
        self.user_move = ""

    def generate_move(self):
        self.computer_move = random.choice(self.moves)
        self.hmac_hex = HMAC.calculate_hmac(self.computer_move, self.key_hex)
        print(f"HMAC: {self.hmac_hex}")
        return self.computer_move, self.hmac_hex

    def display_menu(self):
        print("Available Moves:")
        menu_header = ["Move"]
        menu_data = [[i, move] for i, move in enumerate(self.moves, start=1)]
        menu_data.append(["\033[31m0\033[0m", "\033[31mEXIT\033[0m"])  # Add EXIT Option
        menu_data.append(["\033[34m?\033[0m", "\033[34mHELP\033[0m"])  # Add HELP Option
        print(tabulate(menu_data, headers=menu_header, tablefmt="pretty"))

    def get_input(self):
        while True:
            self.display_menu()
            option = input("Enter your move: ")
            if option == "0":
                exit_game()
            elif option == "?":
                self.display_help()
            else:
                if self.check_input(option):
                    break

    def check_input(self, option):
        try:
            user_index = int(option) - 1
            if 0 <= user_index < len(self.moves):
                self.display_result(user_index)
                return True
            else:
                print(Errors.InvalidOption)
        except ValueError:
            print(Errors.InvalidInputForm)
        return False

    def display_result(self, user_index):
        self.user_move = self.moves[user_index]
        print(f"Your move: {self.user_move}")
        print(f"Computer move: {self.computer_move}")
        computer_index = self.moves.index(self.computer_move)
        result_map = {
            "Win": "You\033[38;5;34m\033[1m win!\033[0m",
            "Lose": "You\033[38;5;196m\033[1m lose!\033[0m",
            "Draw": "It's a\033[1m draw!\033[0m"
        }
        result = result_map[self.help_data[computer_index][user_index]]
        print(tabulate([[result]], tablefmt="pretty"))
        print(f"HMAC Key: {self.key_hex}")
        self.display_link()

    def display_link(self):
        instruction_data = [
            ["1", 'Set "Input Type" to "TEXT" and copy-paste Computer move to "Input" field.'],
            ["2", 'Set "Key Type" to "HEX" and copy-paste HMAC Key to "Key" field.'],
            ["3", 'Set "SHA variant" to "SHA3-256."'],
            ["4", 'Set "Output Type" to "HEX."'],
            ["5", 'Compare with calculated HMAC in "Result" to HMAC provided at the start of game.']
        ]
        instruction_header = ["Step", "Instruction"]
        instruction_table = tabulate(instruction_data, headers=instruction_header, tablefmt="grid")
        hmac_link = "Link to online HMAC Calculator: https://www.liavaag.org/English/SHA-Generator/HMAC/"
        print(hmac_link)
        print(instruction_table)

    def display_help(self):
        current_page, page_size = 1, 7
        while True:
            print("Displaying HELP instructions.\nNote: Results being displayed are from your point of view.")
            help_table = HelpTableGenerator.generate_help_table(self.help_data, self.moves, current_page, page_size)
            print(help_table)
            request = input("Enter '>' for next page, '<' for previous page, or '0' to exit help: ")
            if request.lower() == '>':
                current_page = min(current_page + 1, (len(self.moves) // page_size) + 1)
            elif request.lower() == '<':
                current_page = max(current_page - 1, 1)
            elif request.lower() == '0':
                break
            else:
                print(Errors.InvalidRequest)

    def prompt_user(self):
        while True:
            choice = input("Would you like to play another round? [Y/N]: ")
            if choice.lower() == "y":
                return True
            elif choice.lower() == "n":
                return False
            else:
                print(Errors.InvalidResponse)

    def start_round(self):
        while True:
            self.key_hex = KeyGeneration.generate_key()
            self.generate_move()
            self.get_input()
            # HMAC.verify_hmac(self.computer_move, self.key_hex, self.hmac_hex)
            proceed = self.prompt_user()
            if not proceed:
                exit_game()


class HelpTableGenerator:
    @staticmethod
    def generate_help_table(help_data, moves, page_num, page_size):
        start_index, end_index = HelpTableGenerator.calculate_index_range(page_num, page_size, len(moves))
        paginated_moves = moves[start_index:end_index]

        help_headers = HelpTableGenerator.generate_headers(paginated_moves)

        help_table = HelpTableGenerator.generate_rows(help_data, moves, start_index, end_index)
        help_table.append([f"Page {page_num} of {len(moves) // page_size + 1}"])

        return tabulate(help_table, headers=help_headers, tablefmt="grid")

    @staticmethod
    def calculate_index_range(page_num, page_size, total_moves):
        start_index = (page_num - 1) * page_size
        end_index = min(start_index + page_size, total_moves)
        return start_index, end_index

    @staticmethod
    def generate_headers(paginated_moves):
        header_prefix = "\033[38;5;196m v PC\033[0m / \033[38;5;21m User >\033[0m"
        return [header_prefix] + [f"\033[38;5;21m{move}\033[0m" for move in paginated_moves]

    @staticmethod
    def generate_rows(help_data, moves, start_index, end_index):
        help_table = []
        for move, help_row in zip(moves, help_data):
            colored_move = f"\033[38;5;196m {move}\033[0m"
            help_table_row = HelpTableGenerator.color_row([colored_move] + help_row[start_index:end_index])
            help_table.append(help_table_row)
        return help_table

    @staticmethod
    def color_row(help_row):
        colored_row = []
        for cell in help_row:
            if cell == "Win":
                colored_row.append(f"\033[38;5;34m\033[1m{cell}\033[0m")
            elif cell == "Lose":
                colored_row.append(f"\033[38;5;196m\033[1m{cell}\033[0m")
            elif cell == "Draw":
                colored_row.append(f"\033[1m{cell}\033[0m")
            else:
                colored_row.append(f"{cell}")
        return colored_row


def check_moves(moves):
    errors = []
    if len(moves) < 3:
        errors.append(Errors.InvalidLength)
    if len(moves) % 2 == 0 and len(moves) > 0:
        errors.append(Errors.InvalidNumber)
    if len(moves) != len(set(moves)):
        errors.append(Errors.RepeatedMoves)
        repeated_moves = find_repeat(moves)
        for repeated_move in repeated_moves:
            print(f"{repeated_move} was repeated.")
    if errors:
        for error in errors:
            print(error)
        exit_game()


def find_repeat(moves):
    count = Counter(moves)
    return [move for move, count in count.items() if count > 1]


def start_game(moves):
    check_moves(moves)
    game = Game(moves)
    game.start_round()


def exit_game():
    print("Exiting...")
    sys.exit()


moves = sys.argv[1:]  # Exclude Script Name
start_game(moves)
