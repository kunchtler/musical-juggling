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
from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from cached_method import cached_method
from musicaljuggling.automata.utils import right_shift, left_shift, left_shift_in_place
from typing import Collection, Optional, Sequence, Type, Iterator, Any, Literal
from enum import StrEnum, auto
from musicaljuggling.automata.automatalib2 import MyDFA, MyNFA, MyGNFA
from typing import NamedTuple
from frozendict import frozendict
from multiset import Multiset, FrozenMultiset
from copy import deepcopy
import itertools

Music = dict[int, Multiset[str]]

class DeadEndException(Exception):
    pass

# TODO : Instead of messages in deadendexception, add child classes that describe those errors better.
#TODO : Create (with inheritance class with and without music to avoid all the checks to "music is not None" and "time is not None" etc)
#TODO : What datastructure for music ?
@dataclass(eq=False, slots=True)
class LocalConstraints:
    name: str
    max_height: Optional[int]
    music: Optional[Music]
    can_play_more_music: Optional[bool]
    multiplex: Optional[bool]
    max_hand_capacity: Optional[int]
    # forbidden_patterns : 
    # authorized_patterns :
    # hands_strucutre : 


@dataclass(eq=False, slots=True)
class GlobalConstraints:
    max_height: int
    music : Optional[Music]
    can_play_more_music: bool
    multiplex: bool
    max_hand_capacity: Optional[int]

@dataclass(eq=False, slots=True)
class ComputedConstraints:
    """Class intended to contain the computed constraints for each juggler,
    based on their local constraints if defined, else on their local constraints."""

    max_height: int
    music: Optional[Music]
    can_play_more_music: Optional[bool]
    multiplex: bool
    max_hand_capacity: Optional[int]

    @classmethod
    def from_constraints(
        cls, global_constraints: GlobalConstraints, local_constraints: LocalConstraints
    ) -> ComputedConstraints:
        max_height = (
            local_constraints.max_height
            if local_constraints.max_height is not None
            else global_constraints.max_height
        )
        music = local_constraints.music
        can_play_more_music = (
            local_constraints.can_play_more_music
            if local_constraints.can_play_more_music is not None
            else global_constraints.can_play_more_music
        )
        multiplex = (
            local_constraints.multiplex
            if local_constraints.multiplex is not None
            else global_constraints.multiplex
        )
        max_hand_capacity = (
            local_constraints.max_hand_capacity
            if local_constraints.max_hand_capacity is not None
            else global_constraints.max_hand_capacity
        )
        return cls(
            max_height=max_height,
            music=music,
            can_play_more_music=can_play_more_music,
            multiplex=multiplex,
            max_hand_capacity=max_hand_capacity,
        )


# @dataclass(eq=False, slots=True)
# class Juggler:
#     name: str
#     constraints: LocalConstraints

#     def max_height(self, global_constraint):
#         return (
#             global_constraint.max_height
#             if self.constraints.max_height is None
#             else self.constraints.max_height
#         )


