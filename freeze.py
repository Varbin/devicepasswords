"""
Pin the dependencies given in pyproject.toml.
"""

from venv import EnvBuilder
from shutil import rmtree
from subprocess import check_call
from tomllib import load
from os import mkdir, path, remove

BUILD = "build"
REQUIREMENTS = "build/requirements.txt"
VENV = "build/.venv"

try:
    try:
        mkdir(BUILD, mode=0o750)
    except FileExistsError:
        pass
    try:
        mkdir(VENV, mode=0o750)
    except FileExistsError:
        pass

    EnvBuilder().create(VENV)
    with open("pyproject.toml", "rb") as project:
        pyproject = load(project)
    with open(REQUIREMENTS, "w") as requirements:
        requirements.write("\n".join(pyproject["project"]["dependencies"]))
    check_call([VENV + "/bin/python", "-m", "ensurepip"])
    check_call([VENV + "/bin/pip3", "install", "-r", REQUIREMENTS])
    with open("requirements.txt", "w") as requirements:
        check_call([VENV + "/bin/pip3", "freeze", "-r", REQUIREMENTS],
                   stdout=requirements)
finally:
    if path.isdir(VENV):
        rmtree(VENV)
    if path.exists(REQUIREMENTS):
        remove(REQUIREMENTS)