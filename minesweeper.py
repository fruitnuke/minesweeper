import itertools
import random
import string

class Board:

    def __init__(self, size=6, mines=3):
        self.size = size
        self._board = list()
        self._revealed = list()
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
        return self._board[x][y] if self._revealed[x][y] else '#'

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


def draw(board):
    print('   ' + ' '.join(x for x in string.ascii_uppercase[:board.size]))
    for y in range(board.size):
        print(f'{y+1: <2}', sep='', end='')
        for x in range(board.size):
            print(f' {board.value(x, y):s}', sep='', end='')
        print()


if __name__ == '__main__':
    board = Board(size=6)
    draw(board)
    
    while True:
        try:
            inp = input('> ')
        except EOFError:
            break

        if inp.lower() in ('q', 'quit', 'exit'):
            break

        if len(inp) == 2 and inp[0].isalpha() and inp[1].isdigit():
            x = int(string.ascii_lowercase.index(inp[0].lower()))
            y = int(inp[1]) - 1

            if (x >= board.size) or (y >= board.size):
                print('The co-ordinates are outside of the board.')
                continue

            if (board.is_revealed(x, y)):
                print('That cell has already been revealed.')
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