#TODO : Etre consistant dans le fait qu'une fois dans le calcul des états, on a tout précalculé (la hauteur de chaque jongleur, etc) pour éviter d'avoir des "méthodes dupliquées" avec lesquelles on risque de se tromper. Ex : juggler_max_height
@dataclass(slots=True)
class World:
    jugglers_constraints: dict[str, ComputedConstraints]
    global_constraints: GlobalConstraints
    _unlocal_music : Optional[Music]

    def iter_transitions_backwards(self, state : WorldState):
        pass

    def iter_transitions_forwards(self, state : WorldState):
        pass

    def half_step_fall(self, state: WorldState):
        pass

    def half_step_rise(self, state: WorldState):
        pass

    def compute_unlocal_music(self) -> Music:
        if self.global_constraints.music is None:
            return {}

        unlocal_music : Music = {}
        jugglers_music : dict[str, Music] = {}
        for name, constraints in self.jugglers_constraints.items():
            if constraints.music is not None:
                jugglers_music[name] = deepcopy(constraints.music)
        for time, notes in self.global_constraints.music.items():
            unlocal_music[time] = Multiset()
            for note in notes:
                for name, music in jugglers_music.items():
                    if note in music[time]:
                        music[time].discard(note, 1)
                        break
                else:
                    unlocal_music[time].add(note)
        return unlocal_music

    def compute_unplanned_notes(self, state: WorldState, time: int) -> tuple[Music, dict[str, Music]]:
        if self._unlocal_music is None:
            return {}, {}

        # Planning of which notes are useful.
        max_juggler_height = max(
            constraints.max_height for constraints in self.jugglers_constraints.values()
        )
        unlocal_unplanned : Music = {}
        for note_time, notes in self._unlocal_music.items():
            if time <= note_time <= time + max_juggler_height:
                unlocal_unplanned[note_time] = deepcopy(notes) 
        jugglers_unplanned : dict[str, Music] = {}
        for name, constraints in self.jugglers_constraints.items():
            if constraints.music is None:
                continue
            jugglers_unplanned[name] = {}
            for note_time, notes in constraints.music.items():
                if (
                    time
                    <= note_time
                    <= time + self.jugglers_constraints[name].max_height
                ):
                    jugglers_unplanned[name][note_time] = notes

        #Figuring out what notes are already played, and removing them
        #first from the jugglers plan, then from the global plan.
        for name, juggler in state.jugglers.items():
            for height in range(1, self.jugglers_constraints[name].max_height + 1):
                for ball in juggler.balls_at_height(height):
                    if ball in jugglers_unplanned[name][time + height]:
                        jugglers_unplanned[name][time + height].discard(ball, 1)
                    else:
                        unlocal_unplanned[time + height].discard(ball, 1)

        return unlocal_unplanned, jugglers_unplanned

    # TODO : Musique sous forme de liste pour l'instant ?
    # TODO : Change compute_unplanned_notes behaviour so that it works with only one time ?
    # TODO : prev function, change time key by height key.
    def iter_ball_planning(self, state: WorldState, start_time: int):
        # Check for : multiplex allowed + max_hand_capacity
        # Ne pas encore vérifier si on peut lancer les balles / si

        unlocal_unplanned, jugglers_unplanned = self.compute_unplanned_notes(
            state, start_time
        )
        # Algo
        # 1.
        plan: dict[str, Music] = {name: {} for name in state.jugglers}
        for name, music_plan in jugglers_unplanned.items():
            for time, notes_plan in music_plan.items():
                # Pb d'indice ?
                balls_present = state.jugglers[name].balls_at_height(time - start_time)
                constraints = self.jugglers_constraints[name]
                if len(notes_plan) == 0:
                    continue
                # OPT : We must throw these.
                if time == start_time + 1:
                    if (
                        constraints.max_hand_capacity is not None
                        and len(balls_present) + len(notes_plan)
                        > constraints.max_hand_capacity
                    ):
                        raise DeadEndException("Too much balls have to be thrown to produce music.")
                    if not constraints.multiplex and len(notes_plan) > 1:
                        raise DeadEndException("Too much balls have to be thrown to produce music.")
                    plan[name][time-start_time] = notes_plan
                else:
                    for k in 


                    

        # programmed = [(Juggler1, do, dans 3 temps), (Anybody, re, dans 2 temps)]

    def validate_music(self, state: WorldState):
        if self.global_constraints.music is None:
            return True
        for juggler in state.jugglers.items():
            pass
        raise DeadEndException("Wrongful state caught last second !")

    def validate_global_local_music(self):
        pass



AirborneStateT = tuple[tuple[str, ...], ...]
HeldStateT = tuple[str, ...]
MutAirborneStateT = list[list[str]]
MutHeldStateT = list[str]

HandStateT = tuple[HeldStateT, AirborneStateT]


class HandState(NamedTuple):
    held: HeldStateT
    airborne: AirborneStateT


