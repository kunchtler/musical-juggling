from automata.fa.dfa import DFA
from dataclasses import dataclass


@dataclass
class A:
    l: list[int]

my_dfa = DFA(
    states={A([1, 2]), "🥝", "🐶"},
    input_symbols={"😫", "😁"},
    transitions={
        A([1, 2]): {"😫": A([1, 2]), "😁": "🥝"},
        "🥝": {"😫": A([1, 2]), "😁": "🐶"},
        "🐶": {"😫": "🐶", "😁": "🐶"},
    },
    initial_state=A([1, 2]),
    final_states={"🥝"},
)