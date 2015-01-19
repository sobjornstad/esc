#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <curses.h>

#define MAX_NUMLENGTH 20

struct stackval {
    bool isEntered;
    char cursor_x;

    char entry[MAX_NUMLENGTH + 1]; // for use while entering; +1 for null
    double floatval; // for use after entering
};

static void finish(int sig);

int main(int argc, char *argv[])
{
    int num = 0;


    /* initialize your non-curses data structures here */

    signal(SIGINT, finish);      /* arrange interrupts to terminate */

    initscr();      /* initialize the curses library */
    keypad(stdscr, TRUE);  /* enable keyboard mapping */
    //nonl();         /* tell curses not to do NL->CR/NL on output */
    cbreak();       /* take input chars one at a time, no wait for \n */
    noecho();         /* echo input - in color */

    //mvhline(1, 0, 0, 4);
    //mvaddstr(2,1, "STACK");

    int parent_x, parent_y;
    getmaxyx(stdscr, parent_y, parent_x);

    WINDOW *status = newwin(1, 50, 0, 0);
    mvwaddstr(status, 0, 0, "[ ]");
    //mvwaddstr(status, 0, 50 - 2, "ic");

    WINDOW *stack = newwin(12, 22, 1, 0);
    //mvwaddch(stack, 1, 1, 'e');
    box(stack, 0, 0);

    wrefresh(status);
    wrefresh(stack);
    wmove(status, 0, 1);


    struct stackval s[10];
    unsigned char slvl = 0;
    char c;
    s[slvl].cursor_x = 0;

    while (1) {
        c = wgetch(status);
        if ( (c >= '0' && c <= '9') || c == '.' ) {
            mvwaddch(stack, 10 - slvl, 1 + s[slvl].cursor_x, c);
            s[slvl].cursor_x++;
            s[slvl].entry[s[slvl].cursor_x] = s[slvl].entry[s[slvl].cursor_x], c;
            // prevent this from overflowing the space
        } else if ( c == '\n' ) {
            s[slvl].entry[++s[slvl].cursor_x] = '\0';
            s[slvl].isEntered = true;
            s[slvl].floatval = atof(s[slvl].entry);
            wprintw(status, "%s", s[slvl].entry);
            //wprintw(status, "%f", s[slvl].floatval);
            slvl++;
            s[slvl].cursor_x = 0;
        } else if ( c == KEY_BACKSPACE || c == KEY_DC || c == 127 ) {
            if ( ! s[slvl].cursor_x == 0 ) {
                s[slvl].cursor_x--;
                mvwaddch(stack, 10 - slvl, 1 + s[slvl].cursor_x, ' ');
                wmove(stack, 10 - slvl, 1 + s[slvl].cursor_x);
            }
        }

        wrefresh(status);
        wrefresh(stack);
    }

    sleep(1);

    finish(0);               /* we're done */
}

static void finish(int sig)
{
    endwin();

    /* do your non-curses wrapup here */

    exit(0);
}