class MutHandState(NamedTuple):
    held: MutHeldStateT
    airborne: MutAirborneStateT


@dataclass(slots=True)
class MutJugglerState:
    hands: tuple[MutHandState, MutHandState]
    name: str

    def freeze(self) -> JugglerState:
        new_hands = []
        for held, airborne in self.hands:
            new_held = tuple(held)
            new_airborne = tuple(tuple(height) for height in airborne)
            new_hands.append(HandState(new_held, new_airborne))
        return JugglerState((new_hands[0], new_hands[1]), self.name)


@dataclass(frozen=True, slots=True)
class JugglerState:
    hands: tuple[HandState, HandState]
    name: str
    local_music: Optional[Music]
    max_height: int

    def iter_throwable(
        self, ball_heights: Optional[list[tuple[str, int]]] = None
    ) -> Iterator[Iterator[(int, int)]]:
        """Returns [(hand_id, hand_slot), ...]
        If ball_heights is set, it will exactly look into how to produce the desired output."""

    def unfreeze(self) -> MutJugglerState:
        new_hands = []
        for held, airborne in self.hands:
            new_held = list(held)
            new_airborne = list(list(height) for height in airborne)
            new_hands.append(MutHandState(new_held, new_airborne))
        return MutJugglerState((new_hands[0], new_hands[1]), self.name)

    # @cached_property
    def half_step_fall(self) -> tuple[JugglerState, list[str]]:
        new_state = self.unfreeze()
        fallen = []
        for new_held, new_airborne in new_state.hands:
            fallen.extend(new_airborne[0])
            new_held.extend(new_airborne[0])
            left_shift_in_place(new_airborne)
        return (new_state.freeze(), fallen)
    
    def balls_at_height(self, height: int) -> Multiset[str]:
        """
        Parameters 
        ----------
        height: int
            The height to look at. A height of 0 means balls currently held.

        Returns
        -------
        Multiset[str]
            A multiset of all the notes at that height.
        """
        if height == 0:
            return Multiset(self.hands[0].held + self.hands[1].held)
        notes = Multiset[str]()
        for hand in self.hands:
            if height <= len(hand.airborne):
                notes.update(hand.airborne[height - 1])
        return notes


# TODO : CHanger init pour accepter des conteneurs plus larges (et ensuite dans l'intérieur de la classe les rendre non mutables). Plus esthétique ?

@dataclass(slots=True)
class WorldState:
    jugglers: frozendict[str, JugglerState]
    time: Optional[int]
    unlocal_music: Optional[Music]

    def half_step_fall(self):
        new_jugglers = {}
        for name, juggler in self.jugglers.items():
            new_juggler, balls_caught = juggler.half_step_fall()
            new_jugglers[name] = new_juggler
        return WorldState(frozendict(new_juggler))

    
            

                

    def iter_forward_transitions(self):
        half_step_state = self.state.half_step_fall()
        # A priori, meme si les balles sont ratrappées dans un ordre différent
        # (et donc, qu'il y a plusieurs états half_step), 
        # - les balles qu'on peut lancer sont les memes ? HEU...
        # - les endroits où on peut envoyer sont les memes ? OUI
        # Half step states devrait donc renvoyer uniquement les mains, et un seul exemplaire des balles dans les airs.
        # Pour l'instant, on ignore le fait qu'il peut y avoir plusieurs half steps.
        """destination_spots = self.destination_spots()
        can_throw = self.can_
        juggler_can_throw_iterators = [juggler.can_throw() for juggler in self.jugglers]
        for product in itertools.product(*(juggler_can_throw_iterators)):
            for 
        for name, juggler in self.jugglers.items():
            
            for balls_combo in juggler.can_throw():
                



                for destination_juggler in destination_spots:"""
        
        #Remove satisfied
        max_max_height = max(juggler.get_max_height() for juggler in self.jugglers)
        music_length = len(self.global_constraints.music)
        for t in range(self.time, min(self.time + max_max_height, music_length)):
            for note in self.global_constraints.music[t]:
                pass
                # Si la note est déjà programmée pour un jongleur en particulier OU si la note est

        # 1. Faire attribution de qui va jouer quelle note (en fonction de qui doit jouer quelle note), y compris "on la jouera plus tard".
        # 2. Voir toutes les configurations de balles lancées pour y arriver.

        # programmed = [(Juggler1, do, dans 3 temps), (Anybody, re, dans 2 temps)]


