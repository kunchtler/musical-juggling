from __future__ import annotations

from collections import defaultdict
import os
from typing import (
    AbstractSet,
    Any,
    Callable,
    Generator,
    Iterator,
    NoReturn,
    Optional,
    Self,
    Set,
    Tuple,
    Type,
    Union,
)
import abc

from automata.fa.dfa import DFA, DFATransitionsT, DFAStateT, DFASymbolT
from automata.fa.nfa import NFA, NFAStateT, NFATransitionsT, InputPathListT
from automata.fa.gnfa import GNFA, GNFATransitionsT, GNFAStateT
from automata.fa.fa import FA, FAStateT
from automata.base.automaton import (
    Automaton,
    AutomatonStateT,
    AutomatonTransitionsT,
)
from automata.base.utils import (
    LayoutMethod,
    create_graph,
    create_unique_random_id,
    save_graph,
)

# Optional imports for use with visual functionality
try:
    import coloraide
    import pygraphviz as pgv  # type:ignore
except ImportError:
    _visual_imports = False
else:
    _visual_imports = True
from cached_method import cached_method  # type:ignore
from automata.regex.parser import RESERVED_CHARACTERS
import unicodedata
import automata.base.config as global_config

# TODO : Check non ambiguity of added multichar.

def regex_to_token_list(regex: str):
    current_token = ""
    split_regex = []
    for elem in regex:
        if elem in RESERVED_CHARACTERS:
            if current_token != "":
                split_regex.append(current_token)
                current_token = ""
            if elem != " ":
                split_regex.append(elem)
        else:
            current_token += elem
    return split_regex


class Singleton(type):
    _instances: dict[type, type] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class MultiCharactersEnvironment(metaclass=Singleton):
    def __init__(self, characters_pool: Optional[Set[str]] = None) -> None:
        self._initialize()

    def reset(self, characters_pool: Optional[Set[str]] = None) -> None:
        self._initialize(characters_pool)

    def _initialize(self, characters_pool: Optional[Set[str]] = None) -> None:
        if characters_pool is not None:
            self.characters_pool = characters_pool
        else:
            self.characters_pool = set()
            for beg, end in [
                (127744, 128317),
                (128507, 128591),
                (128640, 128762),
                (129293, 129535),
            ]:
                for i in range(beg, end + 1):
                    if unicodedata.category(chr(i)) == "So":
                        self.characters_pool.add(chr(i))

        self.multi_to_single_char: dict[str, str] = {"": ""}
        self.single_to_multi_char: dict[str, str] = {"": ""}

    def get(self, multi_char: str):
        return self.multi_to_single_char[multi_char]

    def get_or_set(self, multi_char: str, single_char: Optional[str] = None) -> str:
        if multi_char in self.multi_to_single_char:
            return self.multi_to_single_char[multi_char]
        if single_char in self.single_to_multi_char:
            raise RuntimeError(
                f"{single_char} has already been used for \
                multi-character {self.single_to_multi_char[single_char]}."
            )
        if single_char is not None:
            if single_char in self.characters_pool:
                self.characters_pool.remove(single_char)
        else:
            if len(self.characters_pool) == 0:
                raise RuntimeError(
                    "Not enough characters in the character pool. \
                    Please add new characters to the character pool or \
                    specify the single_char to use."
                )
            single_char = self.characters_pool.pop()
        self.multi_to_single_char[multi_char] = single_char
        self.single_to_multi_char[single_char] = multi_char
        return single_char

    def single_to_multi_word(self, single_word: str) -> list[str]:
        return [self.single_to_multi_char[single_char] for single_char in single_word]

    def multi_to_single_word(self, multi_word: list["str"]) -> str:
        output_list = [
            self.single_to_multi_char[multi_char] for multi_char in multi_word
        ]
        return "".join(output_list)

    def split_multi_str(self, multi_word: str) -> list[str]:
        multi_char = ""
        splitted_word: list[str] = []
        for single_char in multi_word:
            multi_char += single_char
            if multi_char in self.multi_to_single_char:
                splitted_word.append(multi_char)
                multi_char = ""
        if multi_char != "":
            raise RuntimeError(
                f"Can't convert word, unrecognized caracter {multi_char}"
            )
        return splitted_word

