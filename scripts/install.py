#!/usr/bin/env python3
"""Create an isolated environment and install this skill's dependencies."""
from pathlib import Path
import os
import subprocess
import sys
import venv


def main():
    if sys.version_info < (3, 10):
        raise SystemExit('Python 3.10+ is required')
    root = Path(__file__).resolve().parents[1]
    env = root / '.venv'
    venv.EnvBuilder(with_pip=True).create(env)
    python = env / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    subprocess.run([str(python), '-m', 'pip', 'install', '-r', str(root / 'requirements.txt')], check=True)
    print(f'Installed. Python: {python}')


if __name__ == '__main__':
    main()