class Throw(NamedTuple):
    from_juggler: str
    from_hand: int
    to_juggler: str
    to_hand: int
    ball: str
    height: int


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
# @dataclass(frozen=True)
# class State:
#     hands: tuple[frozenset[str], frozenset[str]]
#     airborn: tuple[str, ...]
#     throw_from: int
#     time: Optional[int] = None

#     @classmethod
#     def from_list(
#         cls: Type["State"],
#         hands: list[set[str]],
#         airborn: list[str],
#         throw_from: int,
#         time: Optional[int] = None,
#     ) -> "State":
#         if len(hands) != 2:
#             raise ValueError("hands should have 2 elements.")
#         return State(
#             (frozenset(hands[0]), frozenset(hands[1])), tuple(airborn), throw_from, time
#         )

#     def __repr__(self) -> str:
#         string = ""
#         string += "X" if len(self.hands[0]) == 0 else "".join(sorted(self.hands[0]))
#         string += " < " if self.throw_from == 0 else " > "
#         string += "X" if len(self.hands[1]) == 0 else "".join(sorted(self.hands[1]))
#         string += " | "
#         string += "".join("X" if elem == "" else elem for elem in self.airborn)
#         if self.time is not None:
#             string += f" | t={self.time}"
#         return string

#     @cached_property
#     def caught_ball(self) -> str:
#         return self.airborn[0]

#     def enumerate_airborn_balls(self) -> Iterator[tuple[int, str]]:
#         for i, ball in enumerate(self.airborn):
#             if ball != "":
#                 yield (i, ball)

#     def iter_airborn_balls(self) -> Iterator[str]:
#         for ball in self.airborn:
#             if ball != "":
#                 yield ball

#     def _single_back_state(
#         self, note: str, ball_height: Optional[int]
#     ) -> Optional["State"]:
#         old_throw_from = (self.throw_from + 1) % 2
#         old_time = None if self.time is None else self.time - 1
#         old_airborn = list(self.airborn)
#         old_hands = [set(hand) for hand in self.hands]
#         if ball_height is not None:
#             old_hands[old_throw_from].add(self.airborn[ball_height])
#             old_airborn[ball_height] = ""
#         old_airborn = right_shift(old_airborn)
#         if note != "":
#             if note not in old_hands[old_throw_from]:
#                 return None
#             old_hands[old_throw_from].remove(note)
#             old_airborn[0] = note
#         return State.from_list(old_hands, old_airborn, old_throw_from, old_time)

#     def back_transitions(self, note: str) -> list["Transition"]:
#         # Special case: ball at maximum height. We HAVE to throw it.
#         if self.airborn[-1] != "":
#             old_state = self._single_back_state(note, len(self.airborn) - 1)
#             if old_state is None:
#                 return []
#             else:
#                 return [
#                     Transition(old_state, self, self.airborn[-1], len(self.airborn))
#                 ]

#         transitions = []
#         # First try throwing nothing
#         old_state = self._single_back_state(note, None)
#         if old_state is not None:
#             transitions.append(Transition(old_state, self, None, 0))
#         # Then try throwing a ball
#         for i, ball in enumerate(self.airborn):
#             if ball == "":
#                 continue
#             old_state = self._single_back_state(note, i)
#             if old_state is not None:
#                 transitions.append(Transition(old_state, self, ball, i + 1))
#         return transitions

#     def all_notes_back_transitions(self) -> list["Transition"]:
#         notes = set([""])
#         notes.update(self.hands[(self.throw_from + 1) % 2])
#         notes.update(self.iter_airborn_balls())
#         transitions = []
#         for note in notes:
#             transitions.extend(self.back_transitions(note))
#         return transitions