class MyFA(metaclass=abc.ABCMeta):
    multicharenv: MultiCharactersEnvironment
    _fa: FA

    @property
    @abc.abstractmethod
    def initial_state(self) -> AutomatonStateT:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def states(self) -> AbstractSet[AutomatonStateT]:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def final_states(self) -> AbstractSet[AutomatonStateT]:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def transitions(self) -> AutomatonTransitionsT:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def input_symbols(self) -> AbstractSet[str]:
        raise NotImplementedError

    @staticmethod
    def _get_state_name(state_data: Any) -> str:
        """
        Get a string representation of a state. This is used for displaying and
        uses `str` for any unsupported python data types.
        """
        return Automaton._get_state_name(state_data)

    def __post_init__(self) -> None:
        """
        Perform post-initialization validation of the automaton.
        """
        if global_config.should_validate_automata:
            self.validate()

    @abc.abstractmethod
    def validate(self) -> None:
        """
        Raises an exception if this automaton is not internally consistent.

        Raises
        ------
        NotImplementedError
            If this method has not been implemented by a subclass.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def read_input_stepwise(self, input_str: list[str]) -> Generator[Any, None, None]:
        """
        Return a generator that yields each step while reading input.

        Parameters
        ----------
        input_str : str
            The input string to read.

        Yields
        ------
        Generator[Any, None, None]
            A generator that yields the current configuration of the automaton
            after each step of reading input.

        Raises
        ------
        NotImplementedError
            If this method has not been implemented by a subclass.
        """
        raise NotImplementedError

    def read_input(self, input_str: list[str]) -> AutomatonStateT:
        """
        Check if the given string is accepted by this automaton.

        Return the automaton's final configuration if this string is valid.

        Parameters
        ----------
        input_str : str
            The input string to check.

        Returns
        -------
        AutomatonStateT
            The final configuration of the automaton after reading the input.
        """
        # "Fast-forward" generator to get its final value
        new_input_str = self.multicharenv.multi_to_single_word(input_str)
        return self._fa.read_input(new_input_str)

    def accepts_input(self, input_str: list[str]) -> bool:
        """
        Return True if this automaton accepts the given input.

        Parameters
        ----------
        input_str : str
            The input string to check.

        Returns
        -------
        bool
            True if this automaton accepts the given input; False otherwise.
        """
        new_input_str = self.multicharenv.multi_to_single_word(input_str)
        return self._fa.accepts_input(new_input_str)

    def copy(self) -> Self:
        """
        Create a deep copy of the automaton.

        Returns
        -------
        Self
            A deep copy of the automaton.
        """
        return self.__class__(self._fa.copy())  # type: ignore

    def __repr__(self) -> str:
        """
        Return a string representation of the automaton.

        Returns
        -------
        str
            A string representation of the automaton.
        """
        return self._fa.__repr__()

    def __contains__(self, item: Any) -> bool:
        """
        Returns whether the word is accepted by the automaton.

        Parameters
        ----------
        item : Any
            The item to check.

        Returns
        -------
        bool
            _description_
        """
        if not (isinstance(item, list) and all(isinstance(item, str) for item in item)):
            return False
        new_item = self.multicharenv.multi_to_single_word(item)
        return self._fa.__contains__(new_item)

    def _get_edge_name(self, symbol: str) -> str:
        return "ε" if symbol == "" else symbol

    @abc.abstractmethod
    def iter_transitions(self) -> Generator[Tuple[FAStateT, FAStateT, str], None, None]:
        """
        Iterate over all transitions in the automaton. Each transition is a tuple
        of the form (from_state, to_state, symbol)
        """

        raise NotImplementedError(
            f"iter_transitions is not implemented for {self.__class__}"
        )

    def show_diagram(
        self,
        input_str: Optional[list[str]] = None,
        path: Union[str, os.PathLike, None] = None,
        *,
        layout_method: LayoutMethod = "dot",
        horizontal: bool = True,
        reverse_orientation: bool = False,
        fig_size: Union[Tuple[float, float], Tuple[float], None] = None,
        font_size: float = 14.0,
        arrow_size: float = 0.85,
        state_separation: float = 0.5,
    ) -> pgv.AGraph:
        """
        Generates a diagram of the associated automaton.

        Parameters
        ----------
        input_str : Optional[str], default: None
            String consisting of input symbols. If set, will add processing of
            the input string to the diagram.
        path : Union[str, os.PathLike, None], default: None
            Path to output file. If None, the output will not be saved.
        horizontal : bool, default: True
            Direction of node layout in the output graph.
        reverse_orientation : bool, default: False
            Reverse direction of node layout in the output graph.
        fig_size : Union[Tuple[float, float], Tuple[float], None], default: None
            Figure size.
        font_size : float, default: 14.0
            Font size in the output graph.
        arrow_size : float, default: 0.85
            Arrow size in the output graph.
        state_separation : float, default: 0.5
            Distance between nodes in the output graph.

        Returns
        ------
        AGraph
            A diagram of the given automaton.
        """

        if not _visual_imports:
            raise ImportError(
                "Missing visualization packages; "
                "please install coloraide and pygraphviz."
            )

        # Defining the graph.
        graph = create_graph(
            horizontal, reverse_orientation, fig_size, state_separation
        )

        font_size_str = str(font_size)
        arrow_size_str = str(arrow_size)

        # create unique id to avoid colliding with other states
        null_node = create_unique_random_id()

        graph.add_node(
            null_node,
            label="",
            tooltip=".",
            shape="point",
            fontsize=font_size_str,
        )
        initial_node = self._get_state_name(self.initial_state)
        graph.add_edge(
            null_node,
            initial_node,
            tooltip="->" + initial_node,
            arrowsize=arrow_size_str,
        )

        nonfinal_states = map(self._get_state_name, self.states - self.final_states)
        final_states = map(self._get_state_name, self.final_states)
        graph.add_nodes_from(nonfinal_states, shape="circle", fontsize=font_size_str)
        graph.add_nodes_from(final_states, shape="doublecircle", fontsize=font_size_str)

        is_edge_drawn = defaultdict(lambda: False)
        if input_str is not None:
            input_path, is_accepted = self._get_input_path(input_str=input_str)

            start_color = coloraide.Color("#ff0")
            end_color = (
                coloraide.Color("#0f0") if is_accepted else coloraide.Color("#f00")
            )
            interpolation = coloraide.Color.interpolate(
                [start_color, end_color], space="srgb"
            )

            # find all transitions in the finite state machine with traversal.
            for transition_index, (from_state, to_state, symbol) in enumerate(
                input_path, start=1
            ):
                color = interpolation(transition_index / len(input_path))
                label = self._get_edge_name(symbol)

                is_edge_drawn[from_state, to_state, symbol] = True
                graph.add_edge(
                    self._get_state_name(from_state),
                    self._get_state_name(to_state),
                    label=f"<{label} <b>[<i>#{transition_index}</i>]</b>>",
                    arrowsize=arrow_size_str,
                    fontsize=font_size_str,
                    color=color.to_string(hex=True),
                    penwidth="2.5",
                )

        edge_labels = defaultdict(list)
        for from_state, to_state, symbol in self.iter_transitions():
            if is_edge_drawn[from_state, to_state, symbol]:
                continue

            from_node = self._get_state_name(from_state)
            to_node = self._get_state_name(to_state)
            label = self._get_edge_name(symbol)
            edge_labels[from_node, to_node].append(label)

        for (from_node, to_node), labels in edge_labels.items():
            graph.add_edge(
                from_node,
                to_node,
                label=",".join(sorted(labels)),
                arrowsize=arrow_size_str,
                fontsize=font_size_str,
            )

        # Set layout
        graph.layout(prog=layout_method)

        # Write diagram to file
        if path is not None:
            save_graph(graph, path)

        return graph

    @abc.abstractmethod
    def _get_input_path(
        self, input_str: list[str]
    ) -> Tuple[list[Tuple[FAStateT, FAStateT, str]], bool]:
        """Calculate the path taken by input."""

        raise NotImplementedError(
            f"_get_input_path is not implemented for {self.__class__}"
        )

    def _repr_mimebundle_(
        self, *args: Any, **kwargs: Any
    ) -> dict[str, Union[bytes, str]]:
        return self.show_diagram()._repr_mimebundle_(*args, **kwargs)


class MyDFA(MyFA):
    multicharenv = MultiCharactersEnvironment()

    def __init__(self, dfa: DFA):
        self._dfa = dfa
        self._fa = dfa

    @classmethod
    def create(
        cls,
        *,
        states: AbstractSet[DFAStateT],
        input_symbols: AbstractSet[str],
        transitions: DFATransitionsT,
        initial_state: DFAStateT,
        final_states: AbstractSet[DFAStateT],
        allow_partial: bool = False,
    ) -> MyDFA:
        new_input_symbols = {
            cls.multicharenv.get_or_set(symbol) for symbol in input_symbols
        }
        new_transitions: dict[DFAStateT, dict[str, DFAStateT]] = {}
        for state1, tmp_transition in transitions.items():
            new_transitions[state1] = {}
            for symbol, state2 in tmp_transition.items():
                new_transitions[state1][cls.multicharenv.get(symbol)] = state2

        dfa = DFA(
            states=states,
            input_symbols=new_input_symbols,
            transitions=new_transitions,
            initial_state=initial_state,
            final_states=final_states,
            allow_partial=allow_partial,
        )
        return cls(dfa)

    @property
    def states(self) -> AbstractSet[DFAStateT]:
        """Set of the DFA's valid states."""
        return self._dfa.states

    @property
    def input_symbols(self) -> AbstractSet[str]:
        """Set of the DFA's valid input symbols, each of which is a singleton
        string"""
        return self._dfa.input_symbols

    @property
    def transitions(self) -> DFATransitionsT:
        """Dict consisting of the transitions for each state. Each key is a
        state name, and each value is another dict which maps a symbol
        (the key) to a state (the value)."""
        return self._dfa.transitions

    @property
    def initial_state(self) -> DFAStateT:
        """The initial state for this DFA."""
        return self._dfa.initial_state

    @property
    def final_states(self) -> AbstractSet[DFAStateT]:
        """A set of final states for this DFA"""
        return self._dfa.final_states

    @property
    def allow_partial(self) -> bool:
        """By default, each DFA state must have a transition to
        every input symbol; if this parameter is `True`, you can disable this
        characteristic (such that any DFA state can have fewer transitions than input
        symbols). Note that a DFA must always have every state represented in the
        transition dictionary, even if there are no transitions on input symbols
        leaving a state (dictionary is left empty in that case)."""
        return self._dfa.allow_partial

    def clear_cache(self) -> None:
        """
        Resets the word and count caches.
        Can be called if too much memory is being used.
        """
        return self._dfa.clear_cache()

    def __eq__(self, other: Any) -> bool:
        """
        Return True if two DFAs are equivalent. Uses an optimized version of
        the Hopcroft-Karp algorithm. See https://arxiv.org/abs/0907.5058
        """
        if not isinstance(other, MyDFA):
            return NotImplemented
        return self._dfa.__eq__(other._dfa)

    def __le__(self, other: MyDFA) -> bool:
        """Return True if this DFA is a subset of (or equal to) another DFA."""
        return self._dfa.__le__(other._dfa)

    def __ge__(self, other: MyDFA) -> bool:
        """Return True if this DFA is a superset of another DFA."""
        return self._dfa.__ge__(other._dfa)

    def __lt__(self, other: MyDFA) -> bool:
        """Return True if this DFA is a strict subset of another DFA."""
        return self._dfa.__ge__(other._dfa)

    def __gt__(self, other: MyDFA) -> bool:
        """Return True if this DFA is a strict superset of another DFA."""
        return self._dfa.__gt__(other._dfa)

    def __sub__(self, other: MyDFA) -> MyDFA:
        """Return a DFA that is the difference of this DFA and another DFA."""
        return MyDFA(self._dfa.__sub__(other._dfa))

    def __or__(self, other: MyDFA) -> MyDFA:
        """Return the union of this DFA and another DFA."""
        return MyDFA(self._dfa.__or__(other._dfa))

    def __and__(self, other: MyDFA) -> MyDFA:
        """Return the intersection of this DFA and another DFA."""
        return MyDFA(self._dfa.__and__(other._dfa))

    def __xor__(self, other: MyDFA) -> MyDFA:
        """Return the symmetric difference of this DFA and another DFA."""
        return MyDFA(self._dfa.__xor__(other._dfa))

    def __invert__(self) -> MyDFA:
        """Return the complement of this DFA and another DFA."""
        return MyDFA(self._dfa.__invert__())

    def __iter__(self) -> Iterator[list[str]]:
        """
        Iterates through all words in the language represented by the DFA. The
        words are ordered first by length and then by the order of the input
        symbol set.
        """
        for word in self._dfa.__iter__():
            yield self.multicharenv.single_to_multi_word(word)

    def __len__(self) -> int:
        """Returns the cardinality of the language represented by the DFA."""
        return self._dfa.__len__()

    def to_partial(self, *, retain_names: bool = False, minify: bool = True) -> MyDFA:
        """
        Turns a DFA (complete or not) into a partial DFA.
        Removes dead states and trap states (except the initial state)
            and all edges leading to them.

        Parameters
        ----------
        minify : bool, default: True
            Whether to perform a minify operation while converting to
            a partial DFA.
        retain_names : bool, default: True
            Whether to retain state names during minification.

        Returns
        -------
        MyDFA
            An equivalent partial DFA.
        """
        return MyDFA(self._dfa.to_partial(retain_names=retain_names, minify=minify))

    def to_complete(self, trap_state: Optional[DFAStateT] = None) -> MyDFA:
        """
        Creates an equivalent complete DFA with trap_state used as the name
        for an added trap state. If trap_state is not passed in, defaults to
        the largest negative integer which is not already a state name.
        If the DFA is already complete, just returns a copy.

        Parameters
        ----------
        trap_state : Optional[DFAStateT], default: None
            Name for custom trap state to be used.

        Returns
        -------
        MyDFA
            An equivalent complete DFA.

        """
        return MyDFA(self._dfa.to_complete(trap_state=trap_state))

    def validate(self) -> None:
        """
        Raises an exception if this automaton is not internally consistent.

        Raises
        ------
        InvalidStateError
            If this DFA has invalid states in the transition dictionary.
        MissingStateError
            If this DFA has states missing from the transition dictionary.
        InvalidSymbolError
            If this DFA has invalid symbols in the transition dictionary.
        MissingSymbolError
            If this DFA is missing transitions on certain symbols.
        """

        self._dfa.validate()

    def read_input_stepwise(
        self, input_str: list[str], ignore_rejection: bool = False
    ) -> Generator[DFAStateT, None, None]:
        """
        Return a generator that yields each step while reading input.

        Parameters
        ----------
        input_str : list[str]
            The input string to read.
        ignore_rejection : bool, default: False
            Whether to throw an exception if the input string is rejected.

        Yields
        ------
        Generator[DFAStateT, None, None]
            A generator that yields the current configuration of the DFA
            after each step of reading input.

        Raises
        ------
        RejectionException
            Raised if this DFA does not accept the input string.
        """
        word = self.multicharenv.multi_to_single_word(input_str)
        yield from self._dfa.read_input_stepwise(word, ignore_rejection=False)

    def minify(self, retain_names: bool = False) -> MyDFA:
        """
        Create a minimal DFA which accepts the same inputs as this DFA.

        First, non-reachable states are removed.
        Then, indistinguishable states are merged using Hopcroft's Algorithm.

        Parameters
        ----------
        retain_names : bool, default: False
            Whether to retain original names when merging states.
            New names are from 0 to n-1.

        Returns
        ------
        MyDFA
            A state-minimal equivalent DFA. May be complete in some cases
            if the input is partial.
        """
        return MyDFA(self._dfa.minify(retain_names=retain_names))

    def union(
        self, other: MyDFA, *, retain_names: bool = False, minify: bool = True
    ) -> MyDFA:
        """
        Takes as input two DFAs M1 and M2 which
        accept languages L1 and L2 respectively.
        Returns a DFA which accepts the union of L1 and L2.

        Minifies by default. Unreachable states are always removed.
        If either input DFA is partial, the result is partial.

        Parameters
        ----------
        other : DFA
            The DFA we want to take a union with.
        retain_names : bool, default: False
            Whether to retain state names through the union and optional minify.
        minify : bool, default: True
            Whether to minify the result of the union of the two DFAs.

        Returns
        ------
        MyDFA
            A DFA accepting the union of the two input DFAs. State minimal by
            default.
        """
        return MyDFA(
            self._dfa.union(other._dfa, retain_names=retain_names, minify=minify)
        )

    def intersection(
        self, other: MyDFA, *, retain_names: bool = False, minify: bool = True
    ) -> MyDFA:
        """
        Takes as input two DFAs M1 and M2 which
        accept languages L1 and L2 respectively.
        Returns a DFA which accepts the intersection of L1 and L2.

        Minifies by default. Unreachable states are always removed.
        If either input DFA is partial, the result is partial.

        Parameters
        ----------
        other : DFA
            The DFA we want to take a intersection with.
        retain_names : bool, default: False
            Whether to retain state names through the intersection and optional minify.
        minify : bool, default: True
            Whether to minify the result of the intersection of the two DFAs.

        Returns
        ------
        MyDFA
            A DFA accepting the intersection of the two input DFAs. State minimal by
            default.
        """
        return MyDFA(
            self._dfa.intersection(other._dfa, retain_names=retain_names, minify=minify)
        )

    def difference(
        self, other: MyDFA, *, retain_names: bool = False, minify: bool = True
    ) -> MyDFA:
        """
        Takes as input two DFAs M1 and M2 which
        accept languages L1 and L2 respectively.
        Returns a DFA which accepts the difference of L1 and L2.

        Minifies by default. Unreachable states are always removed.
        If either input DFA is partial, the result is partial.

        Parameters
        ----------
        other : DFA
            The DFA we want to take a difference with.
        retain_names : bool, default: False
            Whether to retain state names through the difference and optional minify.
        minify : bool, default: True
            Whether to minify the result of the difference of the two DFAs.

        Returns
        ------
        MyDFA
            A DFA accepting the difference of the two input DFAs. State minimal by
            default.
        """
        return MyDFA(
            self._dfa.difference(other._dfa, retain_names=retain_names, minify=minify)
        )

    def symmetric_difference(
        self, other: MyDFA, *, retain_names: bool = False, minify: bool = True
    ) -> MyDFA:
        """
        Takes as input two DFAs M1 and M2 which
        accept languages L1 and L2 respectively.
        Returns a DFA which accepts the symmetric difference of L1 and L2.

        Minifies by default. Unreachable states are always removed.
        If either input DFA is partial, the result is partial.

        Parameters
        ----------
        other : DFA
            The DFA we want to take a symmetric difference with.
        retain_names : bool, default: False
            Whether to retain state names through the symmetric difference and optional
            minify.
        minify : bool, default: True
            Whether to minify the result of the symmetric difference of the two DFAs.

        Returns
        ------
        MyDFA
            A DFA accepting the symmetric difference of the two input DFAs. State
            minimal by default.
        """
        return MyDFA(
            self._dfa.symmetric_difference(
                other._dfa, retain_names=retain_names, minify=minify
            )
        )

    def complement(self, *, retain_names: bool = False, minify: bool = True) -> MyDFA:
        """
        Creates a DFA which accepts an input if and only if the old one does not.
        Minifies by default. Unreachable states are always removed. Partial DFAs
        are converted into complete ones.

        Parameters
        ----------
        retain_names : bool, default: False
            Whether to retain state names through the complement and optional
            minify.
        minify : bool, default: True
            Whether to minify the result of the complement of the input DFA.

        Returns
        ------
        MyDFA
            A DFA accepting the complement of the input DFA. State
            minimal by default.
        """
        return MyDFA(self._dfa.complement(retain_names=retain_names, minify=minify))

    def issubset(self, other: MyDFA) -> bool:
        """
        Returns True if the language accepted by self is a subset of that of other.

        Parameters
        ----------
        other : MyDFA
            The other DFA we are comparing our language against.

        Returns
        ------
        bool
            True if self is a subset of other, False otherwise.
        """
        return self._dfa.issubset(other._dfa)

    def issuperset(self, other: MyDFA) -> bool:
        """
        Returns True if the language accepted by self is a superset of that of other.

        Parameters
        ----------
        other : MyDFA
            The other DFA we are comparing our language against.

        Returns
        ------
        bool
            True if self is a superset of other, False otherwise.
        """
        return self._dfa.issuperset(other._dfa)

    def isdisjoint(self, other: MyDFA) -> bool:
        """
        Returns True if the language accepted by self is disjoint from that of other.

        Parameters
        ----------
        other : MyDFA
            The other DFA we are comparing our language against.

        Returns
        ------
        bool
            True if self is disjoint from other, False otherwise.
        """
        return self._dfa.isdisjoint(other._dfa)

    @cached_method
    def isempty(self) -> bool:
        """
        Returns True if the language accepted by self is empty.

        Returns
        ------
        bool
            True if self accepts the empty language, False otherwise.
        """
        return self._dfa.isempty()

    @cached_method
    def isfinite(self) -> bool:
        """
        Returns True if the language accepted by self is finite.

        Returns
        ------
        bool
            True if self accepts a finite language, False otherwise.
        """
        return self._dfa.isfinite()

    def random_word(self, k: int, *, seed: Optional[int] = None) -> list[str]:
        """
        Returns a random word of length k accepted by self.

        Parameters
        ----------
        k : int
            The length of the desired word.
        seed : Optional[int], default: None
            The random seed to use for the sampling of the random word.

        Returns
        ------
        str
            A uniformly random word of length k accepted by the DFA self.

        Raises
        ------
        ValueError
            If this DFA does not accept any words of length k.
        """
        return self.multicharenv.single_to_multi_word(
            self._dfa.random_word(k, seed=seed)
        )

    def predecessor(
        self,
        input_str: list[str],
        *,
        strict: bool = True,
        key: Optional[Callable[[Any], Any]] = None,
    ) -> Optional[list[str]]:
        """
        Returns the first string accepted by the DFA that comes before
        the input string in lexicographical order.

        Parameters
        ----------
        input_str : str
            The starting input string.
        strict : bool, default: True
            If set to false and input_str is accepted by the DFA, input_str will be
            returned.
        key : Optional[Callable], default: None
            Function for defining custom lexicographical ordering. Defaults to using
            the standard string ordering.

        Returns
        ------
        str
            The first string accepted by the DFA lexicographically before input_string.

        Raises
        ------
        InfiniteLanguageException
            Raised if the language accepted by self is infinite, as we cannot
            generate predecessors in this case.
        """
        word = self.multicharenv.multi_to_single_word(input_str)
        pred = self._dfa.predecessor(word, strict=strict, key=key)
        if pred is None:
            return None
        return self.multicharenv.single_to_multi_word(pred)

    def predecessors(
        self,
        input_str: list[str],
        *,
        strict: bool = True,
        key: Optional[Callable[[Any], Any]] = None,
    ) -> Generator[list[str], None, None]:
        """
        Generates all strings that come before the input string
        in lexicographical order.

        Parameters
        ----------
        input_str : str
            The starting input string.
        strict : bool, default: True
            If set to false and input_str is accepted by the DFA, input_str will be
            returned.
        key : Optional[Callable], default: None
            Function for defining custom lexicographical ordering. Defaults to using
            the standard string ordering.

        Returns
        ------
        Generator[str, None, None]
            A generator for all strings that come before the input string in
            lexicographical order.

        Raises
        ------
        InfiniteLanguageException
            Raised if the language accepted by self is infinite, as we cannot
            generate predecessors in this case.
        """
        word = self.multicharenv.multi_to_single_word(input_str)
        for pred in self._dfa.predecessors(word, strict=strict, key=key):
            yield self.multicharenv.single_to_multi_word(pred)

    def successor(
        self,
        input_str: Optional[list[str]],
        *,
        strict: bool = True,
        key: Optional[Callable[[Any], Any]] = None,
    ) -> Optional[list[str]]:
        """
        Returns the first string accepted by the DFA that comes after
        the input string in lexicographical order.

        Parameters
        ----------
        input_str : Optional[str]
            The starting input string. If None, will generate all words.
        strict : bool, default: True
            If set to false and input_str is accepted by the DFA, input_str will be
            returned.
        key : Optional[Callable], default: None
            Function for defining custom lexicographical ordering. Defaults to using
            the standard string ordering.

        Returns
        ------
        str
            The first string accepted by the DFA lexicographically before input_string.
        """
        word = (
            None
            if input_str is None
            else self.multicharenv.multi_to_single_word(input_str)
        )
        succ = self._dfa.successor(word, strict=strict, key=key)
        if succ is None:
            return None
        return self.multicharenv.single_to_multi_word(succ)

    def successors(
        self,
        input_str: Optional[list[str]],
        *,
        strict: bool = True,
        key: Optional[Callable[[Any], Any]] = None,
        reverse: bool = False,
    ) -> Generator[list[str], None, None]:
        """
        Generates all strings that come after the input string
        in lexicographical order.

        Parameters
        ----------
        input_str : Optional[str]
            The starting input string. If None, will generate all words.
        strict : bool, default: True
            If set to false and input_str is accepted by the DFA, input_str will be
            returned.
        key : Optional[Callable], default: None
            Function for defining custom lexicographical ordering. Defaults to using
            the standard string ordering.
        reverse : bool, default: False
            If True, then predecessors will be generated instead of successors.

        Returns
        ------
        Generator[str, None, None]
            A generator for all strings that come after the input string in
            lexicographical order.

        """
        word = (
            None
            if input_str is None
            else self.multicharenv.multi_to_single_word(input_str)
        )
        for succ in self._dfa.successors(word, strict=strict, key=key):
            yield self.multicharenv.single_to_multi_word(succ)

    def count_words_of_length(self, k: int) -> int:
        """
        Returns count of words of length k accepted by the DFA.

        Parameters
        ----------
        k : int
            The desired word length.

        Returns
        ------
        int
            The number of words of length k accepted by self.
        """
        return self._dfa.count_words_of_length(k)

    def words_of_length(self, k: int) -> Generator[list[str], None, None]:
        """
        Generates all words of length `k` in the language accepted by the DFA.

        Parameters
        ----------
        k : int
            The desired word length.

        Returns
        ------
        Generator[str, None, None]
            A generator for all words of length k accepted by the DFA.
        """
        for word in self._dfa.words_of_length(k):
            yield self.multicharenv.single_to_multi_word(word)

    @cached_method
    def cardinality(self) -> int:
        """
        Returns the cardinality of the language represented by the DFA.

        Returns
        ------
        int
            The cardinality of the language accepted by self.

        Raises
        ------
        InfiniteLanguageException
            Raised if self accepts an infinite language.
        """
        return self._dfa.cardinality()

    @cached_method
    def minimum_word_length(self) -> int:
        """
        Returns the length of the shortest word in the language accepted by the DFA.

        Returns
        ------
        int
            The length of the shortest word accepted by self.

        Raises
        ------
        EmptyLanguageException
            Raised if self accepts an empty language.
        """
        return self._dfa.minimum_word_length()

    @cached_method
    def maximum_word_length(self) -> Optional[int]:
        """
        Returns the length of the longest word in the language accepted by the DFA
        In the case of infinite languages, `None` is returned.

        Returns
        ------
        Optional[int]
            The length of the longest word accepted by self. None if the language
            is infinite.

        Raises
        ------
        EmptyLanguageException
            Raised if self accepts the empty language.
        """
        return self._dfa.maximum_word_length()

    @classmethod
    def from_prefix(
        cls: Type[MyDFA],
        input_symbols: AbstractSet[str],
        prefix: list[str],
        *,
        contains: bool = True,
        as_partial: bool = True,
    ) -> MyDFA:
        """
        Directly computes the minimal DFA accepting strings with the
        given prefix. If `contains` is set to `False` then the complement is
        constructed instead.

        Parameters
        ----------
        input_symbols : AbstractSet[str]
            The set of input symbols to construct the DFA over.
        prefix : str
            The prefix of strings that are accepted by this DFA.
        contains : bool, default: True
            Whether or not to construct the compliment DFA.
        as_partial : bool, default: True
            Whether or not to construct this DFA as a partial DFA.

        Returns
        ------
        MyDFA
            The DFA accepting the desired language.
        """
        new_input_symbols = {
            cls.multicharenv.get_or_set(symbol) for symbol in input_symbols
        }
        new_prefix = cls.multicharenv.multi_to_single_word(prefix)
        return cls(
            DFA.from_prefix(
                new_input_symbols, new_prefix, contains=contains, as_partial=as_partial
            )
        )

    @classmethod
    def from_suffix(
        cls: Type[MyDFA],
        input_symbols: AbstractSet[str],
        suffix: list[str],
        *,
        contains: bool = True,
    ) -> MyDFA:
        """
        Directly computes the minimal DFA recognizing strings with the
        given suffix. If `contains` is set to `False`, then the complement
        is constructed instead.

        Parameters
        ----------
        input_symbols : AbstractSet[str]
            The set of input symbols to construct the DFA over.
        suffix : str
            The suffix of strings that are accepted by this DFA.
        contains : bool, default: True
            Whether or not to construct the compliment DFA.

        Returns
        ------
        MyDFA
            The DFA accepting the desired language.
        """
        new_input_symbols = {
            cls.multicharenv.get_or_set(symbol) for symbol in input_symbols
        }
        new_suffix = cls.multicharenv.multi_to_single_word(suffix)
        return cls(DFA.from_suffix(new_input_symbols, new_suffix, contains=contains))

    @classmethod
    def from_substring(
        cls: Type[MyDFA],
        input_symbols: AbstractSet[str],
        substring: list[str],
        *,
        contains: bool = True,
        must_be_suffix: bool = False,
    ) -> MyDFA:
        """
        Directly computes the minimal DFA recognizing strings containing the
        given substring. If `contains` is set to `False` then the complement
        is constructed instead. If `must_be_suffix` is set to `True`, then
        the substring must be a suffix instead.

        Parameters
        ----------
        input_symbols : AbstractSet[str]
            The set of input symbols to construct the DFA over.
        substring : str
            The substring of strings that are accepted by this DFA.
        contains : bool, default: True
            Whether or to construct the compliment DFA.
        must_be_suffix : bool, default: False
            Whether or not the target substring must be a suffix.

        Returns
        ------
        MyDFA
            The DFA accepting the desired language.
        """
        new_input_symbols = {
            cls.multicharenv.get_or_set(symbol) for symbol in input_symbols
        }
        new_substring = cls.multicharenv.multi_to_single_word(substring)
        return cls(
            DFA.from_substring(
                new_input_symbols,
                new_substring,
                contains=contains,
                must_be_suffix=must_be_suffix,
            )
        )

    @classmethod
    def from_subsequence(
        cls: Type[MyDFA],
        input_symbols: AbstractSet[str],
        subsequence: list[str],
        *,
        contains: bool = True,
    ) -> MyDFA:
        """
        Directly computes the minimal DFA recognizing strings containing the
        given subsequence. If `contains` is set to `False`, then the complement
        is constructed instead.

        Parameters
        ----------
        input_symbols : AbstractSet[str]
            The set of input symbols to construct the DFA over.
        subsequence : str
            The target subsequence of strings that are accepted by this DFA.
        contains : bool, default: True
            Whether or to construct the compliment DFA.

        Returns
        ------
        MyDFA
            The DFA accepting the desired language.
        """
        new_input_symbols = {
            cls.multicharenv.get_or_set(symbol) for symbol in input_symbols
        }
        new_subsequence = cls.multicharenv.multi_to_single_word(subsequence)
        return cls(
            DFA.from_subsequence(
                new_input_symbols,
                new_subsequence,
                contains=contains,
            )
        )

    @classmethod
    def of_length(
        cls: Type[MyDFA],
        input_symbols: AbstractSet[str],
        *,
        min_length: int = 0,
        max_length: Optional[int] = None,
        symbols_to_count: Optional[AbstractSet[str]] = None,
    ) -> MyDFA:
        """
        Directly computes the minimal DFA recognizing strings whose length is
        between `min_length` and `max_length`, inclusive. To allow arbitrarily
        long words, the value `None` can be passed in for `max_length`.

        Parameters
        ----------
        input_symbols : AbstractSet[str]
            The set of input symbols to construct the DFA over.
        min_length : int, default: 0
            The minimum length of strings to be accepted by this DFA.
        max_length : Optional[int], default: None
            The maximum length of strings to be accepted by this DFA.
            If set to None, there is no maximum.
        symbols_to_count : Optional[AbstractSet[str]], default: None
            The input symbols to count towards the length of words to accepts.
            If set to None, counts all symbols.

        Returns
        ------
        MyDFA
            The DFA accepting the desired language.
        """
        new_input_symbols = {
            cls.multicharenv.get_or_set(symbol) for symbol in input_symbols
        }
        new_symbols_to_count = (
            None
            if symbols_to_count is None
            else {cls.multicharenv.get_or_set(symbol) for symbol in symbols_to_count}
        )
        return cls(
            DFA.of_length(
                new_input_symbols,
                min_length=min_length,
                max_length=max_length,
                symbols_to_count=new_symbols_to_count,
            )
        )

    @classmethod
    def count_mod(
        cls: Type[MyDFA],
        input_symbols: AbstractSet[str],
        k: int,
        *,
        remainders: Optional[AbstractSet[int]] = None,
        symbols_to_count: Optional[AbstractSet[str]] = None,
    ) -> MyDFA:
        """
        Directly computes a DFA that counts given symbols and accepts all strings where
        the remainder of division by k is in the set of remainders given.
        The default value of remainders is {0} and all symbols are counted by default.

        Parameters
        ----------
        input_symbols : AbstractSet[str]
            The set of input symbols to construct the DFA over.
        k : int
            The number to divide the length by.
        remainders : Optional[AbstractSet[int]], default: None
            The remainders to accept. If set to None, defaults to {0}.
        symbols_to_count : Optional[AbstractSet[str]], default: None
            The input symbols to count towards the length of words to accepts.
            If set to None, counts all symbols.

        Returns
        ------
        MyDFA
            The DFA accepting the desired language.
        """
        new_input_symbols = {
            cls.multicharenv.get_or_set(symbol) for symbol in input_symbols
        }
        new_symbols_to_count = (
            None
            if symbols_to_count is None
            else {cls.multicharenv.get_or_set(symbol) for symbol in symbols_to_count}
        )
        return cls(
            DFA.count_mod(
                new_input_symbols,
                k,
                remainders=remainders,
                symbols_to_count=new_symbols_to_count,
            )
        )

    @classmethod
    def universal_language(
        cls: Type[MyDFA],
        input_symbols: AbstractSet[str],
    ) -> MyDFA:
        """
        Directly computes the minimal DFA accepting all strings.

        Parameters
        ----------
        input_symbols : AbstractSet[str]
            The set of input symbols to construct the DFA over.
        Returns
        ------
        MyDFA
            The DFA accepting the desired language.
        """
        new_input_symbols = {
            cls.multicharenv.get_or_set(symbol) for symbol in input_symbols
        }
        return cls(DFA.universal_language(new_input_symbols))

    @classmethod
    def empty_language(
        cls: Type[MyDFA],
        input_symbols: AbstractSet[str],
    ) -> MyDFA:
        """
        Directly computes the minimal DFA rejecting all strings.

        Parameters
        ----------
        input_symbols : AbstractSet[str]
            The set of input symbols to construct the DFA over.

        Returns
        ------
        MyDFA
            The DFA accepting the desired language.
        """
        new_input_symbols = {
            cls.multicharenv.get_or_set(symbol) for symbol in input_symbols
        }
        return cls(DFA.empty_language(new_input_symbols))

    @classmethod
    def nth_from_start(
        cls: Type[MyDFA],
        input_symbols: AbstractSet[str],
        symbol: str,
        n: int,
    ) -> MyDFA:
        """
        Directly computes the minimal DFA which accepts all words whose `n`th
        character from the start is `symbol`, where `n` is a positive integer.

        Parameters
        ----------
        input_symbols : AbstractSet[str]
            The set of input symbols to construct the DFA over.
        symbol : str
            The target input symbol.
        n : int
            The position of the target input symbol.

        Returns
        ------
        MyDFA
            The DFA accepting the desired language.
        """
        new_input_symbols = {
            cls.multicharenv.get_or_set(symbol) for symbol in input_symbols
        }
        new_symbol = cls.multicharenv.get_or_set(symbol)
        return cls(DFA.nth_from_start(new_input_symbols, new_symbol, n))

    @classmethod
    def nth_from_end(
        cls: Type[MyDFA],
        input_symbols: AbstractSet[str],
        symbol: str,
        n: int,
    ) -> MyDFA:
        """
        Directly computes the minimal DFA which accepts all words whose `n`th
        character from the end is `symbol`, where `n` is a positive integer.

        Parameters
        ----------
        input_symbols : AbstractSet[str]
            The set of input symbols to construct the DFA over.
        symbol : str
            The target input symbol.
        n : int
            The position of the target input symbol.

        Returns
        ------
        MyDFA
            The DFA accepting the desired language.
        """
        new_input_symbols = {
            cls.multicharenv.get_or_set(symbol) for symbol in input_symbols
        }
        new_symbol = cls.multicharenv.get_or_set(symbol)
        return cls(DFA.nth_from_end(new_input_symbols, new_symbol, n))

    @classmethod
    def from_finite_language(
        cls: Type[MyDFA],
        input_symbols: AbstractSet[str],
        language: AbstractSet[list[str]],
        as_partial: bool = True,
    ) -> MyDFA:
        """
        Directly computes the minimal DFA accepting the finite language given as input.
        Uses the algorithm described in Finite-State Techniques by Mihov and Schulz,
        Chapter 10

        Parameters
        ----------
        input_symbols : AbstractSet[str]
            The set of input symbols to construct the DFA over.
        language : AbstractSet[str]
            The language to accept.
        as_partial : bool, default: True
            Whether or not to construct this as a partial DFA.

        Returns
        ------
        MyDFA
            The DFA accepting the desired language.
        """
        new_input_symbols = {
            cls.multicharenv.get_or_set(symbol) for symbol in input_symbols
        }
        new_language = {
            cls.multicharenv.multi_to_single_word(word) for word in language
        }
        return cls(
            DFA.from_finite_language(
                new_input_symbols, new_language, as_partial=as_partial
            )
        )

    @classmethod
    def from_nfa(
        cls: Type[MyDFA],
        target_nfa: MyNFA,
        *,
        retain_names: bool = False,
        minify: bool = True,
    ) -> MyDFA:
        """
        Initialize this DFA as one equivalent to the given NFA. Note
        that this usually returns a partial DFA by default.

        Parameters
        ----------
        target_nfa : NFA
            The NFA to construct an equivalent DFA for.
        retain_names : bool, default: False
            Whether or not to retain state names during processing.
        minify : bool, default: True
            Whether or not to minify the DFA resulting from the input NFA.

        Returns
        ------
        MyDFA
            The DFA accepting the language of the input NFA.
        """
        return cls(
            DFA.from_nfa(target_nfa._nfa, retain_names=retain_names, minify=minify)
        )

    def iter_transitions(
        self,
    ) -> Generator[Tuple[DFAStateT, DFAStateT, str], None, None]:
        """
        Iterate over all transitions in the DFA. Each transition is a tuple
        of the form (from_state, to_state, symbol).

        Returns
        ------
        Generator[Tuple[DFAStateT, DFAStateT, str], None, None]
            The desired generator over the DFA transitions.
        """
        for state1, state2, symbol in self._dfa.iter_transitions():
            yield (state1, state2, self.multicharenv.single_to_multi_char[symbol])

    def _get_input_path(
        self, input_str: list[str]
    ) -> Tuple[list[Tuple[DFAStateT, DFAStateT, DFASymbolT]], bool]:
        """
        Calculate the path taken by input.

        Parameters
        ------
        input_str : str
            The input string to run on the DFA.

        Returns
        ------
        Tuple[List[Tuple[DFAStateT, DFAStateT, DFASymbolT], bool]]
            A list of all transitions taken in each step and a boolean
            indicating whether the DFA accepted the input.

        """
        new_input_str = self.multicharenv.multi_to_single_word(input_str)
        return self._dfa._get_input_path(new_input_str)


