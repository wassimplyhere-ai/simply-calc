"""
Desktop calculator (tkinter). Same behavior as the web calculator.

Run:
    python calculator.py

Build a Windows .exe on a Windows PC:
    pip install pyinstaller
    pyinstaller --onefile --windowed calculator.py
The program ends up at dist\\calculator.exe.
"""
import math
import re
import tkinter as tk
from decimal import Decimal

MAX_DIGITS = 12
SYMBOL = {"+": "+", "-": "−", "*": "×", "/": "÷"}

COLORS = {
    "bg": "#e4e8e2",
    "case": "#cfd6ce",
    "lcd": "#b6c8af",
    "lcd_ink": "#12201a",
    "key": "#f6f8f4",
    "fn": "#b9c3b9",
    "op": "#d9891c",
    "ink": "#1c2421",
    "op_ink": "#1d1505",
}

# (label, action, value, style)
LAYOUT = [
    [("AC", "clear", None, "fn"), ("⌫", "back", None, "fn"),
     ("%", "percent", None, "fn"), ("÷", "op", "/", "op")],
    [("7", "digit", "7", "key"), ("8", "digit", "8", "key"),
     ("9", "digit", "9", "key"), ("×", "op", "*", "op")],
    [("4", "digit", "4", "key"), ("5", "digit", "5", "key"),
     ("6", "digit", "6", "key"), ("−", "op", "-", "op")],
    [("1", "digit", "1", "key"), ("2", "digit", "2", "key"),
     ("3", "digit", "3", "key"), ("+", "op", "+", "op")],
    [("±", "sign", None, "fn"), ("0", "digit", "0", "key"),
     (".", "decimal", None, "key"), ("=", "equals", None, "op")],
]

STYLE = {
    "key": (COLORS["key"], COLORS["ink"]),
    "fn": (COLORS["fn"], COLORS["ink"]),
    "op": (COLORS["op"], COLORS["op_ink"]),
}

# Keyboard: character -> (action, value)
KEY_MAP = {str(d): ("digit", str(d)) for d in range(10)}
KEY_MAP.update({
    ".": ("decimal", None),
    ",": ("decimal", None),
    "+": ("op", "+"),
    "-": ("op", "-"),
    "*": ("op", "*"),
    "x": ("op", "*"),
    "X": ("op", "*"),
    "/": ("op", "/"),
    "=": ("equals", None),
    "%": ("percent", None),
    "c": ("clear", None),
    "C": ("clear", None),
})
KEYSYM_MAP = {
    "Return": ("equals", None),
    "KP_Enter": ("equals", None),
    "Escape": ("clear", None),
    "BackSpace": ("back", None),
}


class CalcError(Exception):
    pass


def fmt(n):
    """Round away float noise (0.1 + 0.2 -> 0.3) and use exponent form for very large or small values."""
    r = float(f"{n:.12g}")
    if r == 0:
        return "0"
    if abs(r) >= 1e12 or abs(r) < 1e-7:
        mantissa, exp = f"{r:.11e}".split("e")
        mantissa = mantissa.rstrip("0").rstrip(".")
        e = int(exp)
        return f"{mantissa}e{'+' if e >= 0 else '-'}{abs(e)}"
    s = repr(r)
    if "e" in s:
        s = format(Decimal(s), "f")
    if s.endswith(".0"):
        s = s[:-2]
    return s


def _apply(a, op, b):
    if op == "/" and b == 0:
        raise CalcError("Can't divide by zero")
    try:
        if op == "+":
            r = a + b
        elif op == "-":
            r = a - b
        elif op == "*":
            r = a * b
        else:
            r = a / b
    except OverflowError:
        raise CalcError("Result is too large")
    if not math.isfinite(r):
        raise CalcError("Result is too large")
    return r


def count_digits(s):
    return len(s) - s.count("-") - s.count(".")


