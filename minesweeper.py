import argparse
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

def draw(board):
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Clear the board containing hidden mines, without detonating any of them.')
    parser.add_argument('--size', type=int, action='store', help='Board size (width and height).', default=10)
    parser.add_argument('--mines', type=int, action='store', help='Number of mines', default=10)
    args = parser.parse_args()

    if args.size > 26:
        print('Board too large (max size is 26).')
        sys.exit(1)
        
    board = Board(size=args.size, mines=args.mines)
    draw(board)
    
    while True:
        try:
            inp = input('> ')
        except EOFError:
            break

        if inp.lower() in ('q', 'quit', 'exit'):
            break

        match = re.match(r'^(!?)([a-zA-Z])([0-9]+$)', inp)
        if match:
            mark = bool(match.group(1))
            x = int(string.ascii_lowercase.index(match.group(2).lower()))
            y = int(match.group(3)) - 1

            if (x >= board.size) or (y >= board.size):
                print('The co-ordinates are outside of the board.')
                continue

            if (board.is_revealed(x, y)):
                print('That cell has already been revealed.')
                continue

            if mark:
                board.toggle_mark(x, y)
                draw(board)
                continue

            board.reveal(x, y)
            draw(board)

            if board.value(x, y) == 'M':
                print('Oh no, you hit a mine! You lost.')                
                break

            if board.is_complete():
                print('Congratulations, you swept all mines and won the game!')
                break

        else:
            print('I didn\'t understand that.')



