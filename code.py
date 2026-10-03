# ------------------------------------------- Program: MathQuest ------------------------------------------------------
# ------------------------------------------- Author: [Your Name] -----------------------------------------------------
# ------------------------------------------- Assessment: AS91906 -----------------------------------------------------
# ------------------------------------------- Date: 7/30/2026 ---------------------------------------------------------
# ----- Description: A python tkinter program for Flow Computing that helps students practise a range of maths -------
# ----- topics across three difficulty levels, saving each student's progress to a file between sessions. -------------

# -------------------------------- Tkinter importing --------------------------------

import tkinter as tk
from tkinter import *
from tkinter import messagebox
from math import gcd
import os
import random

# -------------------------------- Constants --------------------------------
# Storing these values here means there are no "magic numbers" hidden in the
# functions below, and every setting only needs to be changed in one place.

WINDOW_WIDTH = 900
WINDOW_HEIGHT = 650

COLOR_BACKGROUND = "#eef2fb"
COLOR_PANEL = "#ffffff"
COLOR_PRIMARY = "#4a63e7"
COLOR_PRIMARY_DARK = "#3548b8"
COLOR_SUCCESS = "#2e9e5b"
COLOR_ERROR = "#d64545"
COLOR_TEXT = "#232946"
COLOR_MUTED = "#6b7280"
COLOR_LOCKED = "#c7cbd9"

FONT_TITLE = ("Verdana", 26, "bold")
FONT_HEADING = ("Verdana", 15, "bold")
FONT_BODY = ("Verdana", 12)
FONT_QUESTION = ("Verdana", 19, "bold")
FONT_BUTTON = ("Verdana", 11, "bold")
FONT_SMALL = ("Verdana", 10)

DIFFICULTY_BASIC = "Basic"
DIFFICULTY_ADVANCED = "Advanced"
DIFFICULTY_EXPERT = "Expert"
DIFFICULTIES = [DIFFICULTY_BASIC, DIFFICULTY_ADVANCED, DIFFICULTY_EXPERT]

TOPIC_ARITHMETIC = "Arithmetic"
TOPIC_FRACTIONS = "Fractions"
TOPIC_EXPONENTS = "Exponents & Roots"
TOPIC_ALGEBRA = "Algebra"
TOPIC_GEOMETRY = "Geometry"
TOPIC_STATISTICS = "Statistics"
TOPICS = [TOPIC_ARITHMETIC, TOPIC_FRACTIONS, TOPIC_EXPONENTS, TOPIC_ALGEBRA, TOPIC_GEOMETRY, TOPIC_STATISTICS]

QUESTIONS_PER_ROUND = 10
PASS_THRESHOLD = 0.7  # Scoring 70% or higher in a round unlocks the next difficulty level.
FLOAT_TOLERANCE = 0.1  # Allows for small, reasonable rounding differences in decimal answers.
MAX_ANSWER_MAGNITUDE = 1000000  # Answers further from zero than this are rejected as out of range.
MAX_NAME_LENGTH = 20
PI_APPROXIMATION = 3.14159
PROGRESS_FILE = "studentProgress.txt"

# -------------------------------- Fraction class (custom data type) --------------------------------


class Fraction:
    # A custom data type representing a maths fraction, always stored in its lowest terms.
    # Any negative sign is kept on the numerator so the denominator is never negative, which
    # means two equal fractions (like 2/4 and 1/2) always end up stored identically.

    def __init__(self, numerator, denominator):
        if denominator == 0:
            raise ValueError("A fraction cannot have a denominator of zero.")
        if denominator < 0:
            numerator, denominator = -numerator, -denominator
        divisor = gcd(abs(numerator), denominator) or 1
        self.numerator = numerator // divisor
        self.denominator = denominator // divisor

    def __add__(self, other):
        return Fraction(self.numerator * other.denominator + other.numerator * self.denominator,
                         self.denominator * other.denominator)

    def __sub__(self, other):
        return Fraction(self.numerator * other.denominator - other.numerator * self.denominator,
                         self.denominator * other.denominator)

    def __mul__(self, other):
        return Fraction(self.numerator * other.numerator, self.denominator * other.denominator)

    def __truediv__(self, other):
        if other.numerator == 0:
            raise ZeroDivisionError("Cannot divide by a fraction that is equal to zero.")
        return Fraction(self.numerator * other.denominator, self.denominator * other.numerator)

    def __eq__(self, other):
        if not isinstance(other, Fraction):
            return NotImplemented
        return self.numerator == other.numerator and self.denominator == other.denominator

    def __hash__(self):
        return hash((self.numerator, self.denominator))

    def __str__(self):
        # Whole numbers are shown without a denominator, e.g. "2" instead of "2/1".
        if self.denominator == 1:
            return str(self.numerator)
        return f"{self.numerator}/{self.denominator}"

    def to_float(self):
        # Returns the fraction as a decimal value. Used for range checks and sorting.
        return self.numerator / self.denominator

    @staticmethod
    def from_string(text):
        # Parses text such as "3/4" or "5" into a Fraction object.
        # Raises a ValueError with a friendly message if the text cannot be understood.
        text = text.strip()
        if "/" in text:
            parts = text.split("/")
            if len(parts) != 2:
                raise ValueError("Write fractions with a single slash, e.g. 3/4.")
            numerator_text, denominator_text = parts[0].strip(), parts[1].strip()
            if not is_signed_integer(numerator_text) or not is_signed_integer(denominator_text):
                raise ValueError("Both parts of a fraction must be whole numbers, e.g. 3/4.")
            return Fraction(int(numerator_text), int(denominator_text))
        if not is_signed_integer(text):
            raise ValueError("Enter a whole number or a fraction such as 3/4.")
        return Fraction(int(text), 1)


def is_signed_integer(text):
    # Returns True if text is a whole number, optionally starting with a minus sign.
    if text.startswith("-"):
        text = text[1:]
    return text.isdigit() and text != ""


