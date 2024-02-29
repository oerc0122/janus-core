"""Prepare and perform single point calculations."""

import pathlib
from typing import Optional

from ase.io import read
from numpy import ndarray

from janus_core.mlip_calculators import choose_calculator

from .janus_types import (
    Architectures,
    ASEReadArgs,
    CalcResults,
    Devices,
    MaybeList,
    MaybeSequence,
)


class SinglePoint:
    """
    Prepare and perform single point calculations.

    Parameters
    ----------
    system : str
        System to simulate.
    architecture : Literal[architectures]
        MLIP architecture to use for single point calculations.
        Default is "mace_mp".
    device : Literal[devices]
        Device to run model on. Default is "cpu".
    read_kwargs : Optional[dict[str, Any]]
        Keyword arguments to pass to ase.io.read. Default is {}.
    **kwargs
        Additional keyword arguments passed to the selected calculator.

    Attributes
    ----------
    architecture : Literal[architectures]
        MLIP architecture to use for single point calculations.
    system : str
        System to simulate.
    device : Literal[devices]
        Device to run MLIP model on.

    Methods
    -------
    read_system(**kwargs)
        Read system and system name.
    set_calculator(**kwargs)
        Configure calculator and attach to system.
    run_single_point(properties=None)
        Run single point calculations.
    """

    def __init__(
        self,
        system: str,
        architecture: Architectures = "mace_mp",
        device: Devices = "cpu",
        read_kwargs: Optional[ASEReadArgs] = None,
        **kwargs,
    ) -> None:
        """
        Read the system being simulated and attach an MLIP calculator.

        Parameters
        ----------
        system : str
            System to simulate.
        architecture : Literal[architectures]
            MLIP architecture to use for single point calculations.
            Default is "mace_mp".
        device : Literal[devices]
            Device to run MLIP model on. Default is "cpu".
        read_kwargs : Optional[dict[str, Any]]
            Keyword arguments to pass to ase.io.read. Default is {}.
        **kwargs
            Additional keyword arguments passed to the selected calculator.
        """
        self.architecture = architecture
        self.device = device
        self.system = system

        # Read system and get calculator
        read_kwargs = read_kwargs if read_kwargs else {}
        self.read_system(**read_kwargs)
        self.set_calculator(**kwargs)

    def read_system(self, **kwargs) -> None:
        """
        Read system and system name.

        If the file contains multiple structures, only the last configuration
        will be read by default.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to ase.io.read.
        """
        self.sys = read(self.system, **kwargs)
        self.sysname = pathlib.Path(self.system).stem

    def set_calculator(
        self, read_kwargs: Optional[ASEReadArgs] = None, **kwargs
    ) -> None:
        """
        Configure calculator and attach to system.

        Parameters
        ----------
        read_kwargs : Optional[ASEReadArgs]
            Keyword arguments to pass to ase.io.read. Default is {}.
        **kwargs
            Additional keyword arguments passed to the selected calculator.
        """
        calculator = choose_calculator(
            architecture=self.architecture,
            device=self.device,
            **kwargs,
        )
        if self.sys is None:
            read_kwargs = read_kwargs if read_kwargs else {}
            self.read_system(**read_kwargs)

        if isinstance(self.sys, list):
            for sys in self.sys:
                sys.calc = calculator

        else:
            self.sys.calc = calculator

    def _get_potential_energy(self) -> MaybeList[float]:
        """
        Calculate potential energy using MLIP.

        Returns
        -------
        MaybeList[float]
            Potential energy of system(s).
        """
        if isinstance(self.sys, list):
            return [sys.get_potential_energy() for sys in self.sys]

        return self.sys.get_potential_energy()

    def _get_forces(self) -> MaybeList[ndarray]:
        """
        Calculate forces using MLIP.

        Returns
        -------
        MaybeList[ndarray]
            Forces of system(s).
        """
        if isinstance(self.sys, list):
            return [sys.get_forces() for sys in self.sys]

        return self.sys.get_forces()

    def _get_stress(self) -> MaybeList[ndarray]:
        """
        Calculate stress using MLIP.

        Returns
        -------
        MaybeList[ndarray]
            Stress of system(s).
        """
        if isinstance(self.sys, list):
            return [sys.get_stress() for sys in self.sys]

        return self.sys.get_stress()

    def run_single_point(self, properties: MaybeSequence[str] = ()) -> CalcResults:
        """
        Run single point calculations.

        Parameters
        ----------
        properties : MaybeSequence[str]
            Physical properties to calculate. If not specified, "energy",
            "forces", and "stress" will be returned.

        Returns
        -------
        CalcResults
            Dictionary of calculated results.
        """
        results: CalcResults = {}
        if isinstance(properties, str):
            properties = [properties]

        if "energy" in properties or len(properties) == 0:
            results["energy"] = self._get_potential_energy()
        if "forces" in properties or len(properties) == 0:
            results["forces"] = self._get_forces()
        if "stress" in properties or len(properties) == 0:
            results["stress"] = self._get_stress()

        return results
