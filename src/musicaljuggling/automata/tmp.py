"""
Global Constraints (all jugglers) -> Local Constraints (per juggler)

Juggler : make balls fall
See all states you end up with (where did the balls get caught in hand ? Maybe there's multiple possbilities, if multiple balls are caught at once, or if you can catch it in multiple places in your hand)
From there, see all balls you can throw (PROBLEM : overlap with previous paragraph)
Then, throw them according to throwing rules.
Finally, see if any unwanted thing happens ? (multicatch or not, forbidden or only allowed patterns)

Global / Local rules :
Music can be defined Globally or Locally.
If global : The note has to be played between x and y amount of times considering every juggler
If local : The juggler has to juggle *exactly* his local part (doesn't consider the global part anymore)
Incoherence if Sum of all local parts make notes not present in the global one.
  

Parameters :
- Music (must be global)
- Max height
- Balls exchange (must be global)
- Balls available (specify amount ? Depends on balls exchange to know if specifi to juggler or not)
- Multiplex ?
- Can hold balls ?
- Silent throws (TODO : difference between 2s and hold ?)
- Table or not ?

TODO Later :
- BPM
- Sync / Async
- 
"""


from dataclasses import dataclass
from functools import cached_property
from musicaljuggling.automata.utils import right_shift, left_shift
from typing import Collection, Optional, Sequence, Type, Iterator, Any, Literal
from enum import StrEnum, auto
from automata.fa.dfa import DFA
from automata.fa.nfa import NFA
from automata.fa.gnfa import GNFA

@dataclass(eq = False)
class LocalConstraints:
    max_height: Optional[int]

@dataclass(eq = False)
class GlobalConstraints:
    max_height: int

@dataclass(eq = False)
class Juggler:
    name: str
    constraints: LocalConstraints

@dataclass
class Scene:
    jugglers: dict[str, Juggler]
    global_constraints: GlobalConstraints

    def juggler_max_height(self, juggler_name: str):
        local_height = self.jugglers[juggler_name].constraints.max_height
        global_height = self.global_constraints.max_height
        return local_height if local_height is not None else global_height
    
@dataclass
class State:
    jugglers: dict[]
    




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

Constraints specific to each juggler.
See a juggler as either 2 hands or A vanilla siteswap kind of hand.
"""

# Constraints can be global (applied to the whole instance) unless set locally for a juggler.

class JugglingStyle(StrEnum):
    VANILLA = auto()
    MULTIPLEX = auto()
    SYNCHRONOUS = auto()
    ASYNCHRONOUS = auto()

class HandTopology(StrEnum):
    SET = auto()
    LIFO = auto()
    FIFO = auto()

class Synchronicity(StrEnum):
    ASYNC = auto()
    SYNC = auto()
    BOTH = auto()



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
        string += " < " if self.throw_from == 0 else " > "
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
        notes.update(self.hands[(self.throw_from + 1) % 2])
        notes.update(self.iter_airborn_balls())
        transitions = []
        for note in notes:
            transitions.extend(self.back_transitions(note))
        return transitions

    def __str__(self) -> str:
        return ""

Ball = str


class Hand:
    held_balls: Sequence[Ball]
    airborne: list[Ball]


class Juggler:
    hands: tuple[list[Ball], list[Ball]]
    airbornes: tuple[list[Ball], list[Ball]]
    throw_from: int
    constraints: Constraints

    def _half_step_fall(self) -> list["Juggler"]:
        new_hands: tuple[list[list[Ball]], list[list[Ball]]]
        for hand, airborne in zip(self.hands, self.airbornes):
            new_airborne = left_shift(airborne)
            new_hand = hand.catch(fallen_balls)
            fallen_balls = airborne[0]
            #TODO: new_hand.add can return multiple possibilities ?
            for new_hand in new_hand.
    
    
        
        pass

    def _half_step_rise(self) -> tuple["State", list[Ball]]:
        pass

    def __str__(self) -> str:

        def str_for_hand(hand_idx: int) -> str:
            string = ""
            #TODO : Handle when both.
            if self.constraints.synchronicity == Synchronicity.ASYNC:
                if 
            
            if self.constraints.can_hold:
                string += "X" if len(self.hands[0]) == 0 else "".join(self.hands[0])
                string += " < " if self.throw_from == 0 else " > "
                string += "X" if len(self.hands[1]) == 0 else "".join(self.hands[1])
                string += " | "
            for balls in self.airborne:
                if len(balls) == 0:
                    string += "X"
                elif len(balls) == 1:
                    string += "".join(balls)
                else:
                    string += "[" + "".join(balls) + "]"
                string += "X" if len(balls) == 0 else "".join(balls)
        string += "".join()
    if self.time is not None:
        string += f" | t={self.time}"
    return string

class State:
    hands: tuple[Collection[Ball]]
    airborne: tuple[tuple[Ball, ...], ...]
    constraints: Constraints
    
    #local_constraints: tuple[Constraints, ...]

    def __init__(self) -> None:
        pass

    # def get_condition_on_juggler(self, juggler_idx: int, constraint_name: str):
    #     if hasattr(self.local_constraints[juggler_idx], constraint_name):
    #         return getattr(self.local_constraints[juggler_idx], constraint_name)
    #     return getattr(self.global_constraints, constraint_name)

    def forward_transitions(self) -> list["Transition"]:
        pass

    def backward_transitions(self) -> list["Transition"]:
        pass

    def _half_step_fall(self) -> tuple["State", list[Ball]]:
        """Simulates all balls falling one step.

        Returns
        -------
        new_state: State
            the new state after balls have fallen
        caught_balls:
            a list of all caught balls in the process
        """
        for hand in self.hands:
            new_hand = []

        new_hands = [list(hand) for hand in self.hands]
        new_airborn = left_shift(list(self.airborn), 1)
        if self.airborn[0] != "":
            new_hands[self.throw_from].append(self.airborn[0])
        return State.from_list(new_hands, new_airborn, self.throw_from, self.time)

    def _half_step_rise(self) -> tuple["State", list[Ball]]:
        """Returns the shifted state of the current state, where all balls have fallen one step.
        This does not define a valid transition from the current state, has we haven't yet thrown a ball.
        """
        

    def __str__(self) -> str:
        string = ""
        for juggler in self.jugglers:
            for hand in juggler.hands:
                if self.constraints.can_hold:
                    if self.constraints.hand_data_structure == HandTopology.SET:
                


        

    def __hash__(self) -> int:
        pass

    def __eq__(self, value: object) -> bool:
        pass

    def __repr__(self) -> str:
        pass

    def 