class Calc:
    """Calculator state and rules. No GUI code here."""

    def __init__(self):
        self.clear()

    def clear(self):
        self.current = "0"   # text shown on the display
        self.prev = None     # left-hand operand waiting for an operator
        self.op = None       # pending operator: + - * /
        self.fresh = False   # True when the next digit starts a new number
        self.error = None    # error message, or None

    def press(self, action, value=None):
        if self.error:
            # After an error, only AC and new numbers do anything.
            if action not in ("clear", "digit", "decimal"):
                return
            self.clear()
        try:
            if action == "digit":
                self._digit(value)
            elif action == "decimal":
                self._decimal()
            elif action == "op":
                self._set_op(value)
            elif action == "equals":
                self._equals()
            elif action == "clear":
                self.clear()
            elif action == "back":
                self._backspace()
            elif action == "sign":
                self._toggle_sign()
            elif action == "percent":
                self._percent()
        except CalcError as e:
            self.error = str(e)

    def _digit(self, d):
        if self.fresh:
            self.current = d
            self.fresh = False
        elif "e" in self.current:
            return
        elif self.current == "0":
            self.current = d
        elif count_digits(self.current) < MAX_DIGITS:
            self.current += d

    def _decimal(self):
        if self.fresh:
            self.current = "0."
            self.fresh = False
        elif "e" in self.current or "." in self.current:
            return
        else:
            self.current += "."

    def _backspace(self):
        if self.fresh:
            return
        if "e" in self.current or re.fullmatch(r"-?.", self.current):
            self.current = "0"
        else:
            self.current = self.current[:-1]

    def _toggle_sign(self):
        if self.current == "0":
            return
        if self.current.startswith("-"):
            self.current = self.current[1:]
        else:
            self.current = "-" + self.current

    def _percent(self):
        self.current = fmt(float(self.current) / 100)
        self.fresh = False

    def _set_op(self, nxt):
        value = float(self.current)
        if self.op and not self.fresh:
            self.prev = _apply(self.prev, self.op, value)
            self.current = fmt(self.prev)
        elif self.prev is None:
            self.prev = value
        self.op = nxt
        self.fresh = True

    def _equals(self):
        if not self.op:
            return
        self.current = fmt(_apply(self.prev, self.op, float(self.current)))
        self.prev = None
        self.op = None
        self.fresh = True


class App:
    def __init__(self, root):
        self.calc = Calc()

        root.title("Calculator")
        root.configure(bg=COLORS["bg"])
        root.resizable(False, False)

        case = tk.Frame(root, bg=COLORS["case"], padx=16, pady=16)
        case.pack(padx=16, pady=16)

        lcd = tk.Frame(case, bg=COLORS["lcd"])
        lcd.pack(fill="x", pady=(0, 12))
        self.expr_var = tk.StringVar()
        self.result_var = tk.StringVar(value="0")
        tk.Label(lcd, textvariable=self.expr_var, bg=COLORS["lcd"],
                 fg=COLORS["lcd_ink"], font=("Consolas", 11), anchor="e"
                 ).pack(fill="x", padx=12, pady=(8, 0))
        self.result_label = tk.Label(lcd, textvariable=self.result_var,
                                     bg=COLORS["lcd"], fg=COLORS["lcd_ink"],
                                     font=("Consolas", 30, "bold"), anchor="e")
        self.result_label.pack(fill="x", padx=12, pady=(0, 8))

        keys = tk.Frame(case, bg=COLORS["case"])
        keys.pack()
        for r, row in enumerate(LAYOUT):
            for c, (label, action, value, style) in enumerate(row):
                bg, fg = STYLE[style]
                tk.Button(
                    keys, text=label, width=4, height=2,
                    font=("Consolas", 16), bg=bg, fg=fg,
                    activebackground=bg, activeforeground=fg,
                    relief="flat", bd=0, highlightthickness=0,
                    takefocus=0, cursor="hand2",
                    command=lambda a=action, v=value: self.press(a, v),
                ).grid(row=r, column=c, padx=5, pady=5)

        root.bind("<Key>", self.on_key)
        root.focus_set()
        self.render()

    def press(self, action, value=None):
        self.calc.press(action, value)
        self.render()

    def on_key(self, event):
        mapped = KEYSYM_MAP.get(event.keysym) or KEY_MAP.get(event.char)
        if mapped:
            self.press(*mapped)

    def render(self):
        c = self.calc
        if c.error:
            self.result_var.set("Error")
            self.result_label.config(font=("Consolas", 30, "bold"))
            self.expr_var.set(f"{c.error}. Press AC to reset.")
            return
        self.result_var.set(c.current)
        n = len(c.current)
        size = 30 if n <= 8 else 22 if n <= 10 else 16
        self.result_label.config(font=("Consolas", size, "bold"))
        if c.op and c.prev is not None:
            self.expr_var.set(f"{fmt(c.prev)} {SYMBOL[c.op]}")
        else:
            self.expr_var.set("")


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
