import networkx as nx
from itertools import product
from dataclasses import dataclass
from functools import cached_property
from musicaljuggling.automata.utils import right_shift
from typing import NamedTuple, Optional, Type, Iterator
from collections import deque
from os.path import exists
from copy import copy

# Second version where we start generation from the end.

"""
Constraints :
- music : the music to be played. A list that states
- max_hand_capacity
- hands_as_heap : Should the hands be seen as a stack (meaning the only balls on a hand have a FIFO structure : only the latest ball can be thrown.
- allow_multiplex
- juggler_as_2_hands or juggler_as_one_hand
- miss_beat_after_synchronous_throw
- table
- forbidden_throw_sequences
- max_height
- allow_silent_catches
- allow multiball catch
- can_hold_balls
- allow_tempo_change

MISSING : constraints on how to catch the balls. For instance, for rythmic balls, higher throws will make them sound different.
Constraints specific to each juggler.
See a juggler as either 2 hands or A vanilla siteswap kind of hand.
"""

"""class Constraints():
    music: Any
    ball_types: Any
    nb_balls
    nb_hands"""


# TODO : Change type of container for hand, to account for multiset / deque ?
# And to not have to rewrite __eq__
@dataclass(frozen=True)
class State:
    hands: tuple[frozenset[str], frozenset[str]]
    airborn: tuple[str, ...]
    throw_from: int
    time: Optional[int] = None

    @classmethod
    def from_list(
        cls: Type["State"],
        hands: list[set[str]],
        airborn: list[str],
        throw_from: int,
        time: Optional[int] = None,
    ) -> "State":
        if len(hands) != 2:
            raise ValueError("hands should have 2 elements.")
        return State(
            (frozenset(hands[0]), frozenset(hands[1])), tuple(airborn), throw_from, time
        )

    def __repr__(self) -> str:
        string = ""
        string += "X" if len(self.hands[0]) == 0 else "".join(sorted(self.hands[0]))
        string += "<| " if self.throw_from == 0 else " |>"
        string += "X" if len(self.hands[1]) == 0 else "".join(sorted(self.hands[1]))
        string += " | "
        string += "".join("X" if elem == "" else elem for elem in self.airborn)
        if self.time is not None:
            string += f" | t={self.time}"
        return string

    @cached_property
    def caught_ball(self) -> str:
        return self.airborn[0]

    def enumerate_airborn_balls(self) -> Iterator[tuple[int, str]]:
        for i, ball in enumerate(self.airborn):
            if ball != "":
                yield (i, ball)

    def iter_airborn_balls(self) -> Iterator[str]:
        for ball in self.airborn:
            if ball != "":
                yield ball

    def _single_back_state(
        self, note: str, ball_height: Optional[int]
    ) -> Optional["State"]:
        old_throw_from = (self.throw_from + 1) % 2
        old_time = None if self.time is None else self.time - 1
        old_airborn = list(self.airborn)
        old_hands = [set(hand) for hand in self.hands]
        if ball_height is not None:
            old_hands[old_throw_from].add(self.airborn[ball_height])
            old_airborn[ball_height] = ""
        old_airborn = right_shift(old_airborn)
        if note != "":
            if note not in old_hands[old_throw_from]:
                return None
            old_hands[old_throw_from].remove(note)
            old_airborn[0] = note
        return State.from_list(old_hands, old_airborn, old_throw_from, old_time)

    def back_transitions(self, note: str) -> list["Transition"]:
        # Special case: ball at maximum height. We HAVE to throw it.
        if self.airborn[-1] != "":
            old_state = self._single_back_state(note, len(self.airborn) - 1)
            if old_state is None:
                return []
            else:
                return [
                    Transition(old_state, self, self.airborn[-1], len(self.airborn))
                ]

        transitions = []
        # First try throwing nothing
        old_state = self._single_back_state(note, None)
        if old_state is not None:
            transitions.append(Transition(old_state, self, None, 0))
        # Then try throwing a ball
        for i, ball in enumerate(self.airborn):
            if ball == "":
                continue
            old_state = self._single_back_state(note, i)
            if old_state is not None:
                transitions.append(Transition(old_state, self, ball, i + 1))
        return transitions

    def all_notes_back_transitions(self) -> list["Transition"]:
        notes = set([""])
        notes.union(self.hands[(self.throw_from + 1) % 2])
        notes.union(self.iter_airborn_balls())
        transitions = []
        for note in notes:
            transitions.extend(self.back_transitions(note))
        return transitions


