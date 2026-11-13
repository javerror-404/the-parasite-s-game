from drafter import *
from dataclasses import dataclass

# Constants are allowed (only global *variables* are not), so this is fine.
MAX_MISTAKES = 3


@dataclass
class Puzzle:
    """Second dataclass: one puzzle in the game.
    (Named Puzzle, not Page, because Drafter already has its own Page class.)"""
    prompt: str          # what the player is asked
    answer: str          # the correct answer
    hints: list[str]     # hints that can be revealed, in order (can be empty)
    hints_given: int     # how many of the hints have been revealed so far
    attempts: int        # how many times the player has submitted an answer
    solved: bool         # True once the player answers correctly


@dataclass
class State:
    puzzles: list[Puzzle]  # list of Puzzle instances (riddle, odd one out, name)
    current_page: int      # 1 intro, 2 riddle, 3 odd one out, 4 name, 5 win, 6 game over
    mistakes: int          # wrong answers so far; reaching max_mistakes ends the game
    max_mistakes: int      # how many mistakes are allowed
    is_game_over: bool     # True once the player has lost
    message: str           # feedback shown on a puzzle page (e.g. "Wrong. Try again.")


# ---------- helper functions (these are NOT routes) ----------

def new_puzzles() -> list[Puzzle]:
    """Builds a fresh list of puzzles. Used at startup and on every restart,
    so we never need a global list that gets changed."""
    return [
        Puzzle("What do you call a person who cannot mentally distinguish right from wrong?",
               "insane", [], 0, 0, False),
        Puzzle("Where am I?",
               "R!GHT H3RE", [], 0, 0, False),
        Puzzle("What is my name?",
               "aranea",
               ["I have eight legs.",
                "I spin webs.",
                "My name is the Latin word for what I am, and it starts with 'A'."],
               0, 0, False),
    ]


def current_puzzle(state: State) -> Puzzle:
    """Pages 2, 3, 4 use puzzles[0], puzzles[1], puzzles[2]."""
    return state.puzzles[state.current_page - 2]


def mistake_bar(state: State) -> str:
    """Returns something like 'Mistakes: ☒ ☐ ☐'.
    Loops once per allowed mistake; boxes up to the mistake count are filled."""
    boxes = ""
    for number in range(state.max_mistakes):
        if number < state.mistakes:
            boxes += "☒ "
        else:
            boxes += "☐ "
    return "Mistakes: " + boxes


def count_solved(puzzles: list[Puzzle]) -> int:
    """Loops over the 'solved' attribute of every Puzzle and counts the True ones."""
    total = 0
    for puzzle in puzzles:
        if puzzle.solved:
            total += 1
    return total


def progress_text(state: State) -> str:
    return "Puzzles solved: " + str(count_solved(state.puzzles)) + "/" + str(len(state.puzzles))


# ---------- helper functions that build each page ----------
# ADVANCED TECHNIQUE: these are normal functions that return a Page. The routes
# below call them, which keeps each route short and avoids repeating code.

def intro_page(state: State) -> Page:
    return Page(state, [
        "THE PARASITE'S GAME.",
        "(Arachnophobia Warning)",
        "Begin?",
        Button("Yes", "start"),
        Button("No", "decline"),
    ])


def riddle_page(state: State) -> Page:
    puzzle = current_puzzle(state)
    return Page(state, [
        mistake_bar(state),
        progress_text(state),
        puzzle.prompt,
        TextBox("answer"),
        Button("Submit", "submit"),
        state.message,
    ])


def odd_one_out_page(state: State) -> Page:
    puzzle = current_puzzle(state)
    # The odd option (the "R!GHT") is the 5th of 6. Move it to change the puzzle.
    options = ["R1GHT H3RE", "R1GHT H3RE", "R1GHT H3RE", "R1GHT H3RE",
               "R!GHT H3RE", "R1GHT H3RE"]
    return Page(state, [
        mistake_bar(state),
        progress_text(state),
        puzzle.prompt,
        "🕷️  🕷️  🕷️  🕷️  🕷️  🕷️",
        SelectBox("answer", options),
        Button("Submit", "submit"),
        state.message,
    ])


def name_page(state: State) -> Page:
    puzzle = current_puzzle(state)
    return Page(state, [
        mistake_bar(state),
        progress_text(state),
        puzzle.prompt,
        TextBox("answer"),
        Button("Submit", "submit"),
        Button("Hint", "hint"),
        state.message,
    ])


def win_page(state: State) -> Page:
    content = [
        "🕷️",
        "Your faith is strong, player. You win... for now.",
    ]
    # Loop over every Puzzle and report how many tries it took.
    for puzzle in state.puzzles:
        line = puzzle.prompt + " - " + str(puzzle.attempts) + " attempt(s)"
        if puzzle.hints_given > 0:
            line += ", " + str(puzzle.hints_given) + " hint(s) used"
        content.append(line)
    content.append(Button("Play Again", "back"))
    return Page(state, content)


def lose_page(state: State) -> Page:
    return Page(state, [
        "All " + str(state.max_mistakes) + " mistakes taken.",
        "YOU GAVE IN.",
        "You solved " + str(count_solved(state.puzzles)) + " of " + str(len(state.puzzles)) + " puzzles.",
        Button("Retry", "back"),
    ])


