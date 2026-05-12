"""Game of Life package.

This package implements Conway's Game of Life cellular automaton, a classic
computer science demonstration of how complex behavior can emerge from simple rules.

The package provides:
- A model for simulating the Game of Life with configurable grids and patterns
- Multiple view implementations (CLI and matplotlib-based visualization)
- Support for both toroidal and flat boundary conditions
- Pattern encoding in Run Length Encoded (RLE) format

"""

from game_of_life.main import app

app()
