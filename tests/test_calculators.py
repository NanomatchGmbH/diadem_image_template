import itertools
import pathlib
import shutil
import subprocess
import tempfile

import pytest
import yaml


def docker_run_helper(image_name: str, workdir: pathlib.Path, molecule: pathlib.Path, calculator: pathlib.Path):
    run_command = ["docker","run","--rm", image_name,f"-v{workdir}:/home/diadem",f"-v{molecule}:/home/diadem/molecule.yml",f"-v{calculator}:/home/diadem/calculator.yml"]
    output = subprocess.check_output(run_command,encoding="utf8")

@pytest.fixture
def image_name():
    image_name = subprocess.check_output(["git","describe"], encoding="utf8")
    return image_name

def molecules() -> list[pathlib.Path]:
    molpath = pathlib.Path(__file__).parent / "inputs" / "molecules"
    files = [*molpath.glob("*.yml")]
    return files


def calculators() -> list[pathlib.Path]:
    calcpath = pathlib.Path(__file__).parent / ".." / "calculators"
    files = [*calcpath.glob("*.yml")]
    return files

@pytest.mark.parametrize("molecule, calculator", itertools.product(molecules(), calculators()))
def test_calculators(molecule: pathlib.Path, calculator: pathlib.Path, image_name: str) -> None:
    output_directory = pathlib.Path(__file__).parent / "test_outputs" / calculator.name / molecule.name
    output_directory.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory as tmpdir:
        docker_run_helper(image_name, tmpdir, molecule, calculator)
        resultfile = pathlib.Path(tmpdir)/"result.yml"
        assert resultfile.is_file(), "Did not find result.yml"
        ref_resultfile = output_directory/"result_reference.yml"
        if ref_resultfile.is_file():
            with ref_resultfile.open('rt') as infile:
                ref_dict = yaml.safe_load(infile)
            with resultfile.open('rt') as infile:
                result_dict = yaml.safe_load(infile)
            assert ref_dict == result_dict
        else:
            print("Did not find reference. Will copy result.yml.")
            shutil.copy(resultfile, ref_resultfile)