# reecrire avec une union de type qui correspondent aux différentes formes de lancers (bruyants, pas de lancer, on attrape juste, et silencieux)
class Transition(NamedTuple):
    old_state: State
    new_state: State
    ball: Optional[str]
    height: int


class MusicalAutomaton:
    def __init__(
        self,
        music: list[str],
        max_height: int,
        balls: Optional[list[str]] = None,
        autobuild: bool = True,
    ) -> None:
        self.music = music
        self.max_height = max_height
        if balls is None:
            balls = list(set(music) - set([""]))
        self.balls = balls
        self.automaton: nx.DiGraph[State] = nx.DiGraph()
        self.initial_states: list[State] = []
        self.final_states: list[State] = []
        if autobuild:
            self.build_automaton()

    def build_automaton(self) -> None:
        # Generation is done from the end of the music to the beginning.
        self.build_final_states()
        self.build_back_transitions()
        self.elagate()

    # Attention à la logique si on appelle plusieurs fois cette fonction.
    # CHanger le type de retour pour retourner la liste plutôt que de muter ?
    def build_final_states(self) -> None:
        balls_to_consider = copy(self.balls)
        if self.music[-1] != "":
            balls_to_consider.remove(self.music[-1])
        airborn = [""] * self.max_height
        airborn[0] = self.music[-1]
        for comb in product(range(2), repeat=len(balls_to_consider)):
            hands: list[set[str]] = [set(), set()]
            for ball_idx, hand_idx in enumerate(comb):
                hands[hand_idx].add(balls_to_consider[ball_idx])
            # We arbitrarily choose to catch the first ball from the left hand.
            state = State.from_list(
                hands, airborn, (len(self.music) - 1) % 2, len(self.music) - 1
            )
            self.final_states.append(state)

    def build_back_transitions(self) -> None:
        # A final state is a state at the end of the music.
        # An initial state is a state when the first note is caught
        states_to_handle: set[State] = set(self.final_states)
        self.automaton.add_nodes_from(states_to_handle)
        for i in range(len(self.music) - 2, -1, -1):
            next_states_to_handle: set[State] = set()
            for state in states_to_handle:
                for transition in state.back_transitions(self.music[i]):
                    self.automaton.add_edge(
                        transition.old_state,
                        transition.new_state,
                        ball=transition.ball,
                        height=transition.height,
                        label=f"{transition.ball if transition.ball else ""}{transition.height}",
                    )
                    next_states_to_handle.add(transition.old_state)
            states_to_handle = next_states_to_handle
        # All initial states are the ones we obtain
        self.initial_states = list(states_to_handle)

    def bfs(self, sources: list[State], reverse: bool = False) -> set[State]:
        to_process: deque[State] = deque(sources)
        nodes_met = set(sources)
        while len(to_process) != 0:
            node = to_process.popleft()
            neighbours = (
                self.automaton.predecessors(node)
                if reverse
                else self.automaton.successors(node)
            )
            for nei in neighbours:
                if nei not in nodes_met:
                    nodes_met.add(nei)
                    to_process.append(nei)
        return nodes_met

    def elagate(self) -> None:
        # Checks if every node v of the automaton is both accessible and co-accessible,
        # ie, if there exists u an initial state and w a final state such that u -> v -> w.
        # By construction of the automaton states, we know there already exists a path v -> w.
        accessible_nodes = self.bfs(self.initial_states, reverse=False)
        nodes_to_remove = set(self.automaton.nodes) - accessible_nodes
        self.automaton.remove_nodes_from(nodes_to_remove)
        # Sanity check
        # accessible_nodes = self.bfs(self.final_states, reverse=True)
        # nodes_to_remove = set(self.automaton.nodes) - accessible_nodes
        # self.automaton.remove_nodes_from(nodes_to_remove)

    def draw(self, path: Optional[str] = None, notebook: bool = False) -> None:
        if not notebook and path is None:
            raise ValueError(
                "Either notebook should be true, or you should provide a path to store the drawing"
            )
        save = path is not None
        if not save:
            path = "_tmp.svg"
            while exists(path):
                path = "_" + path
        aut_to_draw = nx.nx_agraph.to_agraph(self.automaton)  # type: ignore
        aut_to_draw.layout("dot")
        aut_to_draw.draw(path)
        if notebook:
            from IPython.display import SVG, display

            display(SVG(path))
        # if not save:
        #    remove(path)


if __name__ == "__main__":
    au_clair_de_la_lune = [
        "C",
        "C",
        "C",
        "D",
        "E",
        "",
        "D",
        "",
        "C",
        "E",
        "D",
        "D",
        "C",
    ]
    a = MusicalAutomaton(au_clair_de_la_lune, 6)
    print("fini")
