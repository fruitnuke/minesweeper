import string

class Board:

    def __init__(self, size=6):
        self.size = size
        self._board = list()
        self._revealed = list()
        for i in range(size):
            self._board.append([" "] * size)
            self._revealed.append([False] * size)

    def value(self, x, y):
        return self._board[x][y] if self._revealed[x][y] else '#'

    def reveal(self, x, y):
        self._revealed[x][y] = True
        return self.value(x, y)


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
                print('The co-ordinates are outside of the board')
                continue

            board.reveal(x, y)
            draw(board)

        else:
            print('I didn\'t understand that')