# -------------------------------- StudentProgress class --------------------------------


class StudentProgress:
    # Stores one student's saved progress (unlocked levels and scores) across every topic.
    # An object of this class is created for whichever student has typed their name in, and
    # is saved to and loaded from studentProgress.txt between sessions.

    def __init__(self, name, topic_data=None):
        self.name = name
        self.topic_data = topic_data if topic_data is not None else self.blank_topic_data()

    def blank_topic_data(self):
        # Builds a fresh progress record for a brand new student, with only Basic unlocked.
        return {topic: {"unlocked": [DIFFICULTY_BASIC], "best": {}, "attempts": {}, "correct": {}}
                for topic in TOPICS}

    def is_unlocked(self, topic, difficulty):
        return difficulty in self.topic_data[topic]["unlocked"]

    def accuracy(self, topic, difficulty):
        # Returns accuracy as a percentage, or None if that level has not been attempted yet.
        attempts = self.topic_data[topic]["attempts"].get(difficulty, 0)
        if attempts == 0:
            return None
        correct = self.topic_data[topic]["correct"].get(difficulty, 0)
        return round((correct / attempts) * 100, 1)

    def totals(self):
        # Returns (total_attempts, total_correct, topics_past_basic) across every topic, used by
        # the all-students overview window on the starting screen.
        total_attempts = 0
        total_correct = 0
        topics_past_basic = 0
        for topic in TOPICS:
            data = self.topic_data[topic]
            total_attempts += sum(data["attempts"].values())
            total_correct += sum(data["correct"].values())
            if len(data["unlocked"]) > 1:
                topics_past_basic += 1
        return total_attempts, total_correct, topics_past_basic

    def record_round(self, topic, difficulty, correct_count, total_count):
        # Updates the stored stats after a round, unlocking the next difficulty if it was
        # earned. Returns the name of the newly unlocked difficulty, or None otherwise.
        data = self.topic_data[topic]
        data["attempts"][difficulty] = data["attempts"].get(difficulty, 0) + total_count
        data["correct"][difficulty] = data["correct"].get(difficulty, 0) + correct_count
        data["best"][difficulty] = max(data["best"].get(difficulty, 0), correct_count)

        if total_count > 0 and (correct_count / total_count) >= PASS_THRESHOLD:
            next_difficulty = self.next_difficulty(difficulty)
            if next_difficulty and next_difficulty not in data["unlocked"]:
                data["unlocked"].append(next_difficulty)
                return next_difficulty
        return None

    def next_difficulty(self, difficulty):
        # Returns the difficulty after the one given, or None if it was already Expert.
        index = DIFFICULTIES.index(difficulty)
        if index + 1 < len(DIFFICULTIES):
            return DIFFICULTIES[index + 1]
        return None

    def to_lines(self):
        # Converts this student's progress into a list of plain text lines, ready to be
        # written to studentProgress.txt - one "Topic:" line per topic, in a fixed order.
        lines = [f"Name: {self.name}"]
        for topic in TOPICS:
            data = self.topic_data[topic]
            line = (f"Topic: {topic} | Unlocked: {','.join(data['unlocked'])} | "
                    f"Attempts: {format_counts(data['attempts'])} | "
                    f"Correct: {format_counts(data['correct'])} | "
                    f"Best: {format_counts(data['best'])}")
            lines.append(line)
        return lines

    @staticmethod
    def from_lines(lines):
        # Rebuilds a StudentProgress object from the lines written by to_lines.
        name = lines[0].split("Name:")[1].strip()
        topic_data = {}
        for line in lines[1:]:
            if not line.startswith("Topic:"):
                continue
            sections = [section.strip() for section in line.split("|")]
            topic = sections[0].split("Topic:")[1].strip()
            unlocked_text = sections[1].split("Unlocked:")[1].strip()
            topic_data[topic] = {
                "unlocked": unlocked_text.split(",") if unlocked_text else [DIFFICULTY_BASIC],
                "attempts": parse_counts(sections[2].split("Attempts:")[1].strip()),
                "correct": parse_counts(sections[3].split("Correct:")[1].strip()),
                "best": parse_counts(sections[4].split("Best:")[1].strip()),
            }
        return StudentProgress(name, topic_data)


def format_counts(counts_dict):
    # Turns a dictionary like {"Basic": 8, "Advanced": 3} into "Basic:8,Advanced:3" for saving.
    return ",".join(f"{key}:{value}" for key, value in counts_dict.items())


def parse_counts(text):
    # Reverses format_counts, turning "Basic:8,Advanced:3" back into {"Basic": 8, "Advanced": 3}.
    counts = {}
    if not text:
        return counts
    for pair in text.split(","):
        key, value = pair.split(":")
        counts[key] = int(value)
    return counts


# -------------------------------- Saving and loading progress (file handling) --------------------------------
# Every student's progress is stored as a block of text in studentProgress.txt, with each
# Block separated by "===" on its own line - the same pattern used for receipts.txt in the
# Party Hire program.


def load_all_progress():
    # Returns a dictionary of {name: StudentProgress} for every student saved so far.
    # Returns an empty dictionary if the save file is missing, empty or damaged, so a bad
    # file never crashes the program.
    if not os.path.exists(PROGRESS_FILE):
        return {}
    with open(PROGRESS_FILE, "r") as file:
        content = file.read().strip()
    if not content:
        return {}

    all_progress = {}
    blocks = [block.strip() for block in content.split("\n===\n") if block.strip()]
    for block in blocks:
        try:
            progress = StudentProgress.from_lines(block.splitlines())
            all_progress[progress.name] = progress
        except (IndexError, ValueError):
            continue  # Skips one corrupted block instead of losing every student's progress.
    return all_progress