#     def __str__(self) -> str:
#         return ""


# Ball = str


# class Hand:
#     held_balls: Sequence[Ball]
#     airborne: list[Ball]


# class Juggler:
#     hands: tuple[list[Ball], list[Ball]]
#     airbornes: tuple[list[Ball], list[Ball]]
#     throw_from: int
#     constraints: Constraints

#     def _half_step_fall(self) -> list["Juggler"]:
#         new_hands: tuple[list[list[Ball]], list[list[Ball]]]
#         for hand, airborne in zip(self.hands, self.airbornes):
#             new_airborne = left_shift(airborne)
#             new_hand = hand.catch(fallen_balls)
#             fallen_balls = airborne[0]
#             #TODO: new_hand.add can return multiple possibilities ?
#             for new_hand in new_hand.


#         pass

#     def _half_step_rise(self) -> tuple["State", list[Ball]]:
#         pass

#     def __str__(self) -> str:

#         def str_for_hand(hand_idx: int) -> str:
#             string = ""
#             #TODO : Handle when both.
#             if self.constraints.synchronicity == Synchronicity.ASYNC:
#                 if

#             if self.constraints.can_hold:
#                 string += "X" if len(self.hands[0]) == 0 else "".join(self.hands[0])
#                 string += " < " if self.throw_from == 0 else " > "
#                 string += "X" if len(self.hands[1]) == 0 else "".join(self.hands[1])
#                 string += " | "
#             for balls in self.airborne:
#                 if len(balls) == 0:
#                     string += "X"
#                 elif len(balls) == 1:
#                     string += "".join(balls)
#                 else:
#                     string += "[" + "".join(balls) + "]"
#                 string += "X" if len(balls) == 0 else "".join(balls)
#         string += "".join()
#     if self.time is not None:
#         string += f" | t={self.time}"
#     return string

# class State:
#     hands: tuple[Collection[Ball]]
#     airborne: tuple[tuple[Ball, ...], ...]
#     constraints: Constraints

#     #local_constraints: tuple[Constraints, ...]

#     def __init__(self) -> None:
#         pass

#     # def get_condition_on_juggler(self, juggler_idx: int, constraint_name: str):
#     #     if hasattr(self.local_constraints[juggler_idx], constraint_name):
#     #         return getattr(self.local_constraints[juggler_idx], constraint_name)
#     #     return getattr(self.global_constraints, constraint_name)

#     def forward_transitions(self) -> list["Transition"]:
#         pass

#     def backward_transitions(self) -> list["Transition"]:
#         pass

#     def _half_step_fall(self) -> tuple["State", list[Ball]]:
#         """Simulates all balls falling one step.

#         Returns
#         -------
#         new_state: State
#             the new state after balls have fallen
#         caught_balls:
#             a list of all caught balls in the process
#         """
#         for hand in self.hands:
#             new_hand = []

#         new_hands = [list(hand) for hand in self.hands]
#         new_airborn = left_shift(list(self.airborn), 1)
#         if self.airborn[0] != "":
#             new_hands[self.throw_from].append(self.airborn[0])
#         return State.from_list(new_hands, new_airborn, self.throw_from, self.time)

#     def _half_step_rise(self) -> tuple["State", list[Ball]]:
#         """Returns the shifted state of the current state, where all balls have fallen one step.
#         This does not define a valid transition from the current state, has we haven't yet thrown a ball.
#         """


#     def __str__(self) -> str:
#         string = ""
#         for juggler in self.jugglers:
#             for hand in juggler.hands:
#                 if self.constraints.can_hold:
#                     if self.constraints.hand_data_structure == HandTopology.SET:


#     def __hash__(self) -> int:
#         pass

#     def __eq__(self, value: object) -> bool:
#         pass

#     def __repr__(self) -> str:
#         pass

#     def