# ---------- routes ----------

@route
def index(state: State) -> Page:
    """Looks at state.current_page and returns the matching page."""
    if state.current_page == 1:
        return intro_page(state)
    elif state.current_page == 2:
        return riddle_page(state)
    elif state.current_page == 3:
        return odd_one_out_page(state)
    elif state.current_page == 4:
        return name_page(state)
    elif state.current_page == 5:
        return win_page(state)
    else:
        return lose_page(state)


@route
def start(state: State) -> Page:
    """The 'Yes' button on the first page: begin the game."""
    state.current_page = 2
    return index(state)


@route
def decline(state: State) -> Page:
    """The 'No' button on the first page."""
    return Page(state, [
        "👀",
        "You're no fun.",
        Button("Back", "back"),
    ])


@route
def submit(state: State, answer: str) -> Page:
    """Checks the answer for whichever puzzle the player is on.
    The right answer is stored in the Puzzle, so one route handles all three.
    ADVANCED TECHNIQUE: .strip().lower() removes extra spaces and ignores
    capital letters, so " Insane " still matches "insane"."""
    # Safety check: only pages 2-4 have puzzles (e.g. the browser's back button
    # could bring someone here from the win page).
    if state.current_page < 2 or state.current_page > 4:
        return index(state)

    puzzle = current_puzzle(state)
    puzzle.attempts += 1

    if answer.strip().lower() == puzzle.answer.lower():
        # Correct: mark it solved and move on (or win if it was the last one).
        puzzle.solved = True
        state.message = ""
        if state.current_page == 4:
            return win(state)
        state.current_page += 1
        return index(state)

    # Wrong: add a mistake, then let game_over decide if that was the last one.
    state.mistakes += 1
    state.message = "Wrong. Try again."
    return game_over(state)


@route
def game_over(state: State) -> Page:
    """Checks the mistakes. If the player has used them all, the game is over;
    otherwise they go back to the puzzle they were on."""
    if state.mistakes >= state.max_mistakes:
        state.is_game_over = True
        state.current_page = 6
        return lose_page(state)
    return index(state)


@route
def win(state: State) -> Page:
    """Called after the last puzzle is answered correctly."""
    state.current_page = 5
    return win_page(state)


@route
def hint(state: State) -> Page:
    """Reveals the next hint for the current puzzle, up to the max for that puzzle."""
    if state.current_page < 2 or state.current_page > 4:
        return index(state)

    puzzle = current_puzzle(state)
    # If a hint was already given, the next click reveals a *different* one,
    # until all of this puzzle's hints have been used.
    if puzzle.hints_given < len(puzzle.hints):
        puzzle.hints_given += 1

    content = ["Hints so far:"]
    # ADVANCED TECHNIQUE: list[:n] is a slice - it takes only the first n items.
    for hint_text in puzzle.hints[:puzzle.hints_given]:
        content.append("- " + hint_text)
    if puzzle.hints_given >= len(puzzle.hints):
        content.append("No more hints.")
    content.append(Button("Back to puzzle", "index"))
    return Page(state, content)


@route
def back(state: State) -> Page:
    """Back to the first page, with everything reset for a new game."""
    state.puzzles = new_puzzles()
    state.current_page = 1
    state.mistakes = 0
    state.is_game_over = False
    state.message = ""
    return index(state)


# ---------- website setup (must come before start_server) ----------

# Shown on the site's "About" page (add --about to the end of your deployed URL).
# Fill in the placeholders with your own details.
set_site_information(
    author="YOUR_EMAIL_HERE",
    description="A spooky trial-and-error puzzle game. Solve three puzzles "
                "before you make three mistakes.",
    sources=["Drafter documentation", "Anthropic's Claude (AI assistant)"],
    planning=["PLANNING_DOC_FILENAME.pdf"],   # the exact name of your uploaded design doc
    links=["https://github.com/YOUR_USERNAME/YOUR_REPO"],
)
hide_debug_information()           # hides the debug panel; comment this out while testing
set_website_title("The Parasite's Game")   # browser tab title
set_website_framed(False)          # fill the whole browser window

# Dark, spooky look. add_website_css("selector", "css rules") styles every
# element of that type on every page.
add_website_css("body", "background-color: #140c18; font-family: Georgia, serif; "
                        "font-size: 20px; text-align: center;")
# The site's built-in theme sets its own text colors, so we list every common
# text element and use !important to make sure our light color wins.
add_website_css("body, div, p, span, label, h1, h2, h3, h4, a",
                "color: #fff4dc !important;")
# Dark input boxes with light text, so typed answers are easy to read too.
add_website_css("input, select, textarea",
                "background-color: #2a1a30 !important; color: #fff4dc !important; "
                "border: 1px solid #b07ab8 !important; font-size: 20px;")
add_website_css("button", "background-color: #5a2a60 !important; color: #ffffff !important; "
                          "border: 1px solid #d9a6e0 !important; font-size: 20px; "
                          "cursor: pointer;")
add_website_css("button:hover", "background-color: #7a3b82 !important;")


start_server(State(puzzles=new_puzzles(), current_page=1, mistakes=0,
                   max_mistakes=MAX_MISTAKES, is_game_over=False, message=""))