def load_student_progress(name):
    # Returns the saved StudentProgress for name, or a brand new one if they have not played before.
    all_progress = load_all_progress()
    return all_progress.get(name, StudentProgress(name))


def save_student_progress(progress):
    # Saves one student's progress, keeping every other student's saved progress intact.
    all_progress = load_all_progress()
    all_progress[progress.name] = progress
    blocks = ["\n".join(student.to_lines()) for student in all_progress.values()]
    with open(PROGRESS_FILE, "w") as file:
        file.write("\n===\n".join(blocks) + "\n===\n" if blocks else "")


# -------------------------------- Generating maths problems --------------------------------
# Each question is represented as a dictionary with four keys: "question" (the text shown to
# the student), "answer" (the correct value), "type" ("int", "float" or "fraction", which
# tells check_answer how to mark it), and "working" (an optional short hint shown if the
# student gets the question wrong).


def generate_problem(topic, difficulty):
    # Returns one randomly generated question dictionary for the chosen topic and difficulty.
    generators = {
        TOPIC_ARITHMETIC: generate_arithmetic_problem,
        TOPIC_FRACTIONS: generate_fractions_problem,
        TOPIC_EXPONENTS: generate_exponents_problem,
        TOPIC_ALGEBRA: generate_algebra_problem,
        TOPIC_GEOMETRY: generate_geometry_problem,
        TOPIC_STATISTICS: generate_statistics_problem,
    }
    return generators[topic](difficulty)


def generate_arithmetic_problem(difficulty):
    if difficulty == DIFFICULTY_BASIC:
        first_number, second_number = random.randint(1, 20), random.randint(1, 20)
        if random.choice([True, False]):
            return {"question": f"Calculate: {first_number} + {second_number}",
                     "answer": first_number + second_number, "type": "int", "working": ""}
        larger, smaller = max(first_number, second_number), min(first_number, second_number)
        return {"question": f"Calculate: {larger} - {smaller}", "answer": larger - smaller,
                 "type": "int", "working": ""}

    if difficulty == DIFFICULTY_ADVANCED:
        if random.choice([True, False]):
            first_number, second_number = random.randint(2, 12), random.randint(2, 12)
            return {"question": f"Calculate: {first_number} x {second_number}",
                     "answer": first_number * second_number, "type": "int", "working": ""}
        quotient, divisor = random.randint(2, 12), random.randint(2, 12)
        dividend = quotient * divisor
        return {"question": f"Calculate: {dividend} ÷ {divisor}", "answer": quotient,
                 "type": "int", "working": ""}

    # Expert level uses two-step calculations that require order of operations.
    first_number, second_number, multiplier = random.randint(2, 30), random.randint(2, 30), random.randint(2, 12)
    working = "Work out the brackets first, then multiply (order of operations)."
    if random.choice([True, False]):
        question = f"Calculate: ({first_number} + {second_number}) x {multiplier}"
        return {"question": question, "answer": (first_number + second_number) * multiplier,
                 "type": "int", "working": working}
    larger, smaller = max(first_number, second_number), min(first_number, second_number)
    question = f"Calculate: ({larger} - {smaller}) x {multiplier}"
    return {"question": question, "answer": (larger - smaller) * multiplier, "type": "int", "working": working}


def generate_fractions_problem(difficulty):
    if difficulty == DIFFICULTY_BASIC:
        base_denominator = random.randint(2, 12)
        base_numerator = random.randint(1, base_denominator - 1)
        scale = random.randint(2, 6)
        shown_numerator = base_numerator * scale
        shown_denominator = base_denominator * scale
        answer = Fraction(shown_numerator, shown_denominator)  # Simplifies automatically.
        question = f"Simplify the fraction {shown_numerator}/{shown_denominator} to its lowest terms."
        working = "Divide the numerator and denominator by their highest common factor."
        return {"question": question, "answer": answer, "type": "fraction", "working": working}

    if difficulty == DIFFICULTY_ADVANCED:
        first_fraction = Fraction(random.randint(1, 5), random.randint(2, 8))
        second_fraction = Fraction(random.randint(1, 5), random.randint(2, 8))
        working = "Find a common denominator before adding or subtracting."
        if random.choice([True, False]):
            question = f"Calculate {first_fraction} + {second_fraction}. Give your answer as a simplified fraction."
            return {"question": question, "answer": first_fraction + second_fraction, "type": "fraction", "working": working}
        bigger, smaller = sorted((first_fraction, second_fraction), key=lambda f: f.to_float(), reverse=True)
        question = f"Calculate {bigger} - {smaller}. Give your answer as a simplified fraction."
        return {"question": question, "answer": bigger - smaller, "type": "fraction", "working": working}

    # Expert level multiplies and divides fractions.
    first_fraction = Fraction(random.randint(1, 6), random.randint(2, 9))
    second_fraction = Fraction(random.randint(1, 6), random.randint(2, 9))
    if random.choice([True, False]):
        question = f"Calculate {first_fraction} x {second_fraction}. Give your answer as a simplified fraction."
        working = "Multiply the numerators, then multiply the denominators."
        return {"question": question, "answer": first_fraction * second_fraction, "type": "fraction", "working": working}
    question = f"Calculate {first_fraction} ÷ {second_fraction}. Give your answer as a simplified fraction."
    working = "To divide fractions, multiply by the reciprocal of the second fraction."
    return {"question": question, "answer": first_fraction / second_fraction, "type": "fraction", "working": working}


