import argparse
import enum
import itertools
import random
import re
import string
import sys


class Board:

    def __init__(self, size, mines):
        self.size = size
        self._board = list()
        self._revealed = list()
        self._marks = set()

        for i in range(size):
            self._board.append([' '] * size)
            self._revealed.append([False] * size)

        cells = list(itertools.product(range(size), repeat=2))
        random.shuffle(cells)
        for x, y in cells[:mines]:
            self._board[x][y] = 'M'

        for x in range(size):
            for y in range(size):
                if self._board[x][y] == 'M':
                    continue
                n = 0
                for i in range(max(0, x-1), min(size, x+2)):
                    for j in range(max(0, y-1), min(size, y+2)):
                        if not (i == x and j == y):
                            if self._board[i][j] == 'M':
                                n += 1
                if n > 0:
                    self._board[x][y] = f'{n:d}'


    def value(self, x, y):
        return self._board[x][y]

    def reveal(self, x, y):
        """Reveal this cell and, if empty, all connected empty cells and their bordering numbered cells."""
        if (self._board[x][y] == ' '):
            self._flood_reveal(x, y)
        else:
            self._revealed[x][y] = True        

    def _flood_reveal(self, x, y):
        if self._revealed[x][y]:
            return

        self._revealed[x][y] = True

        if self._board[x][y] == ' ':
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
        return all(self._revealed[x][y] or self._board[x][y] == 'M'
                   for x in range(self.size)
                   for y in range(self.size))

    def toggle_mark(self, x, y):
        cell = (x, y)
        if cell in self._marks:
            self._marks.discard(cell)
        else:
            self._marks.add(cell)

    def is_marked(self, x, y):
        cell = (x, y)
        return cell in self._marks


class Commands(enum.Enum):

    Unknown = enum.auto() 
    Quit    = enum.auto() 
    Reveal  = enum.auto()
    Mark    = enum.auto()

class UnknownCommand:

    action = Commands.Unknown

class QuitCommand:

    action = Commands.Quit

class RevealCommand:

    action = Commands.Reveal

    def __init__(self, x, y):
        self.x = x
        self.y = y

class MarkCommand:

    action = Commands.Mark

    def __init__(self, x, y):
        self.x = x
        self.y = y


class UI:

    _prompt = '> '

    def draw(self, board):
        print('   ' + ' '.join(x for x in string.ascii_uppercase[:board.size]))
        for y in range(board.size):
            print(f'{y+1: <2}', sep='', end='')
            for x in range(board.size):
                if not board.is_revealed(x, y):
                    if board.is_marked(x, y):
                        print(' !', sep='', end='')
                    else:
                        print(' #', sep='', end='')
                else:
                    value = board.value(x, y)
                    if value == 'M':
                        value = "*"
                    print(f' {value:s}', sep='', end='')
            print()

    def input(self):
        try:
            s = input(self._prompt)
        except EOFError:
            return QuitCommand()
        
        if s.lower() in ('q', 'quit', 'exit'):
            return QuitCommand()

        match = re.match(r'^(!?)([a-zA-Z])([0-9]+$)', s)
        if match:
            mark = bool(match.group(1))
            x = int(string.ascii_lowercase.index(match.group(2).lower()))
            y = int(match.group(3)) - 1

            if mark:
                return MarkCommand(x, y)
            else:
                return RevealCommand(x, y)

        else:
            return UnknownCommand

    def message(self, msg):
        print(msg)


class GameLoop:

    def run(self, board, ui):
        while True:
            command = ui.input()

            if command.action in (Commands.Mark, Commands.Reveal):
                if (command.x >= board.size) or (command.y >= board.size):
                    ui.message('The co-ordinates are outside of the board.')
                    continue

            if command.action == Commands.Quit:
                break

            elif command.action == Commands.Mark:
                board.toggle_mark(command.x, command.y)
                ui.draw(board)

            elif command.action == Commands.Reveal:          
                if (board.is_revealed(command.x, command.y)):
                    ui.message('That cell has already been revealed.')
                    continue                

                board.reveal(command.x, command.y)
                ui.draw(board)

                if board.value(command.x, command.y) == 'M':
                    ui.message('Oh no, you hit a mine! You lost.')                
                    break

                if board.is_complete():
                    ui.message('Congratulations, you swept all mines and won the game!')
                    break

            elif command.action == Commands.Unknown:
                ui.message('I didn\'t understand that.')


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
    
