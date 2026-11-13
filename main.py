from drafter import *
from dataclasses import dataclass

MAX_MISTAKES = 3

@dataclass
class Puzzle:
    """Second dataclass: one puzzle in the game.
    (Named Puzzle, not Page, because Drafter already has its own Page class.)"""
    prompt: str
    answer: str
    hints: list[str]
    hints_given: int
    attempts: int
    solved: bool

@dataclass
class State:
    puzzles: list[Puzzle]
    current_page: int
    mistakes: int
    max_mistakes: int
    is_game_over: bool
    message: int

def new_puzzles() -> list[Puzzle]:
    """Builds a fresh list of puzzles. Used at startup and on every restart,
    so we never need a global list that gets changed."""
    return [
        Puzzle("The more of me there is, the less you can see. What am I?",
       "darkness", [], 0, 0, False),
        Puzzle("Where am I?","R!GHT H3RE", [], 0, 0, False),
        Puzzle("What is my name?",
               "aranea",
               ["I have eight legs.",
                "I spin webs of chaos.",
                "My name is Latin for what I am."],
               0, 0, False)
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

def intro_page(state: State) -> Page:
    return Page(state, [
        "THE PARASITE'S GAME.",
        "Begin?",
        Button("Yes", "start")
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
    options = ["R1GHT H3RE", "R1GHT H3RE", "R1GHT H3RE", "R1GHT H3RE",
"R1GHT H3RE", "R1GHT H3RE", "R!GHT H3RE", "R1GHT H3RE"]
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
        state.message
    ])

def win_page(state: State) -> Page:
    content = [
        "🕷",
        "Your faith is strong, player. You win... for now."
    ]
    for puzzle in state.puzzles:
        line = puzzle.prompt + " - " + str(puzzle.attempts) + "attempt(s)"
        if puzzle.hints_given > 0:
            line += ", " + str(puzzle.hints_given) + " hint(s) used"
            content.append(line)
    content.append(Button("Play Again", "back"))
    return Page(state, content)

def lose_page(state: State) -> Page:
    return Page(state, [
        "All " + str(state.max_mistakes) + "mistakes taken.",
        "YOU GAVE IN.",
        "You solved " +
str(count_solved(state.puzzles)) + " of " +
str(len(state.puzzles)) + " puzzles.",
        Button("Retry", "back"),
    ])

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
    if state.current_page < 2 or state.current_page > 4:
        return index(state)
    puzzle = current_puzzle(state)
    puzzle.attempts += 1
    if answer.strip().lower() == puzzle.answer.lower():
        puzzle.solved = True
        state.message = ""
        if state.current_page == 4:
            return win(state)
        state.current_page += 1
        return index(state)
    state.mistakes += 1
    state.message = "Wrong. Try again."
    return game_over(state)  
    #if state.mistakes >= 3:
        #return game_over(state)

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
def riddle(state: State) -> Page:
    """Reveals the next hint for the current puzzle, up to the max for that puzzle."""
    return Page(state, ["What do you call a person who cannot distinguish right from wrong?",
        TextBox("answer"),
        Button("Submit", "submit")
    ])

@route
def hint(state: State) -> Page:
    if state.current_page < 2 or state.current_page > 4:
        return index(state)
    puzzle = current_puzzle(state)
    if puzzle.hints_given < len(puzzle.hints):
        puzzle.hints_given += 1
        
    content = ["Hints so far:"]
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

hide_debug_information()
set_site_information(
    author="javerror-404",
    description="A trial-and-error puzzle game. Solve three puzzles, before you give in to insanity.",
    sources=["Drafter documentation", "Anthropic's Claude (AI assistant)"],
    planning=["CS1 Final Project 1_Design.pdf", "CS1 Final Project 0_Pick a Problem"],
    links=[https://javerror-404.github.io/the-parasite-s-game/]
    )

set_website_title("The Parasite's Game")
set_website_framed(False)
add_website_css("body", "background-color: #140c18; font-family: Georgia, serif; "
                        "font-size: 20px; text-align: center;")
add_website_css("body, div, p, span, label, h1, h2, h3, h4, a",
                "color: #fff4dc !important;")
add_website_css("input, select, textarea",
                "background-color: #2a1a30 !important; color: #fff4dc !important; "
                "border: 1px solid #b07ab8 !important; font-size: 20px;")
add_website_css("button", "background-color: #5a2a60 !important; color: #ffffff !important; "
                          "border: 1px solid #d9a6e0 !important; font-size: 20px; "
                          "cursor: pointer;")
add_website_css("button:hover", "background-color: #7a3b82 !important;")

start_server(State(puzzles=new_puzzles(), current_page=1, mistakes=0,
                   max_mistakes=MAX_MISTAKES, is_game_over=False, message=""))