def generate_exponents_problem(difficulty):
    if difficulty == DIFFICULTY_BASIC:
        base, exponent = random.randint(2, 10), random.randint(2, 3)
        return {"question": f"Calculate: {base}^{exponent}", "answer": base ** exponent, "type": "int", "working": ""}

    if difficulty == DIFFICULTY_ADVANCED:
        if random.choice([True, False]):
            base, exponent = random.randint(2, 12), random.randint(2, 4)
            return {"question": f"Calculate: {base}^{exponent}", "answer": base ** exponent, "type": "int", "working": ""}
        root_value = random.randint(2, 15)
        question = f"Calculate the square root of {root_value * root_value}."
        return {"question": question, "answer": root_value, "type": "int", "working": ""}

    # Expert level covers negative exponents and cube roots.
    if random.choice([True, False]):
        base, exponent = random.randint(2, 6), random.randint(1, 3)
        question = f"Calculate: {base}^-{exponent} (give your answer as a fraction)"
        working = "A negative exponent means 1 over the base raised to the positive exponent."
        return {"question": question, "answer": Fraction(1, base ** exponent), "type": "fraction", "working": working}
    root_value = random.randint(2, 10)
    question = f"Calculate the cube root of {root_value ** 3}."
    return {"question": question, "answer": root_value, "type": "int", "working": ""}


def generate_algebra_problem(difficulty):
    if difficulty == DIFFICULTY_BASIC:
        x_value = random.randint(1, 20)
        constant = random.randint(1, 15)
        result = x_value + constant
        question = f"Solve for x: x + {constant} = {result}"
        return {"question": question, "answer": x_value, "type": "int",
                 "working": "Subtract the constant from both sides to isolate x."}

    if difficulty == DIFFICULTY_ADVANCED:
        coefficient = random.randint(2, 9)
        x_value = random.randint(1, 15)
        constant = random.randint(1, 20)
        result = coefficient * x_value + constant
        question = f"Solve for x: {coefficient}x + {constant} = {result}"
        working = "Subtract the constant, then divide both sides by the coefficient of x."
        return {"question": question, "answer": x_value, "type": "int", "working": working}

    # Expert level puts x on both sides of the equation.
    x_value = random.randint(1, 12)
    coefficient_left = random.randint(3, 9)
    coefficient_right = random.randint(1, coefficient_left - 1)  # Keeps the equation solvable.
    constant_left = random.randint(1, 20)
    constant_right = (coefficient_left - coefficient_right) * x_value + constant_left
    question = f"Solve for x: {coefficient_left}x + {constant_left} = {coefficient_right}x + {constant_right}"
    working = "Move the x terms to one side and the numbers to the other, then divide."
    return {"question": question, "answer": x_value, "type": "int", "working": working}


def generate_geometry_problem(difficulty):
    if difficulty == DIFFICULTY_BASIC:
        length, width = random.randint(2, 20), random.randint(2, 20)
        question = f"Calculate the area of a rectangle with length {length}cm and width {width}cm."
        return {"question": question, "answer": float(length * width), "type": "float",
                 "working": "Area of a rectangle = length x width."}

    if difficulty == DIFFICULTY_ADVANCED:
        if random.choice([True, False]):
            base, height = random.randint(4, 20), random.randint(4, 20)
            answer = round(base * height / 2, 2)
            question = f"Calculate the area of a triangle with base {base}cm and height {height}cm."
            return {"question": question, "answer": answer, "type": "float",
                     "working": "Area of a triangle = (base x height) / 2."}
        radius = random.randint(2, 15)
        answer = round(PI_APPROXIMATION * radius ** 2, 2)
        question = (f"Calculate the area of a circle with radius {radius}cm. "
                    f"Use {PI_APPROXIMATION} for pi, rounded to 2 decimal places.")
        return {"question": question, "answer": answer, "type": "float", "working": "Area of a circle = pi x radius^2."}

    # Expert level calculates the volume of a cylinder.
    radius, height = random.randint(2, 10), random.randint(4, 20)
    answer = round(PI_APPROXIMATION * radius ** 2 * height, 2)
    question = (f"Calculate the volume of a cylinder with radius {radius}cm and height {height}cm. "
                f"Use {PI_APPROXIMATION} for pi, rounded to 2 decimal places.")
    return {"question": question, "answer": answer, "type": "float", "working": "Volume of a cylinder = pi x radius^2 x height."}


def generate_statistics_problem(difficulty):
    # Uses plain Python (no external libraries) for the statistics calculations below,
    # so the program has no dependencies beyond the standard library.
    if difficulty == DIFFICULTY_BASIC:
        values = [random.randint(1, 20) for _ in range(5)]
        answer = round(sum(values) / len(values), 2)
        question = f"Calculate the mean of this data set: {values}"
        return {"question": question, "answer": answer, "type": "float",
                 "working": "Mean = the total of all values divided by how many there are."}

    if difficulty == DIFFICULTY_ADVANCED:
        values = [random.randint(1, 50) for _ in range(7)]
        sorted_values = sorted(values)
        middle_index = len(sorted_values) // 2
        if len(sorted_values) % 2 == 1:
            median = float(sorted_values[middle_index])
        else:
            median = (sorted_values[middle_index - 1] + sorted_values[middle_index]) / 2
        answer = round(median, 2)
        question = f"Find the median of this data set: {sorted_values}"
        return {"question": question, "answer": answer, "type": "float",
                 "working": "The median is the middle value once the data is sorted."}

    # Expert level asks for the range of a data set.
    values = [random.randint(1, 40) for _ in range(6)]
    answer = max(values) - min(values)
    question = f"Find the range of this data set: {values}"
    return {"question": question, "answer": answer, "type": "int",
             "working": "Range = the largest value minus the smallest value."}


# -------------------------------- Marking answers --------------------------------


