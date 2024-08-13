"""Test eos commandline interface."""

from pathlib import Path

from ase.io import read
import pytest
from typer.testing import CliRunner
import yaml

from janus_core.cli.janus import app
from tests.utils import assert_log_contains, strip_ansi_codes

DATA_PATH = Path(__file__).parent / "data"

runner = CliRunner()


def test_help():
    """Test calling `janus eos --help`."""
    result = runner.invoke(app, ["eos", "--help"])
    assert result.exit_code == 0
    assert "Usage: janus eos [OPTIONS]" in strip_ansi_codes(result.stdout)


def test_eos(tmp_path):
    """Test calculating the equation of state."""
    log_path = tmp_path / "test.log"
    summary_path = tmp_path / "summary.yml"
    eos_raw_path = tmp_path / "NaCl-eos-raw.dat"
    eos_fit_path = tmp_path / "NaCl-eos-fit.dat"
    result = runner.invoke(
        app,
        [
            "eos",
            "--struct",
            DATA_PATH / "NaCl.cif",
            "--file-prefix",
            tmp_path / "NaCl",
            "--log",
            log_path,
            "--summary",
            summary_path,
        ],
    )
    assert result.exit_code == 0
    assert eos_raw_path.exists()
    assert eos_fit_path.exists()

    # Check contents of raw data file
    with open(eos_raw_path, encoding="utf8") as eos_raw_file:
        lines = eos_raw_file.readlines()

    assert len(lines) == 8
    assert lines[0] == "#Lattice Scalar | Energy [eV] | Volume [Å^3] \n"
    assert lines[4].split()[0] == "1.0"
    assert float(lines[4].split()[1]) == pytest.approx(-27.046359959669214)
    assert float(lines[4].split()[2]) == pytest.approx(184.05884033013012)

    # Check contents of fitted data file
    with open(eos_fit_path, encoding="utf8") as eos_fit_file:
        lines = eos_fit_file.readlines()

    assert len(lines) == 2
    assert lines[0] == "#Bulk modulus [GPa] | Energy [eV] | Volume [Å^3] \n"
    assert float(lines[1].split()[0]) == pytest.approx(27.186555689697165)
    assert float(lines[1].split()[1]) == pytest.approx(-27.046361904823204)
    assert float(lines[1].split()[2]) == pytest.approx(184.22281215770133)

    # Check only initial structure is minimized
    assert_log_contains(
        log_path,
        includes=["Minimising initial structure"],
        excludes=["Minimising lattice scalar = 1.0"],
    )

    # Read eos summary file
    assert summary_path.exists()
    with open(summary_path, encoding="utf8") as file:
        eos_summary = yaml.safe_load(file)

    assert "command" in eos_summary
    assert "janus eos" in eos_summary["command"]
    assert "start_time" in eos_summary
    assert "inputs" in eos_summary
    assert "end_time" in eos_summary

    assert "emissions" in eos_summary
    assert eos_summary["emissions"] > 0


def test_setting_lattice(tmp_path):
    """Test setting the lattice constants."""
    log_path = tmp_path / "test.log"
    summary_path = tmp_path / "summary.yml"
    eos_raw_path = tmp_path / "NaCl-eos-raw.dat"
    result = runner.invoke(
        app,
        [
            "eos",
            "--struct",
            DATA_PATH / "NaCl.cif",
            "--min-volume",
            0.8,
            "--max-volume",
            1.2,
            "--n-volumes",
            5,
            "--file-prefix",
            tmp_path / "NaCl",
            "--log",
            log_path,
            "--summary",
            summary_path,
        ],
    )
    assert result.exit_code == 0
    assert eos_raw_path.exists()

    # Check contents of raw data file
    with open(eos_raw_path, encoding="utf8") as eos_raw_file:
        lines = eos_raw_file.readlines()
    assert len(lines) == 6
    assert lines[3].split()[0] == "1.0"
    assert float(lines[1].split()[0]) == pytest.approx(0.8 ** (1 / 3))
    assert float(lines[5].split()[0]) == pytest.approx(1.2 ** (1 / 3))


test_data = [("--min-volume", 1), ("--max-volume", 0.9), ("--n-volumes", 0)]


