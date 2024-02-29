"""
Module containing types used in Janus-Core
"""

from pathlib import Path, PurePath
from typing import IO, Literal, Optional, Sequence, TypedDict, TypeVar, Union

from ase import Atoms
import numpy as np
from numpy.typing import NDArray

# General

T = TypeVar("T")
MaybeList = Union[T, list[T]]
MaybeSequence = Union[T, Sequence[T]]
PathLike = Union[str, Path]


# ASE Arg types


class ASEReadArgs(TypedDict, total=False):
    """Main arguments for ase.io.read"""

    filename: Union[str, PurePath, IO]
    index: Union[int, slice, str]
    format: Optional[str]
    parallel: bool
    do_not_split_by_at_sign: bool


class ASEWriteArgs(TypedDict, total=False):
    """Main arguments for ase.io.write"""

    filename: Union[str, PurePath, IO]
    images: MaybeSequence[Atoms]
    format: Optional[str]
    parallel: bool
    append: bool


class ASEOptArgs(TypedDict, total=False):
    """Main arugments for ase optimisers"""

    restart: Optional[bool]
    logfile: Optional[PathLike]
    trajectory: PathLike


class ASEOptRunArgs(TypedDict, total=False):
    """Main arugments for running ase optimisers"""

    fmax: float
    steps: int


# Janus specific
Architectures = Literal["mace", "mace_mp", "mace_off", "m3gnet", "chgnet"]
Devices = Literal["cpu", "cuda", "mps"]


class CalcResults(TypedDict, total=False):
    """Return type from calculations"""

    energy: MaybeList[float]
    forces: MaybeList[NDArray[np.float64]]
    stress: MaybeList[NDArray[np.float64]]