def check_answer(problem, raw_input):
    # Validates and marks a typed answer against problem. Returns a tuple of (status, message)
    # where status is "correct", "incorrect" or "invalid". Keeping all of this logic in one
    # place means every window below marks answers in exactly the same, tested way.
    raw_input = raw_input.strip()
    if not raw_input:
        return "invalid", "Please type an answer before submitting."

    answer_type = problem["type"]
    try:
        if answer_type == "int":
            if not is_signed_integer(raw_input):
                raise ValueError("Please enter a whole number, with no letters, symbols or decimals.")
            parsed_value = int(raw_input)
        elif answer_type == "float":
            try:
                parsed_value = float(raw_input)
            except ValueError:
                raise ValueError("Please enter a number (e.g. 4 or 4.5), with no letters or symbols.")
            if parsed_value != parsed_value or parsed_value in (float("inf"), float("-inf")):
                # parsed_value != parsed_value is only True for NaN; this also catches inf and -inf.
                raise ValueError("Please enter a real, finite number.")
        elif answer_type == "fraction":
            parsed_value = Fraction.from_string(raw_input)
        else:
            raise ValueError("Internal error: unknown answer type.")
    except (ValueError, ZeroDivisionError) as error:
        return "invalid", str(error)

    magnitude = parsed_value.to_float() if isinstance(parsed_value, Fraction) else parsed_value
    if abs(magnitude) > MAX_ANSWER_MAGNITUDE:
        return "invalid", f"That answer is outside the accepted range (-{MAX_ANSWER_MAGNITUDE:,} to {MAX_ANSWER_MAGNITUDE:,})."

    if answer_type == "float":
        is_correct = abs(parsed_value - problem["answer"]) <= FLOAT_TOLERANCE
    else:
        is_correct = parsed_value == problem["answer"]

    if is_correct:
        return "correct", "Correct! Well done."
    explanation = f" {problem['working']}" if problem["working"] else ""
    return "incorrect", f"Not quite. The correct answer was {problem['answer']}.{explanation}"


# ======================================================================================
# Everything below this line builds the tkinter interface. None of it does any maths or
# file handling itself - it only ever calls the tested functions above, which keeps the
# interface and the underlying logic cleanly separated.
# ======================================================================================

# -------------------------------- Root window setup --------------------------------
# Minimises the root window on launch, matching the pattern used throughout this program:
# every "screen" is really its own Toplevel window, opened and closed by switch_window.

root = Tk()
root.title("MathQuest")
root.geometry("1x1")
root.iconify()

# Global variables shared between window functions, since each window is only created when
# it is needed rather than being kept around like an object's attributes would be.
current_progress = None
quiz_topic = None
quiz_difficulty = None
last_round_score = 0
last_round_unlocked = None

# navigation_history is a stack (a complex data structure): every time the program moves
# forward to a new screen via go_to, the screen being left is pushed on. The Back button on
# each screen calls go_back, which pops the most recent one off and returns to it - so Back
# always goes to wherever the student actually came from, not a fixed "main menu".
navigation_history = []

# -------------------------------- Shared helper functions --------------------------------


def switch_window(current_window, new_window):
    # Destroys the current window and opens the next one. This is the low-level building
    # block that every navigation in this program is built on top of.
    current_window.destroy()
    root.iconify()
    new_window()


def go_to(current_window, current_window_function, new_window):
    # Moves forward to a new screen, pushing the screen being left onto navigation_history
    # so the Back button can return to it later.
    navigation_history.append(current_window_function)
    switch_window(current_window, new_window)


def go_back(current_window):
    # Returns to whichever screen is on top of navigation_history, matching the pattern of a
    # normal Back button. Falls back to the topic screen if the history is somehow empty.
    previous_window = navigation_history.pop() if navigation_history else topic_window
    switch_window(current_window, previous_window)


def center_window(window, width, height):
    # Sizes and centres a Toplevel window on the screen. Pulling this out into its own
    # function avoids repeating the same calculation in every window function below.
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width / 2) - (width / 2)
    y = (screen_height / 2) - (height / 2)
    window.geometry(f"{width}x{height}+{int(x)}+{int(y)}")
    window.resizable(False, False)


def add_hover_effect(button, normal_color, hover_color):
    # Swaps a button's background colour on mouse hover, matching the effect used on every
    # button in this program.
    button.bind("<Enter>", lambda event: button.config(bg=hover_color))
    button.bind("<Leave>", lambda event: button.config(bg=normal_color))


def add_exit_button(window):
    # Adds a consistent Exit button to the top-right corner of window, since every window
    # here has no title bar and therefore no built-in close button.
    exit_btn = Button(window, text="Exit", font=FONT_SMALL, bg="red", fg="white",
                      borderwidth=3, relief=RAISED, cursor="hand2", command=quit)
    exit_btn.place(x=WINDOW_WIDTH - 100, y=20)
    add_hover_effect(exit_btn, "red", "#444")


def add_back_button(window, on_click):
    # Adds a consistent Back button to the top-left corner of window.
    back_btn = Button(window, text="< Back", font=FONT_SMALL, bg=COLOR_PANEL, fg=COLOR_PRIMARY,
                      borderwidth=3, relief=RAISED, cursor="hand2", command=on_click)
    back_btn.place(x=20, y=20)
    add_hover_effect(back_btn, COLOR_PANEL, COLOR_BACKGROUND)


def start_quiz(current_window, topic, difficulty):
    # Records which topic and difficulty were chosen, then moves to the quiz window.
    global quiz_topic, quiz_difficulty
    quiz_topic = topic
    quiz_difficulty = difficulty
    go_to(current_window, topic_window, quiz_window)


# -------------------------------- Creating Start Window --------------------------------