class MyNFA(MyFA):
    multicharenv = MultiCharactersEnvironment()

    def __init__(self, nfa: NFA):
        self._nfa = nfa
        self._fa = nfa

    @classmethod
    def create(
        cls,
        *,
        states: AbstractSet[NFAStateT],
        input_symbols: AbstractSet[str],
        transitions: NFATransitionsT,
        initial_state: NFAStateT,
        final_states: AbstractSet[NFAStateT],
    ) -> MyNFA:
        new_input_symbols = {
            cls.multicharenv.get_or_set(symbol) for symbol in input_symbols
        }
        new_transitions: dict[DFAStateT, dict[str, DFAStateT]] = {}
        for state1, tmp_transition in transitions.items():
            new_transitions[state1] = {}
            for symbol, states2 in tmp_transition.items():
                new_transitions[state1][cls.multicharenv.get(symbol)] = states2

        nfa = NFA(
            states=states,
            input_symbols=new_input_symbols,
            transitions=new_transitions,
            initial_state=initial_state,
            final_states=final_states,
        )
        return cls(nfa)

    @property
    def states(self) -> AbstractSet[NFAStateT]:
        """Set of the NFA's valid states."""
        return self._nfa.states

    @property
    def input_symbols(self) -> AbstractSet[str]:
        """Set of the NFA's valid input symbols, each of which is a singleton
        string."""
        return self._nfa.input_symbols

    @property
    def transitions(self) -> NFATransitionsT:
        """Dict consisting of the transitions for each state. Each key is a
        state name, and each value is another dict which maps a symbol
        (the key) to a set of states (the value)."""
        return self._nfa.transitions

    @property
    def initial_state(self) -> NFAStateT:
        """The initial state for this NFA."""
        return self._nfa.initial_state

    @property
    def final_states(self) -> AbstractSet[NFAStateT]:
        """A set of final states for this NFA."""
        return self._nfa.final_states

    def __add__(self, other: MyNFA) -> MyNFA:
        """Return the concatenation of this NFA and another NFA."""
        return MyNFA(self._nfa.__add__(other._nfa))

    def __or__(self, other: MyNFA) -> MyNFA:
        """Return the union of this NFA and another NFA."""
        return MyNFA(self._nfa.__or__(other._nfa))

    def __and__(self, other: MyNFA) -> MyNFA:
        """Return the union of this NFA and another NFA."""
        return MyNFA(self._nfa.__and__(other._nfa))

    @classmethod
    def from_dfa(cls: Type[MyNFA], target_dfa: MyDFA) -> MyNFA:
        """
        Initialize this NFA as one equivalent to the given DFA.

        Parameters
        ----------
        target_dfa : DFA
            The DFA to construct an equivalent NFA for.

        Returns
        ------
        MyNFA
            The NFA accepting the language of the input DFA.
        """
        return cls(NFA.from_dfa(target_dfa._dfa))

    @classmethod
    def from_regex(
        cls: Type[MyNFA],
        regex: str,
        *,
        input_symbols: Optional[AbstractSet[str]] = None,
    ) -> MyNFA:
        """
        Initialize this NFA as one equivalent to the given regular expression.

        Parameters
        ----------
        regex : str
            The regex to construct an equivalent NFA for. CHaracters must be separated by spaces or reservd characters.
        input_symbols : Optional[AbstractSet[str]], default: None
            The set of input symbols to create the NFA over. If not
            set, defaults to all ascii letters and digits.

        Returns
        ------
        MyNFA
            The NFA accepting the language of the input regex.
        """
        new_split_regex = []
        for char in regex_to_token_list(regex):
            if char in RESERVED_CHARACTERS:
                new_split_regex.append(char)
            else:
                new_split_regex.append(cls.multicharenv.get_or_set(char))

        new_regex = "".join(new_split_regex)

        new_input_symbols = (
            None
            if input_symbols is None
            else {cls.multicharenv.get_or_set(symbol) for symbol in input_symbols}
        )

        return cls(NFA.from_regex(new_regex, input_symbols=new_input_symbols))

    def validate(self) -> None:
        """
        Raises an exception if this automaton is not internally consistent.

        Raises
        ------
        InvalidStateError
            If this NFA has invalid states in the transition dictionary.
        MissingStateError
            If this NFA has states missing from the transition dictionary.
        InvalidSymbolError
            If this NFA has invalid symbols in the transition dictionary.
        """
        self._nfa.validate()

    def eliminate_lambda(self) -> MyNFA:
        """
        Returns an equivalent NFA with lambda transitions removed.

        Returns
        ------
        MyNFA
            The equivalent NFA with lambda transitions removed.
        """
        return MyNFA(self._nfa.eliminate_lambda())

    def read_input_stepwise(
        self, input_str: list[str]
    ) -> Generator[AbstractSet[NFAStateT], None, None]:
        """
        Return a generator that yields the configuration of this NFA at each
        step while reading input.

        Parameters
        ----------
        input_str : str
            The input string to read.

        Yields
        ------
        Generator[AbstractSet[NFAStateT], None, None]
            A generator that yields the current configuration (a set of states) of
            the NFA after each step of reading input.

        Raises
        ------
        RejectionException
            Raised if this NFA does not accept the input string.
        """
        new_inpunt_str = self.multicharenv.multi_to_single_word(input_str)
        yield from self._nfa.read_input_stepwise(new_inpunt_str)

    def union(self, other: MyNFA) -> MyNFA:
        """
        Given two NFAs, M1 and M2, which accept the languages
        L1 and L2 respectively, returns an NFA which accepts
        the union of L1 and L2.

        Parameters
        ----------
        other : NFA
            The NFA we want to take a union with.

        Returns
        ------
        MyNFA
            An NFA accepting the union of the two input NFAs.
        """
        return MyNFA(self._nfa.union(other._nfa))

    def concatenate(self, other: MyNFA) -> MyNFA:
        """
        Given two NFAs, M1 and M2, which accept the languages
        L1 and L2 respectively, returns an NFA which accepts
        the language L1 concatenated with L2.

        Parameters
        ----------
        other : NFA
            The NFA we want to concatenate with.

        Returns
        ------
        MyNFA
            An NFA accepting the language concatenation of the two input NFAs.
        """
        return MyNFA(self._nfa.concatenate(other._nfa))

    def kleene_star(self) -> MyNFA:
        """
        Given an NFA which accepts the language L, returns
        an NFA which accepts L repeated 0 or more times.

        Returns
        ------
        MyNFA
            An NFA accepting the finite repetition of the input NFA.
        """
        return MyNFA(self._nfa.kleene_star())

    def option(self) -> MyNFA:
        """
        Given an NFA which accepts the language L, returns
        an NFA which accepts L repeated 0 or 1 times.

        Returns
        ------
        MyNFA
            An NFA accepting the optional of the input NFA.
        """
        return MyNFA(self._nfa.option())

    def reverse(self) -> MyNFA:
        """
        Given an NFA which accepts the language L,
        returns an NFA which accepts the reverse of L.

        Returns
        ------
        MyNFA
            An NFA accepting the reversal of the input NFA.
        """
        return MyNFA(self._nfa.reverse())

    def intersection(self, other: MyNFA) -> MyNFA:
        """
        Given two NFAs, M1 and M2, which accept the languages
        L1 and L2 respectively, returns an NFA which accepts
        the intersection of L1 and L2.

        Parameters
        ----------
        other : NFA
            The NFA we want to take an intersection with.

        Returns
        ------
        MyNFA
            An NFA accepting the intersection of the two input NFAs.
        """
        return MyNFA(self._nfa.intersection(other._nfa))

    def shuffle_product(self, other: MyNFA) -> MyNFA:
        """
        Given two NFAs, M1 and M2, which accept the languages
        L1 and L2 respectively, returns an NFA which accepts
        the shuffle of L1 and L2.

        Parameters
        ----------
        other : NFA
            The NFA we want to take a shuffle product with.

        Returns
        ------
        MyNFA
            An NFA accepting the shuffle product of the two input NFAs.
        """
        return MyNFA(self._nfa.shuffle_product(other._nfa))

    def right_quotient(self, other: MyNFA) -> MyNFA:
        """
        Given two NFAs, M1 and M2, which accept the languages
        L1 and L2 respectively, returns an NFA which accepts
        the right quotient of L1 with respect to L2 (L1 / L2).

        Construction is based off of the one described here:
        https://cs.stackexchange.com/a/102043

        Parameters
        ----------
        other : NFA
            The NFA we want to take a right quotient with.

        Returns
        ------
        MyNFA
            An NFA accepting the right quotient of the two input NFAs.
        """
        return MyNFA(self._nfa.right_quotient(other._nfa))

    def left_quotient(self, other: MyNFA) -> MyNFA:
        """
        Given two NFAs, M1 and M2, which accept the languages
        L1 and L2 respectively, returns an NFA which accepts
        the left quotient of L1 with respect to L2 (L2 \\ L1).

        Construction is based off of the one described here:
        https://cs.stackexchange.com/a/102043

        Parameters
        ----------
        other : NFA
            The NFA we want to take a left quotient with.

        Returns
        ------
        MyNFA
            An NFA accepting the left quotient of the two input NFAs.
        """
        return MyNFA(self._nfa.left_quotient(other._nfa))

    def __eq__(self, other: Any) -> bool:
        """
        Return True if two NFAs are equivalent. Uses an optimized version of
        the extended Hopcroft-Karp algorithm (HKe). See
        https://arxiv.org/abs/0907.5058
        """
        if not isinstance(other, MyNFA):
            return NotImplemented
        return self._nfa.__eq__(other._nfa)

    @classmethod
    def edit_distance(
        cls: Type[MyNFA],
        input_symbols: AbstractSet[str],
        reference_str: list[str],
        max_edit_distance: int,
        *,
        insertion: bool = True,
        deletion: bool = True,
        substitution: bool = True,
    ) -> MyNFA:
        """
        Constructs the Levenshtein NFA for the given reference_str and given
        Levenshtein distance. This NFA recognizes strings within the given
        Levenshtein distance (commonly called edit distance) of the
        reference_str. Parameters control which error types the NFA will
        recognize (insertions, deletions, or substitutions). At least one error
        type must be set.

        If insertion and deletion are False and substitution is True, then this
        is the same as Hamming distance.

        If insertion and deletion are True and substitution is False, then this
        is the same as LCS distance.

        insertion, deletion, and substitution all default to True.

        Code adapted from:
        http://blog.notdot.net/2010/07/Damn-Cool-Algorithms-Levenshtein-Automata

        Parameters
        ----------
        input_symbols : AbstractSet[str]
            The set of input symbols to construct the NFA over.
        reference_str : str
            The reference string the NFA will use to recognize other close strings.
        max_edit_distance : int
            The maximum edit distance from the reference string this NFA will recognize.
            Must be positive.
        insertion : bool, default: True
            Whether to recognize insertion edits relative to the reference string.
        deletion : bool, default: True
            Whether to recognize deletion edits relative to the reference string.
        substitution : bool, default: True
            Whether to recognize substitution edits relative to the reference string.

        Returns
        ------
        MyNFA
            An NFA accepting all strings within the given edit distance to the reference
            string.

        Raises
        ------
        ValueError
            Raised if the max_edit_distance is negative or all of the error flags are
            set to False (at least one must be True).
        """
        new_input_symbols = {
            cls.multicharenv.get_or_set(symbol) for symbol in input_symbols
        }
        new_reference_str = cls.multicharenv.multi_to_single_word(reference_str)
        return cls(
            NFA.edit_distance(
                new_input_symbols,
                new_reference_str,
                max_edit_distance,
                insertion=insertion,
                deletion=deletion,
                substitution=substitution,
            )
        )

    def iter_transitions(
        self,
    ) -> Generator[Tuple[NFAStateT, NFAStateT, str], None, None]:
        """
        Iterate over all transitions in the NFA. Each transition is a tuple
        of the form (from_state, to_state, symbol).

        Returns
        ------
        Generator[Tuple[NFAStateT, NFAStateT, str], None, None]
            The desired generator over the NFA transitions.
        """
        for state1, state2, symbol in self._nfa.iter_transitions():
            yield (state1, state2, self.multicharenv.single_to_multi_char[symbol])

    def _get_input_path(self, input_str: list[str]) -> Tuple[InputPathListT, bool]:
        """
        Calculate the path taken by input.

        Parameters
        ------
        input_str : str
            The input string to run on the DFA.

        Returns
        ------
        Tuple[List[Tuple[DFAStateT, DFAStateT, DFASymbolT], bool]]
            A list of all transitions taken in each step and a boolean
            indicating whether the DFA accepted the input.

        """
        new_input_str = self.multicharenv.multi_to_single_word(input_str)
        return self._nfa._get_input_path(new_input_str)