@pytest.mark.parametrize("option, value", test_data)
def test_invalid_lattice(option, value, tmp_path):
    """Test setting the invalid lattice constants."""
    log_path = tmp_path / "test.log"
    summary_path = tmp_path / "summary.yml"
    result = runner.invoke(
        app,
        [
            "eos",
            "--struct",
            DATA_PATH / "NaCl.cif",
            option,
            value,
            "--file-prefix",
            tmp_path / "NaCl",
            "--log",
            log_path,
            "--summary",
            summary_path,
        ],
    )
    assert result.exit_code == 1
    assert isinstance(result.exception, ValueError)


def test_minimising_all(tmp_path):
    """Test minimising structures with different lattice constants."""
    log_path = tmp_path / "test.log"
    summary_path = tmp_path / "summary.yml"
    result = runner.invoke(
        app,
        [
            "eos",
            "--struct",
            DATA_PATH / "NaCl.cif",
            "--minimize-all",
            "--file-prefix",
            tmp_path / "NaCl",
            "--log",
            log_path,
            "--summary",
            summary_path,
        ],
    )
    assert result.exit_code == 0

    # Check minimizes multiple structures
    assert_log_contains(
        log_path,
        includes=[
            "Minimising initial structure",
            "Minimising lattice scalar = 1.0",
            "constant_volume: True",
        ],
    )


def test_writing_structs(tmp_path):
    """Test writing out generated structures."""
    log_path = tmp_path / "test.log"
    summary_path = tmp_path / "summary.yml"
    file_prefix = tmp_path / "example"
    generated_path = tmp_path / "example-generated.extxyz"

    result = runner.invoke(
        app,
        [
            "eos",
            "--struct",
            DATA_PATH / "NaCl.cif",
            "--n-volumes",
            4,
            "--file-prefix",
            file_prefix,
            "--write-structures",
            "--log",
            log_path,
            "--summary",
            summary_path,
        ],
    )
    assert result.exit_code == 0
    assert generated_path.exists()
    atoms = read(generated_path, index=":")
    assert len(atoms) == 5


def test_error_write_geomopt(tmp_path):
    """Test an error is raised if trying to write via geomopt."""
    log_path = tmp_path / "test.log"
    summary_path = tmp_path / "summary.yml"
    file_prefix = tmp_path / "example"

    minimize_kwargs = "{'write_results': True}"

    result = runner.invoke(
        app,
        [
            "eos",
            "--struct",
            DATA_PATH / "NaCl.cif",
            "--n-volumes",
            4,
            "--file-prefix",
            file_prefix,
            "--minimize",
            "--minimize-kwargs",
            minimize_kwargs,
            "--log",
            log_path,
            "--summary",
            summary_path,
        ],
    )
    assert result.exit_code == 1
    assert isinstance(result.exception, ValueError)


@pytest.mark.parametrize("read_kwargs", ["{'index': 1}", "{}"])
def test_valid_traj_input(read_kwargs, tmp_path):
    """Test valid trajectory input structure handled."""
    eos_raw_path = tmp_path / "traj-eos-raw.dat"
    eos_fit_path = tmp_path / "traj-eos-fit.dat"
    log_path = tmp_path / "test.log"
    summary_path = tmp_path / "summary.yml"

    result = runner.invoke(
        app,
        [
            "eos",
            "--struct",
            DATA_PATH / "NaCl-traj.xyz",
            "--read-kwargs",
            read_kwargs,
            "--file-prefix",
            tmp_path / "traj",
            "--log",
            log_path,
            "--summary",
            summary_path,
        ],
    )
    assert result.exit_code == 0
    assert eos_raw_path.exists()
    assert eos_fit_path.exists()


def test_invalid_traj_input(tmp_path):
    """Test invalid trajectory input structure handled."""
    log_path = tmp_path / "test.log"
    summary_path = tmp_path / "summary.yml"

    result = runner.invoke(
        app,
        [
            "eos",
            "--struct",
            DATA_PATH / "NaCl-traj.xyz",
            "--read-kwargs",
            "{'index': ':'}",
            "--file-prefix",
            tmp_path / "traj",
            "--log",
            log_path,
            "--summary",
            summary_path,
        ],
    )
    assert result.exit_code == 1
    assert isinstance(result.exception, ValueError)