def starting_window():
    start_window = tk.Toplevel()
    center_window(start_window, WINDOW_WIDTH, WINDOW_HEIGHT)
    start_window.overrideredirect(True)
    start_window.configure(bg=COLOR_BACKGROUND, borderwidth=15, relief=RAISED)

    # Brings this window back up if the hidden root window is ever refocused.
    root.bind("<FocusIn>", lambda event: switch_window(start_window, starting_window))

    add_exit_button(start_window)

    Label(start_window, text="MathQuest", font=FONT_TITLE, bg=COLOR_BACKGROUND, fg=COLOR_PRIMARY).pack(pady=(55, 10))
    Label(start_window, text="Practise maths and level up at your own pace.", font=FONT_BODY,
          bg=COLOR_BACKGROUND, fg=COLOR_MUTED).pack(pady=(0, 30))

    card = Frame(start_window, bg=COLOR_PANEL, borderwidth=5, relief=RAISED, padx=40, pady=30)
    card.pack()
    Label(card, text="Enter your name to begin:", font=FONT_HEADING, bg=COLOR_PANEL, fg=COLOR_TEXT).pack(pady=(0, 15))

    name_var = tk.StringVar()

    def validate_name_char(proposed_text):
        if len(proposed_text) > MAX_NAME_LENGTH:
            return False
        return all(character.isalpha() or character in " -'" for character in proposed_text)

    name_vcmd = start_window.register(validate_name_char)
    name_entry = Entry(card, textvariable=name_var, font=FONT_BODY, width=25, justify="center",
                       validate="key", validatecommand=(name_vcmd, "%P"))
    name_entry.pack(ipady=6)
    name_entry.focus_set()

    def continue_to_topics():
        global current_progress
        name = name_var.get().strip()
        if not name:
            messagebox.showwarning("Name Required", "Please enter your name before continuing.")
            return
        current_progress = load_student_progress(name)
        navigation_history.clear()  # Starting a fresh session, so any old Back history is cleared.
        go_to(start_window, starting_window, topic_window)

    name_entry.bind("<Return>", lambda event: continue_to_topics())

    continue_btn = Button(card, text="Continue", font=FONT_BUTTON, bg=COLOR_PRIMARY, fg="white",
                          borderwidth=3, relief=RAISED, cursor="hand2", command=continue_to_topics)
    continue_btn.pack(pady=(20, 0))
    add_hover_effect(continue_btn, COLOR_PRIMARY, COLOR_PRIMARY_DARK)

    all_students_btn = Button(start_window, text="View All Students' Progress", font=FONT_BUTTON,
                             bg=COLOR_PANEL, fg=COLOR_PRIMARY, borderwidth=2, relief=RAISED, cursor="hand2",
                             command=lambda: go_to(start_window, starting_window, all_students_window))
    all_students_btn.pack(pady=25)
    add_hover_effect(all_students_btn, COLOR_PANEL, COLOR_BACKGROUND)


# -------------------------------- Creating All Students Window --------------------------------


def all_students_window():
    # Reads studentProgress.txt directly (through load_all_progress) so this always shows
    # every student who has ever played, not just the one currently signed in.
    all_win = tk.Toplevel()
    center_window(all_win, WINDOW_WIDTH, WINDOW_HEIGHT)
    all_win.overrideredirect(True)
    all_win.configure(bg=COLOR_BACKGROUND, borderwidth=15, relief=RAISED)

    add_exit_button(all_win)
    add_back_button(all_win, lambda: go_back(all_win))

    Label(all_win, text="All Students' Progress", font=FONT_TITLE, bg=COLOR_BACKGROUND, fg=COLOR_PRIMARY).pack(pady=(30, 15))

    all_progress = load_all_progress()

    table_frame = Frame(all_win, bg=COLOR_BACKGROUND)
    table_frame.pack(padx=40, fill=BOTH, expand=True)

    headers = ["Student", "Questions Answered", "Overall Accuracy", "TPB"]
    for column, text in enumerate(headers):
        Label(table_frame, text=text, font=FONT_HEADING, bg=COLOR_BACKGROUND, fg=COLOR_TEXT).grid(
            row=0, column=column, padx=14, pady=8, sticky="w")

    if not all_progress:
        Label(table_frame, text="No students have played yet.", font=FONT_BODY, bg=COLOR_BACKGROUND,
              fg=COLOR_MUTED).grid(row=1, column=0, columnspan=4, padx=14, pady=10, sticky="w")

    for row_index, name in enumerate(sorted(all_progress.keys()), start=1):
        total_attempts, total_correct, topics_past_basic = all_progress[name].totals()
        accuracy_text = f"{round((total_correct / total_attempts) * 100, 1)}%" if total_attempts > 0 else "N/A"

        Label(table_frame, text=name, font=FONT_BODY, bg=COLOR_BACKGROUND, fg=COLOR_TEXT).grid(
            row=row_index, column=0, padx=14, pady=4, sticky="w")
        Label(table_frame, text=str(total_attempts), font=FONT_BODY, bg=COLOR_BACKGROUND, fg=COLOR_TEXT).grid(
            row=row_index, column=1, padx=14, pady=4, sticky="w")
        Label(table_frame, text=accuracy_text, font=FONT_BODY, bg=COLOR_BACKGROUND, fg=COLOR_TEXT).grid(
            row=row_index, column=2, padx=14, pady=4, sticky="w")
        Label(table_frame, text=f"{topics_past_basic} of {len(TOPICS)}", font=FONT_BODY, bg=COLOR_BACKGROUND,
              fg=COLOR_TEXT).grid(row=row_index, column=3, padx=14, pady=4, sticky="w")


# -------------------------------- Creating Topic Select Window --------------------------------