class MyGNFA(MyFA):
    multicharenv = MultiCharactersEnvironment()

    def __init__(self, gnfa: GNFA):
        self._gnfa = gnfa
        self._fa = gnfa

    @classmethod
    def create(
        cls,
        *,
        states: AbstractSet[GNFAStateT],
        input_symbols: AbstractSet[str],
        transitions: GNFATransitionsT,
        initial_state: GNFAStateT,
        final_state: GNFAStateT,
    ) -> MyGNFA:
        new_input_symbols = {
            cls.multicharenv.get_or_set(symbol) for symbol in input_symbols
        }
        new_transitions: dict[DFAStateT, dict[str, DFAStateT]] = {}
        for state1, tmp_transition in transitions.items():
            new_transitions[state1] = {}
            for symbol, states2 in tmp_transition.items():
                new_transitions[state1][cls.multicharenv.get(symbol)] = states2

        gnfa = GNFA(
            states=states,
            input_symbols=new_input_symbols,
            transitions=new_transitions,
            initial_state=initial_state,
            final_state=final_state,
        )
        return cls(gnfa)

    @property
    def states(self) -> AbstractSet[GNFAStateT]:
        """Set of the GNFA's valid states."""
        return self._gnfa.states

    @property
    def input_symbols(self) -> AbstractSet[str]:
        """Set of the GNFA's valid input symbols, each of which is a singleton
        string."""
        return self._gnfa.input_symbols

    @property
    def transitions(self) -> GNFATransitionsT:
        """A dict with the transitions for each state, except `final_state`.
        Each key is a state name and each value is dict which maps a state
        (the key) to the transition expression (the value) or None.
        The transition expression is a regular expression (string) over
        `input_symbols`, and the following symbols only: `*`, `|`, `?`, `()`.

        This is a subset of the standard regular expressions using this package."""
        return self._gnfa.transitions

    @property
    def initial_state(self) -> GNFAStateT:
        """The initial state for this GNFA. Has transitions going to every
        other state, but no transitions coming in from any other state."""
        return self._gnfa.initial_state

    @property
    def final_states(self) -> GNFAStateT:
        """A single final state for this GNFA. Has transitions coming in from every
        other state, but no transitions going to any other state.
        Must be different from the `initial_state`."""
        return self._gnfa.final_states

    @classmethod
    def from_dfa(cls: Type[MyGNFA], target_dfa: MyDFA) -> MyGNFA:
        """
        Initialize this GNFA as one equivalent to the given DFA.

        Parameters
        ----------
        target_dfa : DFA
            The DFA to construct an equivalent GNFA for.

        Returns
        ------
        MyGNFA
            The GNFA accepting the language of the input DFA.
        """
        return cls(GNFA.from_dfa(target_dfa._dfa))

    @classmethod
    def from_nfa(cls: Type[MyGNFA], target_nfa: MyNFA) -> MyGNFA:
        """
        Initialize this GNFA as one equivalent to the given NFA.

        Parameters
        ----------
        target_nfa : NFA
            The NFA to construct an equivalent GNFA for.

        Returns
        ------
        MyGNFA
            The GNFA accepting the language of the input NFA.
        """
        return cls(GNFA.from_nfa(target_nfa._nfa))

    def validate(self) -> None:
        """
        Raises an exception if this automaton is not internally consistent.

        Raises
        ------
        InvalidStateError
            If this GNFA has invalid states in the transition dictionary.
        MissingStateError
            If this GNFA has states missing from the transition dictionary.
        InvalidRegexError
            If this GNFA has invalid regex in the transition dictionary.
        """
        self._gnfa.validate()

    def to_regex(self) -> str:
        """
        Convert GNFA to regular expression.

        Returns
        ------
        str
            A regular expression equivalent to the input GNFA.
        """
        regex = self._gnfa.to_regex()
        new_regex = ""
        prev_token_was_reserved = True
        for char in regex:
            if char in RESERVED_CHARACTERS:
                new_regex += char
                prev_token_was_reserved = True
            else:
                if not prev_token_was_reserved:
                    new_regex += " "
                new_regex += self.multicharenv.single_to_multi_char[char]
                prev_token_was_reserved = False

        return new_regex

    def read_input_stepwise(self, input_str: list[str]) -> NoReturn:
        # No docstring because this is a dummy implementation
        raise NotImplementedError

    def iter_transitions(
        self,
    ) -> Generator[Tuple[GNFAStateT, GNFAStateT, str], None, None]:
        """
        Iterate over all transitions in the GNFA. Each transition is a tuple
        of the form (from_state, to_state, symbol).

        Returns
        ------
        Generator[Tuple[GNFAStateT, GNFAStateT, str], None, None]
            The desired generator over the GNFA transitions.
        """
        for state1, state2, symbol in self._gnfa.iter_transitions():
            yield (state1, state2, self.multicharenv.single_to_multi_char[symbol])

    def _get_input_path(self, input_str: list[str]) -> NoReturn:
        raise NotImplementedError(
            f"_get_input_path is not implemented for {self.__class__}"
        )
