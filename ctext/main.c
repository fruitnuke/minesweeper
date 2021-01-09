#include <assert.h>
#include <ctype.h>
#include <errno.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>

static char *_ascii_upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

struct Board
{
    unsigned int size;
};

enum InputState
{
    InputValid,
    InputInvalid,
    InputEof,
    InputError,
};

enum CommandType
{
    CommandQuit,
};

struct Command
{
    enum CommandType type;
};

void view_draw(struct Board *board)
{
    printf("  ");
    for (unsigned int i = 0; i < board->size; i++)
    {
        printf("%2c", _ascii_upper[i]);
    }
    printf("\n");

    for (unsigned int i = 0; i < board->size; i++)
    {
        printf("%2u", i + 1);
        for (unsigned int j = 0; j < board->size; j++)
        {
            printf(" #");
        }
        printf("\n");
    }
}

 enum InputState view_input(struct Command* command)
 {
    assert(command != NULL);

    printf("> ");
    fflush(stdout);

    char input[6] = {0};

    if (fgets(input, sizeof input, stdin) == NULL && ferror(stdin))
    {
        return InputError;
    }

    if (feof(stdin))
    {
        return InputEof;
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
            return ferror(stdin) ? InputError : InputEof;
        }

        return InputInvalid;
    }

    for (char* s = input; *s != '\0'; s++)
    {
        *s = tolower(*s);
        if (*s == '\n')
            *s = '\0';
    }

    if (strncmp(input, "q", 4) == 0 || strncmp(input, "quit", 4) == 0)
    {
        command->type = CommandQuit;
        return InputValid;
    }

    return InputInvalid;
 }

static char input[6] = {0};

int main(int argc, char** argv)
{
    struct Board board;
    board.size = 6;
    view_draw(&board);

    while (1)
    {
        struct Command command;
        switch (view_input(&command))
        {
            case InputError:
                printf("Error getting input.\n");
                return 1;
                break;
            case InputEof:
                printf("\n");
                return 0;
                break;
            case InputInvalid:
                printf("I didn't understand that.\n");
                break;
            case InputValid:
                switch (command.type)
                {
                    case CommandQuit:
                        return 0;
                };
                break;
        };
    }
    return 0;
}