def topic_window():
    topic_win = tk.Toplevel()
    center_window(topic_win, WINDOW_WIDTH, WINDOW_HEIGHT)
    topic_win.overrideredirect(True)
    topic_win.configure(bg=COLOR_BACKGROUND, borderwidth=15, relief=RAISED)

    add_exit_button(topic_win)
    add_back_button(topic_win, lambda: go_back(topic_win))

    Label(topic_win, text=f"Welcome back, {current_progress.name}!", font=FONT_HEADING,
          bg=COLOR_BACKGROUND, fg=COLOR_TEXT).pack(pady=(25, 5))
    Label(topic_win, text="Choose a topic and difficulty to start practising:", font=FONT_BODY,
          bg=COLOR_BACKGROUND, fg=COLOR_MUTED).pack(pady=(0, 15))

    topics_frame = Frame(topic_win, bg=COLOR_BACKGROUND)
    topics_frame.pack(fill=BOTH, expand=True, padx=30)

    for topic in TOPICS:
        row = Frame(topics_frame, bg=COLOR_PANEL, borderwidth=3, relief=GROOVE, padx=15, pady=10)
        row.pack(fill=X, pady=6)
        Label(row, text=topic, font=FONT_HEADING, bg=COLOR_PANEL, fg=COLOR_TEXT, width=15, anchor="w").pack(side=LEFT)

        for difficulty in DIFFICULTIES:
            unlocked = current_progress.is_unlocked(topic, difficulty)
            accuracy = current_progress.accuracy(topic, difficulty)
            if not unlocked:
                label_text = f"{difficulty} (Locked)"
            elif accuracy is None:
                label_text = difficulty
            else:
                label_text = f"{difficulty} ({accuracy}%)"

            difficulty_btn = Button(row, text=label_text, font=FONT_SMALL, width=16,
                                    bg=COLOR_PRIMARY if unlocked else COLOR_LOCKED,
                                    fg="white" if unlocked else COLOR_MUTED,
                                    state=NORMAL if unlocked else DISABLED,
                                    borderwidth=2, relief=RAISED,
                                    cursor="hand2" if unlocked else "arrow",
                                    command=lambda t=topic, d=difficulty: start_quiz(topic_win, t, d))
            difficulty_btn.pack(side=LEFT, padx=6)
            if unlocked:
                add_hover_effect(difficulty_btn, COLOR_PRIMARY, COLOR_PRIMARY_DARK)

    bottom_bar = Frame(topic_win, bg=COLOR_BACKGROUND)
    bottom_bar.pack(pady=15)

    stats_btn = Button(bottom_bar, text="View My Stats", font=FONT_BUTTON, bg=COLOR_PANEL, fg=COLOR_PRIMARY,
                       borderwidth=2, relief=RAISED, cursor="hand2",
                       command=lambda: go_to(topic_win, topic_window, stats_window))
    stats_btn.pack(side=LEFT, padx=8)
    add_hover_effect(stats_btn, COLOR_PANEL, COLOR_BACKGROUND)

    switch_btn = Button(bottom_bar, text="Switch Student", font=FONT_BUTTON, bg=COLOR_PANEL, fg=COLOR_MUTED,
                        borderwidth=2, relief=RAISED, cursor="hand2",
                        command=lambda: (navigation_history.clear(), switch_window(topic_win, starting_window)))
    switch_btn.pack(side=LEFT, padx=8)
    add_hover_effect(switch_btn, COLOR_PANEL, COLOR_BACKGROUND)


# -------------------------------- Creating Quiz Window --------------------------------


def quiz_window():
    quiz_win = tk.Toplevel()
    center_window(quiz_win, WINDOW_WIDTH, WINDOW_HEIGHT)
    quiz_win.overrideredirect(True)
    quiz_win.configure(bg=COLOR_BACKGROUND, borderwidth=15, relief=RAISED)

    add_exit_button(quiz_win)

    # quiz_state holds the current question in a dictionary so the nested functions below can
    # update it without needing a nonlocal declaration. question_number_var and correct_count_var
    # use tkinter's own variable classes for the same reason, and so labels can watch them.
    quiz_state = {"problem": None}
    question_number_var = tk.IntVar(value=0)
    correct_count_var = tk.IntVar(value=0)

    def quit_to_menu():
        if question_number_var.get() > 0:
            confirmed = messagebox.askyesno("Quit Round?",
                                             "Your progress in this round will not be saved. Are you sure?")
            if not confirmed:
                return
        go_back(quiz_win)

    add_back_button(quiz_win, quit_to_menu)

    header_label = Label(quiz_win, font=FONT_BODY, bg=COLOR_BACKGROUND, fg=COLOR_MUTED)
    header_label.pack(pady=(20, 5))

    progress_canvas = Canvas(quiz_win, width=420, height=14, bg=COLOR_LOCKED, highlightthickness=0)
    progress_canvas.pack(pady=5)
    progress_bar = progress_canvas.create_rectangle(0, 0, 0, 14, fill=COLOR_PRIMARY, width=0)

    card = Frame(quiz_win, bg=COLOR_PANEL, borderwidth=5, relief=RAISED, padx=40, pady=30)
    card.pack(pady=15)

    question_label = Label(card, font=FONT_QUESTION, bg=COLOR_PANEL, fg=COLOR_TEXT, wraplength=500, justify="center")
    question_label.pack(pady=(0, 20))

    answer_var = tk.StringVar()

    def validate_answer_char(proposed_text):
        # Blocks any keystroke that could never be part of a whole number, decimal or fraction.
        allowed_characters = set("-0123456789./")
        return all(character in allowed_characters for character in proposed_text)

    answer_vcmd = quiz_win.register(validate_answer_char)
    answer_entry = Entry(card, textvariable=answer_var, font=FONT_BODY, width=18, justify="center",
                         validate="key", validatecommand=(answer_vcmd, "%P"))
    answer_entry.pack(ipady=6)

    def load_next_question():
        # Displays the next question, or finishes the round once ten have been answered.
        if question_number_var.get() >= QUESTIONS_PER_ROUND:
            finish_round()
            return
        question_number_var.set(question_number_var.get() + 1)
        quiz_state["problem"] = generate_problem(quiz_topic, quiz_difficulty)
        header_label.config(text=(f"{quiz_topic} - {quiz_difficulty}   |   "
                                   f"Question {question_number_var.get()} of {QUESTIONS_PER_ROUND}   |   "
                                   f"Score: {correct_count_var.get()}"))
        progress_canvas.coords(progress_bar, 0, 0, 420 * (question_number_var.get() - 1) / QUESTIONS_PER_ROUND, 14)
        question_label.config(text=quiz_state["problem"]["question"])
        answer_var.set("")
        answer_entry.focus_set()

    def submit_answer():
        # Marks the current answer. A separate message box style is used for input that
        # could not be understood at all, distinct from a right or wrong answer.
        status, message = check_answer(quiz_state["problem"], answer_var.get())
        if status == "invalid":
            messagebox.showerror("Invalid Answer", message)
            return
        if status == "correct":
            correct_count_var.set(correct_count_var.get() + 1)
            messagebox.showinfo("Correct!", message)
        else:
            messagebox.showwarning("Not Quite", message)
        load_next_question()

    answer_entry.bind("<Return>", lambda event: submit_answer())

    submit_btn = Button(card, text="Submit", font=FONT_BUTTON, bg=COLOR_PRIMARY, fg="white",
                        borderwidth=3, relief=RAISED, cursor="hand2", command=submit_answer)
    submit_btn.pack(pady=(20, 0))
    add_hover_effect(submit_btn, COLOR_PRIMARY, COLOR_PRIMARY_DARK)

    def finish_round():
        # Saves the completed round to file, then moves to the results window. This does not
        # go through go_to, since the results screen is reached automatically rather than by
        # the student choosing to navigate deeper - Back from Results should still return to
        # the topic screen, which is already sitting on top of navigation_history.
        global last_round_score, last_round_unlocked
        last_round_score = correct_count_var.get()
        last_round_unlocked = current_progress.record_round(quiz_topic, quiz_difficulty, correct_count_var.get(), QUESTIONS_PER_ROUND)
        save_student_progress(current_progress)
        switch_window(quiz_win, results_window)

    load_next_question()


