import argparse
import enum
import itertools
import random
import re
import string
import sys

class Cells(enum.Enum):

    Empty  = 1
    Number = 2
    Mine   = 3

class Commands(enum.Enum):

    Unknown = 1
    Quit    = 2 
    Reveal  = 3
    Mark    = 4

class GameConditions(enum.Enum):

    Lost = 1
    Won  = 2

class InputErrors(enum.Enum):
    OutOfBounds = 1
    Unknown     = 2

class Command:

    def __init__(self, type):
        self.type = type

class Move:

    def __init__(self, type, x, y):
        self.type = type
        self.x = x
        self.y = y

class Cell:

    def __init__(self, type, value=None):
        self.type = type
        self.value = value

class Board:

    # Internally the board is a simple 2-D "matrix" (list-of-lists) of characters: 
    # 'M' for a mine, ' ' for an empty cell, and '1'..'8' for number 
    # cells. A separate "matrix" of bools determines which cells have
    # been revealed by the player and which remain hidden.

    def __init__(self, size, mines):
        self.size = size

        self._board = list()
        self._revealed = list()
        self._marks = set()

        for i in range(size):
            self._board.append([Cell(Cells.Empty)] * size)
            self._revealed.append([False] * size)

        # Populate the mines
        cells = list(itertools.product(range(size), repeat=2))
        random.shuffle(cells)
        for x, y in cells[:mines]:
            self._board[x][y] = Cell(Cells.Mine)

        # Populate the numbers
        for x in range(size):
            for y in range(size):
                if self._board[x][y].type == Cells.Mine:
                    continue
                n = 0
                for i in range(max(0, x-1), min(size, x+2)):
                    for j in range(max(0, y-1), min(size, y+2)):
                        if not (i == x and j == y):
                            if self._board[i][j].type == Cells.Mine:
                                n += 1
                if n > 0:
                    self._board[x][y] = Cell(Cells.Number, value=n)

    def cell(self, x, y):
        return self._board[x][y]

    def reveal(self, x, y):
        """Reveal this cell and, if empty, all connected empty cells and their bordering numbered cells."""
        if (self._board[x][y].type == Cells.Empty):
            self._flood_reveal(x, y)
        else:
            self._revealed[x][y] = True
            self._marks.discard((x, y)) 

    def _flood_reveal(self, x, y):
        if self._revealed[x][y]:
            return

        self._revealed[x][y] = True
        self._marks.discard((x, y)) 

        if self._board[x][y].type == Cells.Empty:
            for i in range(x-1, x+2):
                if i < 0 or i >= board.size:
                    continue
                for j in range(y-1, y+2):
                    if j < 0 or j >= board.size:
                        continue
                    self._flood_reveal(i, j)

    def is_revealed(self, x, y):
        return self._revealed[x][y]

    def is_complete(self):        
        return all(self._revealed[x][y] or self._board[x][y].type == Cells.Mine
                   for x in range(self.size)
                   for y in range(self.size))

    def is_marked(self, x, y):
        cell = (x, y)
        return cell in self._marks

    def toggle_mark(self, x, y):
        cell = (x, y)
        if cell in self._marks:
            self._marks.discard(cell)
        else:
            self._marks.add(cell)

class UI:

    _prompt = '> '
    _mine   = ' *'
    _empty  = '  '
    _mark   = ' !'
    _hidden = ' #'

    _move_regex = re.compile(r'^(!?)([a-zA-Z])([0-9]+$)')

    def draw(self, board):
        print('   ' + ' '.join(x for x in string.ascii_uppercase[:board.size]))
        for y in range(board.size):
            print(f'{y+1: <2}', sep='', end='')
            for x in range(board.size):
                if board.is_revealed(x, y):
                    cell = board.cell(x, y)
                    if cell.type == Cells.Mine:
                        print(UI._mine, sep='', end='')
                    elif cell.type == Cells.Empty:
                        print(UI._empty, sep='', end='')
                    else:
                        print(f' {cell.value:d}', sep='', end='')
                else:
                    if board.is_marked(x, y):
                        print(UI._mark, sep='', end='')
                    else:
                        print(UI._hidden, sep='', end='')
            print()

    def input(self):
        try:
            s = input(self._prompt)
        except EOFError:
            return Command(Commands.Quit)
        
        if s.lower() in ('q', 'quit', 'exit'):
            return Command(Commands.Quit)

        match = ui._move_regex.match(s)
        if match:
            mark = bool(match.group(1))
            x = int(string.ascii_lowercase.index(match.group(2).lower()))
            y = int(match.group(3)) - 1

            if mark:
                return Move(Commands.Mark, x, y)
            else:
                return Move(Commands.Reveal, x, y)

        else:
            return Command(Commands.Unknown)

    def update(self, condition):
        if condition == GameConditions.Lost:
            print('Oh no, you hit a mine! You lost.')
        elif condition == GameConditions.Won:
            print('Congratulations, you swept all mines and won the game!')

    def reply(self, reply):
        if reply == InputErrors.Unknown:
            print('I didn\'t understand that.')
        elif reply == InputErrors.OutOfBounds:
            print('The co-ordinates are outside of the board.')

class GameLoop:

    def run(self, board, ui):
        while True:
            command = ui.input()

            if isinstance(command, Move) and (command.x >= board.size or command.x < 0 or command.y >= board.size or command.y < 0):
                ui.reply(InputErrors.OutOfBounds)
                continue

            if command.type == Commands.Quit:
                break

            elif command.type == Commands.Mark:
                board.toggle_mark(command.x, command.y)
                ui.draw(board)

            elif command.type == Commands.Reveal:                      
                board.reveal(command.x, command.y)
                ui.draw(board)

                if board.cell(command.x, command.y).type == Cells.Mine:
                    ui.update(GameConditions.Lost)
                    break

                if board.is_complete():
                    ui.update(GameConditions.Won)
                    break

            elif command.type == Commands.Unknown:
                ui.reply(InputErrors.Unknown)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Clear the board containing hidden mines, without detonating any of them.')
    parser.add_argument('--size', type=int, action='store', help='Board size (width and height).', default=10)
    parser.add_argument('--mines', type=int, action='store', help='Number of mines', default=10)
    args = parser.parse_args()

    # Limit board size to 26 so that all the columns can be addressed by a single alphabet character.
    if args.size < 1 or args.size > 26:
        print('Board size must be a positive integer between 1 and 26 inclusive.')
        sys.exit(1)
        
    board = Board(size=args.size, mines=args.mines)
    
    ui = UI()
    ui.draw(board)

    loop = GameLoop()
    loop.run(board, ui)
