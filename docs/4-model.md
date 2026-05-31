# The Model

<!-- TODO: ADD IN link to MVC article overview  -->
The Model is the centerpiece of the Game of Life simulation.
It's responsible for maintaining the game state and computing how that state evolves over time. In the Model-View-Controller (MVC) architecture, the Model knows nothing about how it's being displayed or which buttons the user is clicking. It only understands one thing - the rules of Conway's Game of Life and how to apply them.

## Understanding Conway's Game of Life

Conway's Game of Life is a cellular automaton where cells on a grid live or die based on simple rules. These rules are beautifully elegant:

1. A live cell with 2 or 3 live neighbors survives to the next generation
2. A dead cell with exactly 3 live neighbors becomes alive
3. All other cells die or stay dead

That's it. From these three rules, complex and often unpredictable patterns emerge. Some configurations oscillate endlessly. Others move across the grid like spaceships. Still others produce intricate structures that change in fascinating ways.

### From Rules to Code: The Single Responsibility Principle

When we translate these rules into code, we face an interesting design decision. We could write one large method that computes the next generation and updates the grid. But notice that Conway's rules describe two distinct concerns,

1. Computing what the next generation should be
2. Advancing the simulation

As such, our implementation splits these concerns into two methods. The `GameOfLife` class provides `compute_next_generation()` and `step()`.
This split follows the Single Responsibility Principle. The former applies Conway's rules. The latter coordinates the simulation's progression and maintain the history. Separating these makes the code easier to test. For example, the computation of the next generation can be tested independently of the stepping.

```python title="model.py in GameOfLife class"
    def compute_next_generation(self) -> NDArrayU8:
{%
    include-markdown "../src/game_of_life/model.py"
    start="# Finds the number of neighbours that are alive"
    end="def step"
%}
```

This method computes the next generation by first determining how many neighbours are alive. Using the `np.roll` function we can shift the grid to get a neighboring value at the current index. By adding up all neighbours, we can determine how many neighbours are alive. The next steps involve applying the rules of the game and handling the boundary. These two steps result in an array of what the grid will look like at the next step. Thus, this method has only one responsibility.

```python title="model.py in GameOfLife class"
    def step(self) -> None:
        self._generation += 1
        self._grid = self.compute_next_generation()
        self._history.append(self._grid)
```

This method is responsible for coordinating all the different components involved in moving from one time step to the next. It is also the means for controller to manipulate the model such that it updates for the view. This corresponds to the parts in purple in the MVC diagram below

```mermaid
---
config:
  look: handDrawn
  theme: base
---
flowchart TD
  user([User])
  user -->|provides input| controller
  controller -->|manipulates| model
  model -->|updates| view
  view -->|renders for| user

  style user fill:#DDF9FF,stroke:#82E8FF
  style model fill:#E3DDFF,stroke:#BDAEFF
  linkStyle 1,2 stroke:#7455FF,stroke-width:4px
```

### Grid as a Data Container

The grid is represented as a 2D NumPy array in which each cell holds a value of either 0 (dead) or 1 (alive). The `GameOfLife` object owns and manages this array, external components do not have direct write access to it. This encapsulation is intentional. By restricting modification to the GameOfLife object itself, the state of the grid remains predictable and controlled throughout the program's execution.

This is an example of [composition in object-oriented design](https://realpython.com/inheritance-composition-python/#whats-composition). This a relationship in which one object owns another as an attribute. Here, the grid is a constituent part of the `GameOfLife` object, not an external dependency. This can be understood through a simple distinction: a grid _is not_ a `GameOfLife` (which rules out inheritance), but a GameOfLife _has a_ grid (which confirms composition). This _has-a_ relationship is what determines how the two are structured and how ownership is assigned in the code.

![inheritance vs composition](https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fmiro.medium.com%2Fv2%2Fresize%3Afit%3A1200%2F1*mcv2uIZnDYodmTBJGjtwXg.png&f=1&nofb=1&ipt=89cd9ae1631b28c9ddd09029c33d3816b82e24841be716ce7d432cd2d15594da){width="400" align=right}

!!! tip
    There are two major concepts in object oriented programming (OOP): inheritance and composition. A heuristic to determine what the most appropriate relationship between the two is to use the _is-a_ and _has-a_ test. For example, a cat _is a_ animal. So, a `Cat` class should inherit from a parent `Animal` class. And a cat _has a_ tail. So, a `Cat` should contain an object of `Tail`. It would be incorrect for the `Tail` to inherit from the `Cat` class as a `Tail` is not a `Cat`.

!!! abstract "Further Reading"
    Another design pattern related to inheritance and composition is to [favour composition over inheritance](https://en.wikipedia.org/wiki/Composition_over_inheritance) to give a design more flexibility.