# -------------------------------- Creating Results Window --------------------------------


def results_window():
    results_win = tk.Toplevel()
    center_window(results_win, WINDOW_WIDTH, WINDOW_HEIGHT)
    results_win.overrideredirect(True)
    results_win.configure(bg=COLOR_BACKGROUND, borderwidth=15, relief=RAISED)

    add_exit_button(results_win)
    add_back_button(results_win, lambda: go_back(results_win))

    percentage = round((last_round_score / QUESTIONS_PER_ROUND) * 100)
    if percentage >= 90:
        heading = "Outstanding!"
    elif percentage >= 70:
        heading = "Great work!"
    else:
        heading = "Keep practising!"

    card = Frame(results_win, bg=COLOR_PANEL, borderwidth=5, relief=RAISED, padx=50, pady=40)
    card.pack(pady=110)

    Label(card, text=heading, font=FONT_TITLE, bg=COLOR_PANEL, fg=COLOR_PRIMARY).pack(pady=(0, 10))
    Label(card, text=f"You scored {last_round_score} out of {QUESTIONS_PER_ROUND} ({percentage}%)",
          font=FONT_HEADING, bg=COLOR_PANEL, fg=COLOR_TEXT).pack(pady=(0, 10))
    if last_round_unlocked:
        Label(card, text=f"You unlocked {last_round_unlocked} difficulty!", font=FONT_BODY,
              bg=COLOR_PANEL, fg=COLOR_SUCCESS).pack(pady=(0, 20))
    else:
        Label(card, text="", bg=COLOR_PANEL).pack(pady=(0, 20))

    try_again_btn = Button(card, text="Try Again", font=FONT_BUTTON, bg=COLOR_PRIMARY, fg="white",
                          borderwidth=3, relief=RAISED, cursor="hand2",
                          command=lambda: switch_window(results_win, quiz_window))
    try_again_btn.pack()
    add_hover_effect(try_again_btn, COLOR_PRIMARY, COLOR_PRIMARY_DARK)


# -------------------------------- Creating Stats Window --------------------------------


def stats_window():
    stats_win = tk.Toplevel()
    center_window(stats_win, WINDOW_WIDTH, WINDOW_HEIGHT)
    stats_win.overrideredirect(True)
    stats_win.configure(bg=COLOR_BACKGROUND, borderwidth=15, relief=RAISED)

    add_exit_button(stats_win)
    add_back_button(stats_win, lambda: go_back(stats_win))

    Label(stats_win, text="My Progress", font=FONT_TITLE, bg=COLOR_BACKGROUND, fg=COLOR_PRIMARY).pack(pady=(30, 15))

    table_frame = Frame(stats_win, bg=COLOR_BACKGROUND)
    table_frame.pack(padx=40)

    headers = ["Topic"] + DIFFICULTIES
    for column, text in enumerate(headers):
        Label(table_frame, text=text, font=FONT_HEADING, bg=COLOR_BACKGROUND, fg=COLOR_TEXT).grid(
            row=0, column=column, padx=14, pady=8, sticky="w")

    for row_index, topic in enumerate(TOPICS, start=1):
        Label(table_frame, text=topic, font=FONT_BODY, bg=COLOR_BACKGROUND, fg=COLOR_TEXT).grid(
            row=row_index, column=0, padx=14, pady=4, sticky="w")
        for column, difficulty in enumerate(DIFFICULTIES, start=1):
            accuracy = current_progress.accuracy(topic, difficulty)
            if not current_progress.is_unlocked(topic, difficulty):
                text, colour = "Locked", COLOR_MUTED
            elif accuracy is None:
                text, colour = "Not attempted", COLOR_MUTED
            else:
                text = f"{accuracy}%"
                colour = COLOR_SUCCESS if accuracy >= 70 else COLOR_ERROR
            Label(table_frame, text=text, font=FONT_BODY, bg=COLOR_BACKGROUND, fg=colour).grid(
                row=row_index, column=column, padx=14, pady=4, sticky="w")


# -------------------------------- Calling & Starting The Program --------------------------------


def main():
    # Starts the whole program running.
    starting_window()
    root.mainloop()


main()