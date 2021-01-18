#include <assert.h>
#include <ctype.h>
#include <errno.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define min(a, b) (((a) < (b)) ? (a) : (b))
#define max(a, b) (((a) > (b)) ? (a) : (b))

static char *_ascii_upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

// Limit the max board size to 26 so that each column can be identified
// by a single letter of the (english) alphabet. As the board area is
// bounded, and the bound trivially small, we can use fixed size arrays
// of memory for the board cells and overlay, rather than dynamically
// allocating them; this makes the code simpler and more robust and no
// meaningful cost.
#define MAX_BOARD_SIZE 26
#define MAX_BOARD_AREA (MAX_BOARD_SIZE * MAX_BOARD_SIZE)

// Use uint8_t and #defines for the cell values, rather than using an enum, as
// most of the value are actually going to be the numbers 0..9.
#define CELL_MINE  (uint8_t)255
#define CELL_EMPTY (uint8_t)0

enum OverlayCell
{
    OverlayCellHidden,
    OverlayCellVisible,
    OverlayCellMarked,
};

struct Board
{
    uint8_t size;
    uint8_t cells[MAX_BOARD_AREA];
    enum OverlayCell overlay[MAX_BOARD_AREA];
};

static struct Board board = {0};

void board_init(struct Board* board, uint8_t size, uint16_t num_mines)
{
    assert(board != NULL);
    assert(size > 0 && size <= MAX_BOARD_SIZE);

    board->size = size;
    memset(board->cells, 0, MAX_BOARD_AREA);
    memset(board->overlay, (unsigned char)OverlayCellHidden, MAX_BOARD_AREA);

    uint16_t area = (uint16_t)size * size;

    // Select a random set of mines by shuffling an array of all the cell indices and selecting the first M,
    // where M is the number of mines, rather than repeatedly choosing a random cell until we
    // find one that doesn't already contain a mine as (1) it places an upper bound on the time
    // of the algorithm and (2) handles the degenerate case of a large numbers of mines relative
    // to the number of cells well. The shuffle algorithm is the "inside-out" Fisher-Yates shuffle.

    uint16_t shuffled_indices[MAX_BOARD_AREA] = {0};
    for (size_t i = 0; i < min(area, MAX_BOARD_AREA); i++)
    {
        uint16_t j = rand() % (i + 1);
        if (j != i)
            shuffled_indices[i] = shuffled_indices[j];
        shuffled_indices[j] = i;
    }

    for (size_t i = 0; i < num_mines; i++)
    {
        board->cells[shuffled_indices[i]] = CELL_MINE;
    }

    // Generate the numeric values for each non-mine cell that give the number of neighboring mines.
    for (int y = 0; y < board->size; y++)
        for (int x = 0; x < board->size; x++)
        {
            size_t n = y * board->size + x;
            if (board->cells[n] != CELL_MINE)
            {
                unsigned short int count = 0;
                for (int j = max(0, y - 1); j < min(board->size, y + 2); j++)
                    for (int i = max(0, x - 1); i < min(board->size, x + 2); i++)
                    {
                        if (i == x && j == y)
                            continue;
                        if (board->cells[j * board->size + i] == CELL_MINE)
                            count += 1;
                    }
                board->cells[n] = count;
            }
        }
}

void board_reveal(struct Board* board, unsigned int x, unsigned int y)
{
    unsigned int n = y * board->size + x;

    if (board->overlay[n])
        return;

    board->overlay[n] = OverlayCellVisible;

    // "Flood reveal" connected empty cells.
    if (board->cells[n] == CELL_EMPTY)
        for (int j = max((int)y - 1, 0); j < min((int)y + 2, board->size); j++)
            for (int i = max((int)x - 1, 0); i < min((int)x + 2, board->size); i++)
                board_reveal(board, i, j);
}

void board_mark(struct Board* board, unsigned int x, unsigned int y)
{
    size_t n = y * board->size + x;
    switch (board->overlay[n])
    {
        case OverlayCellHidden:
            board->overlay[n] = OverlayCellMarked;
            break;
        case OverlayCellMarked:
            board->overlay[n] = OverlayCellHidden;
            break;
        case OverlayCellVisible:
            break;
    }
}

enum GameState
{
    GameStateUnfinished,
    GameStateWon,
    GameStateLost,
};

enum GameState board_check_game_state(struct Board* board)
{
    for (unsigned int y = 0; y < board->size; y++)
        for (unsigned int x = 0; x < board->size; x++)
        {
            size_t n = y * board->size + x;
            if ((board->overlay[n] == OverlayCellVisible) && (board->cells[n] == CELL_MINE))
                return GameStateLost;
        }

    for (unsigned int y = 0; y < board->size; y++)
        for (unsigned int x = 0; x < board->size; x++)
        {
            size_t n = y * board->size + x;
            if ((board->overlay[n] == OverlayCellHidden) && (board->cells[n] != CELL_MINE))
                return GameStateUnfinished;
        }

    return GameStateWon;
}

void view_draw(struct Board *board)
{
    printf("  ");
    for (unsigned int i = 0; i < board->size; i++)
    {
        printf("%2c", _ascii_upper[i]);
    }
    printf("\n");

    for (unsigned int y = 0; y < board->size; y++)
    {
        printf("%2u", y + 1);
        for (unsigned int x = 0; x < board->size; x++)
        {
            size_t n = y * board->size + x;

            enum OverlayCell overlay = board->overlay[n];
            if (overlay == OverlayCellHidden)
                printf(" #");
            else if (overlay == OverlayCellMarked)
                printf(" !");
            else
            {
                uint8_t cell = board->cells[n];
                if (cell == CELL_EMPTY)
                    printf("  ");
                else if (cell == CELL_MINE)
                    printf(" *");
                else
                    printf(" %d", cell);
            }
        }
        printf("\n");
    }
}

