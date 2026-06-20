# Type Hinting

Python is a [dynamically typed language](https://www.baeldung.com/cs/statically-vs-dynamically-typed-languages), variables can hold any type of data, and their type can change at runtime. Python uses [duck typing](https://en.wikipedia.org/wiki/Duck_typing), it cares about what objects can *do* rather than what they *are*. This provides remarkable flexibility. However, this results in implicit assumptions scattered throughout the code. You might pass a string to a function that expects a number, or forget what type a variable contains. Then, at runtime, things break. Or fails silently.

[Type hints](https://docs.python.org/3/library/typing.html) are a way to make these implicit assumptions explicit. It enables documentation and verification of the types in your code without sacrificing Python's flexibility. They answer the question of "what type is this supposed to be, and what will go wrong if it is wrong?"

Type hints are not enforced by Python itself. They are [metadata](https://en.wikipedia.org/wiki/Metadata). These annotation tell the interpreter (and more importantly, developers and tools) what types are expected. This might sound optional, but in practice, type hints have become essential for writing maintainable research software. See [PEP 484](https://peps.python.org/pep-0484/) for the full specification.

## What Are Type Hints?

A type hint is an annotation that declares what type a variable, parameter, or return value should have. Here's the simplest example,

```python
def add(x: int, y: int) -> int:
    """Add two integers and return the result."""
    return x + y
```

Breaking this down:

- `x: int` says the parameter `x` should be an integer
- `y: int` says the parameter `y` should be an integer
- `-> int` says the function returns an integer

If you call `#!py add(2, 3)`, it works. If you call `#!py add("hello", "world")`, Python will still execute it (by concatenating strings to return `#!py "helloworld"`), because Python doesn't enforce type hints. But a type checker will complain and your IDE will warn you.

!!! abstract "TL;DR"
    Type hints are for tools and humans, _not_ for Python itself.

### Variable Type Hints

Variables can be annotated using this syntax,

```python
name: str = "game of life"
count: int = 42
ratio: float = 0.5
is_active: bool = True
```

The type annotation comes after the variable name, before the value. This tells anyone reading the code (or your IDE) what type the variable should hold.

## Why Type Hints Matter

### 1. IDE Support

When your IDE knows the type of a variable, it can help you immensely. Consider this example without type hints,

```python
game = create_game_of_life(config)
game.
```

When you type `game.` and pause, your IDE doesn't know what properties or methods `game` has. It can't autocomplete. Now with type hints,

```python
def create_game_of_life(config: GameOfLifeConfigFrom) -> GameOfLife:
    return GameOfLife(config.num_rows, config.num_cols, grid_creator=...)

game: GameOfLife = create_game_of_life(config)
game.
```

Your IDE knows `game` is a `GameOfLife` object. It can autocomplete and show you all available methods and properties: `game.step()`, `game.grid`, `game.generation`, `game.compute_next_generation()`, etc. This saves time and prevents typos.

### 2. Readability and Maintenance

Type hints act as inline documentation. Consider a function without hints,

```python
def process_data(data, factor):
    return [x * factor for x in data]
```

What type is `data`? Is it a list, tuple, or something else? What about `factor`? Is it a number? The function works, but the reader must trace through the code or guess. With type hints,

```python
def process_data(data: list[float], factor: float) -> list[float]:
    return [x * factor for x in data]
```

Now it's immediately clear, the function takes a list of floats and a scale factor, and returns a list of floats.

### 3. Catching Bugs Early

Type checkers are tools that analyze your code without running it. They can catch many bugs before they cause problems. For example,

```python
def divide(numerator: float, denominator: float) -> float:
    return numerator / denominator

result: int = divide(10, 2)  # Type checker warns: expected int, got float
```

The type checker warns you that the return type of `divide` is `float`, not `int`. This catches the mismatch before the code runs.

### 4. Better Code Organization

Type hints encourage better code design. When you must explicitly declare input and output types, you think more carefully about what your function does. Vague, overly-general functions become clearer, more focused.

## Duck Typing and the Limits of Type Hints

Python is built on a principle called *duck typing*: "If it walks like a duck and quacks like a duck, then it's a duck." In other words, Python cares less about what something *is* and more about what it can *do*.

![duck typing comic](https://4loc.wordpress.com/wp-content/uploads/2009/02/ducktyping1.jpg){ width=320, align=right }

Consider this function,

```python
def process(obj):
    return obj.process_data()
```

Python doesn't care what type `obj` is. It could be a custom class you defined, a third-party library class, or anything else, as long as it has a `process_data()` method, it works. This flexibility allows you to write generic functions that work with many types without knowing their names in advance.

However, this flexibility has a downside - duck typing is implicit. Developers must read the code to understand what methods are expected. An IDE can't autocomplete because it doesn't know what type `obj` is. If someone passes an object without a `process_data()` method, the code crashes at runtime with an error message rather than failing early. As the code base and developed over a longer period of time, it becomes a pain to have to trace backward each time to know what is required of the function.

Type hints make the implicit explicit,

```python
class DataProcessor:
    def process_data(self) -> dict:
        ...

def process(obj: DataProcessor) -> dict:
    return obj.process_data()
```

This makes the contract is clear. `process` expects something of type `DataProcessor` (or a subclass). Your IDE can autocomplete. Type checkers can verify calls at development time.

!!! warning
    The crucial limitation is that type hints are not enforced by Python at runtime. This means that `process("hello string")` can still be invoked and Python will try to execute it. If `"hello string"` doesn't have a `process_data()` method, you'll get an `AttributeError` at runtime, type hints notwithstanding.

    ```python
    process("hello string")  # No error from type hints, but AttributeError at runtime
    ```

    If a static type checker is not run before running the code or enabled in your IDE to scream at you, then the code will fail regardless of whether type hints are present.


This is why type hints are best paired with,

- Type checkers (such as, [mypy](https://mypy-lang.org/), [pyright](https://github.com/microsoft/pyright), [ty](https://docs.astral.sh/ty/)) that catch mismatches before runtime
    - [basedpyright](https://docs.basedpyright.com/latest/) is "a fork of pyright with various type checking improvements, pylance features and more." This is a much stricter type checker. I would only recommend this if you're more experienced with Python type hinting and know how to use their judgment to balance flexibility, safety and simplicity due to [its benefit](https://docs.basedpyright.com/latest/benefits-over-pyright/new-diagnostic-rules/).
- Unit tests that verify behavior
- Good documentation that clarifies expectations

Type hints improve code quality and developer experience, but they're not a substitute for careful testing and design.

### Type Checkers

As mentioned, type hints alone don't enforce anything. A type checker is a necessary tool that analyzes your code and reports type mismatches. The two main type checkers for Python are,

- [`mypy`](https://www.mypy-lang.org/): The original type checker, widely used
- [`pyright`](https://github.com/microsoft/pyright): Made by Microsoft, more modern and faster
- [`ty`](https://docs.astral.sh/ty/): A newer type checker that is faster than `mypy` and `pyright`. However, it is currently (June 2026) not as full-featured as `pyright` and `mypy` (e.g. it does not have a pre-commit hook).

In the `pyproject.toml`, `ty` has been installed as a dev dependency,

```toml title="excerpt of pyproject.toml"
[dependency-groups]
dev = [
    ...
    "ty",   # Type checker and language server
]
```

`ty` can be run from the command line using,

```console
$ ty check .
```

It analyzes your code and reports any type inconsistencies. You can also configure your IDE to show type checker warnings in real time, where the warnings appear inline as you code.

## A Short Tour of Python Types

### Common Types

Python provides basic types you can use in hints,

```python
name: str = "Alice"           # Text, i.e. strings
count: int = 42               # Whole numbers, i.e. integers
ratio: float = 0.5            # Floating point numbers
is_active: bool = True        # True or False
```

For collections, you specify both the container and the element type,

```python
numbers: list[int] = [1, 2, 3]
names: tuple[str, str, str] = ("Alice", "Bob", "Carol")
config: dict[str, int] = {"rows": 50, "cols": 100}
```

!!! note
    In Python 3.9+, you can use `list[int]` instead of `List[int]` from the `typing` module. The built-in generic syntax is more concise and preferred.

Sometimes, it's advantageous to type hint using the [abstract base class of the built-in types](https://docs.python.org/3/library/collections.abc.html#collections-abstract-base-classes). For example, lists and tuples are [sequence types](https://docs.python.org/3/library/stdtypes.html#sequence-types-list-tuple-range) and dictionaries are [mapping types](https://docs.python.org/3/library/stdtypes.html#mapping-types-dict) which maps a [hashable value](https://docs.python.org/3/glossary.html#term-hashable) to an arbitrary object.

```python
from collections.abc import Sequence, Mapping, Hashable

numbers: Sequence[int] = [1, 2, 3]
names: Sequence[str, str, str] = ("Alice", "Bob", "Carol")
config: Mapping[Hashable, int] = {"rows": 50, "cols": 100}
```

### Optional and Union Types

What if a variable can be `None` (absent or unset)? Use [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional),

```python
def get_config_value(key: str) -> Optional[str]:
    if key in config:
        return config[key]
    return None
```

`Optional[str]` means the return value is either a `str` or `None`. If the user forgets to handle the `None` case, a type checker will warn them.

Alternatively and more explicitly in Python 3.10+,

```python
def get_config_value(key: str) -> str | None:
    ...
```

The `|` operator is [syntactic sugar for union types](https://docs.python.org/3/library/stdtypes.html#types.UnionType). It reads more naturally as "string or None".

This is also useful when a function can accept multiple types,

```python
def log(message: str | int | bool) -> None:
    print(f"[LOG] {message}")
```

This says `message` can be a string, integer, or boolean.

### Generic Types and Type Variables

Sometimes a function works with any type. For example, a function that doubles whatever it receives,

```python
from typing import TypeVar

T = TypeVar('T')

def double(x: T) -> T:
    return x * 2
```

Here, `T` is a [*type variable*](https://docs.python.org/3/library/typing.html#typing.TypeVar). It's a placeholder for any type. The function says: "whatever type you pass in, I'll return the same type." If you pass an `int`, you get an `int` back. If you pass a `float`, you get a `float` back.

This is useful for [generic containers](https://docs.python.org/3/library/typing.html#generics) like lists,

```python
def first_element(items: list[T]) -> T:
    return items[0]
```

The type of the returned element matches the type of elements in the list. If `items` is `list[str]`, you get a `str` back.

### Type Aliases

Long type hints can become unwieldy. Creating [type aliases](https://docs.python.org/3/library/typing.html#type-aliases) helps with readability,

```python
from typing import Annotated
from pydantic import Field, NonNegativeFloat

# Type alias for a proportion (0 to 1)
Proportion = Annotated[NonNegativeFloat, Field(le=1)]

def set_density(density: Proportion) -> None:
    ...
```

This is especially useful in projects, where a type such as `Proportion` appears throughout the codebase. By defining it once, it can then be easily used everywhere. If requirements change, update the definition in one place.

### Type Hints in This Project

Throughout the Game of Life project, you'll see type hints extensively:

```python title="model.py"
def compute_next_generation(self) -> NDArrayU8:
    ...
```

`NDArrayU8` is a type alias for a NumPy array of unsigned 8-bit integers. It's defined at the top of the file:

```python
NDArrayU8 = npt.NDArray[np.uint8]
```

This communicates to readers that "this function returns a NumPy array of bytes (0-255 values)." Without the type hint, it's ambiguous.

Another example,

```python title="controller.py"
def execute_game_of_life(
    game: GameOfLife,
    view: BaseView,
    num_generations: int | None,
) -> None:
    with view as opened_view:
        for _ in GoLIterator(num_generations):
            opened_view.render(game)
            game.step()
```

The hints tell you:
- `game` must be a `GameOfLife` instance
- `view` must be a `BaseView` instance (or a subclass)
- `num_generations` is either an `int` or `None`
- The function returns `None` (no value)

If you pass a `str` as `num_generations`, a type checker will catch it.

## Best Practices

### 1. Always Annotate Function Signatures

Function signatures are the contract between a function and its callers. Always include type hints for parameters and return types,

```python
# Good
def add(x: int, y: int) -> int:
    return x + y

# Avoid
def add(x, y):
    return x + y
```

### 2. Use Specific Types

Be as specific as practical. `list[str]` is better than `list`, which is better than no hint at all,

```python
# Good
def process_names(names: list[str]) -> dict[str, int]:
    ...

# Less specific
def process_names(names: list) -> dict:
    ...

# No hints
def process_names(names):
    ...
```

### 3. Use Type Aliases for Complex Types

If a type hint is long or repeated, create an alias. The Game of Life project does this,

```python
# Type alias for a grid of unsigned 8-bit integers
NDArrayU8 = npt.NDArray[np.uint8]

# Instead of repeating npt.NDArray[np.uint8] everywhere:
def compute_next_generation(self) -> NDArrayU8:
    ...

def _history(self) -> list[NDArrayU8]:
    ...
```

Define it once, use it everywhere. If you need to change the type, update the alias in one place.

### 4. Document Complex Types

If a type is not immediately clear, add a docstring,

```python
from typing import Annotated
from pydantic import Field, NonNegativeFloat
{%
  include-markdown "../src/game_of_life/config.py"
  start="from game_of_life.model import Pattern"
  end="if TYPE_CHECKING:"
%}
```

### 5. Use Type Checkers in CI/CD

Configure your type checker to run as part of your continuous integration. If code has type inconsistencies, the build fails. This is a safeguard to prevent bad code from being added to protected branches.

```yaml title="excerpt from .github/workflows/ci.yml"
{%
  include-markdown "../.github/workflows/ci.yml"
  start="uses: astral-sh/ruff-action@v3"
  end="- name: Test with pytest"
%}
```

### 6. Learn from Experience

Basic use of type hints with Python is quite easy to pick up. However, acquiring the finesse to use type hints in a way that balances flexibility, control, safety and simplicity takes time. It is with experience that you learn how best to use type hints and more importantly, how *not* to use type hints.

## Looking Ahead

Type hints are foundational for understanding the subsequent tutorials. The Game of Life project uses,

- [Pydantic models](https://pydantic.dev/docs/validation/latest/concepts/models/) with type hints for configuration validation (covered in the Controller and Bringing It Together tutorials)
- [Type variables](https://docs.python.org/3/library/typing.html#typing.TypeVar) and [annotated types](https://docs.python.org/3/library/typing.html#typing.Annotated) for flexible, constrained types (used throughout)
- [Union types](https://docs.python.org/3/library/stdtypes.html#types.UnionType) (`|`) for expressing multiple valid types (used in configuration and view selection)

Each of these relies on type hints to work correctly and provide IDE support.

## Conclusion

Type hints are an investment. The upfront cost of writing and learning them is reaped many times over as,

- Your IDE can help you more effectively
- Bugs are caught before runtime
- Code is easier to read and maintain
- Refactoring becomes safer
- Onboarding new developers is easier

In the context of research software, type hints are especially valuable. Research often involves complex data structures and transformations. Type hints make implicit assumptions explicit, improving reproducibility and reducing misunderstandings.

As you work through the subsequent tutorials, pay attention to how type hints are used. They're not just decorations, they're there to help you understand what the code more easily and provide a safety net.