enum CommandType
{
    CommandTypeQuit,
    CommandTypeReveal,
    CommandTypeMark,
};

struct Command
{
    enum CommandType type;
    unsigned int x;
    unsigned int y;
};

enum InputType
{
    InputTypeCommand,
    InputTypeInvalid,
    InputTypeEof,
    InputTypeError,
};

static char input[6] = {0};

enum InputType view_input(struct Command* command)
{
    assert(command != NULL);

    printf("> ");
    fflush(stdout);

    char input[6] = {0};

    if (fgets(input, sizeof input, stdin) == NULL && ferror(stdin))
    {
        return InputTypeError;
    }

    if (feof(stdin))
    {
        return InputTypeEof;
    }

    if (input[strlen(input) - 1] != '\n')
    {
        char c = '\0';
        do
        {
            c = getc(stdin);
        } while (c != '\n' && c != EOF);

        if (c == EOF)
        {
            return ferror(stdin) ? InputTypeError : InputTypeEof;
        }

        return InputTypeInvalid;
    }

    for (char* s = input; *s != '\0'; s++)
    {
        *s = toupper(*s);
        if (*s == '\n')
            *s = '\0';
    }

    if (strncmp(input, "Q", 4) == 0 || strncmp(input, "QUIT", 4) == 0)
    {
        command->type = CommandTypeQuit;
        command->x = 0;
        command->y = 0;
        return InputTypeCommand;
    }

    char* s = &input[0];

    bool mark = (*s == '!');
    if (mark)
        s++;

    if (!isalpha(*s))
        return InputTypeInvalid;

    unsigned int x = (strchr(_ascii_upper, *s) - &_ascii_upper[0]);
    s++;

    unsigned int y = 0;
    while (isdigit(*s))
    {
        y = (y * 10) + (*s - '0');
        s++;
    }
    y = y - 1;

    if (*s != '\0')
        return InputTypeInvalid;

    command->type = (mark ? CommandTypeMark : CommandTypeReveal);
    command->x = x;
    command->y = y;
    return InputTypeCommand;
}

void display_help()
{
    printf("usage: minesweeper [-h|--help] [-s|--size SIZE] [-m|--mines MINES]\n");
}

int main(int argc, char** argv)
{
    unsigned int exit_code = 0;
    srand(time(NULL));

    // Default values.
    uintmax_t size = 6;
    uintmax_t mines = 6;

    for (size_t i = 1; i < argc; i += 2)
    {
        if (strcmp(argv[i], "-s") == 0 || strcmp(argv[i], "--size") == 0)
        {
            // Errno does not need to be set/checked here, as if the return value is 0 or UINTMAX_MAX
            // then the value is already considered invalid.
            size = strtoumax(argv[i + 1], NULL, 10);
            if (size < 1 || size > MAX_BOARD_SIZE)
            {
                display_help();
                printf("error: invalid board size: %s\n", argv[i + 1]);
                exit_code = 1;
                goto exit;
            }
        }
        else if (strcmp(argv[i], "-m") == 0 || strcmp(argv[i], "--mines") == 0)
        {
            // A number of mines > board area is fine, we just fill the board with mines and ignore
            // the rest. Zero is also fine - the game is simply an instant win.
            errno = 0;
            mines = strtoumax(argv[i + 1], NULL, 10);
            if (errno)
            {
                display_help();
                printf("error: invalid value: %s\n", argv[i + 1]);
                exit_code = 1;
                goto exit;
            }
            if (mines > MAX_BOARD_AREA)
                mines = MAX_BOARD_AREA;
        }
        else if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0)
        {
            display_help();
            goto exit;
        }
        else
        {
            display_help();
            printf("error: unrecognized argument: %s\n", argv[i]);
            exit_code = 1;
            goto exit;
        }
    }

    // These casts are okay as we've already range checked them.
    board_init(&board, (uint8_t)size, (uint16_t)mines);
    view_draw(&board);

    while (1)
    {
        struct Command command;
        switch (view_input(&command))
        {
            case InputTypeError:
                printf("Error getting input.\n");
                exit_code = 1;
                goto exit;
            case InputTypeEof:
                printf("\n");
                goto exit;
            case InputTypeInvalid:
                printf("I didn't understand that.\n");
                break;
            case InputTypeCommand:
            {
                if (command.x >= board.size || command.y >= board.size)
                {
                    printf("Co-ordinates not valid.\n");
                    continue;
                }

                switch (command.type)
                {
                    case CommandTypeQuit:
                        goto exit;

                    case CommandTypeReveal:
                    {
                        board_reveal(&board, command.x, command.y);
                        view_draw(&board);

                        switch (board_check_game_state(&board))
                        {
                            case GameStateWon:
                                printf("Congratulations, you have swept all the mines and won!\n");
                                goto exit;
                            case GameStateLost:
                                printf("Oh no, you hit a mine and lost!\n");
                                goto exit;
                            case GameStateUnfinished:
                                break;
                        };

                        break;
                    }

                    case CommandTypeMark:
                        board_mark(&board, command.x, command.y);
                        view_draw(&board);
                        break;
                };
                break;
            }
        };
    }

exit:
    return exit_code;
}