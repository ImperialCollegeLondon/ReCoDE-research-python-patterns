# Type Hinting

**Estimated read time:** 16 minutes

Python is a [dynamically typed language](https://www.baeldung.com/cs/statically-vs-dynamically-typed-languages), so variables can hold any type of data and their type can change at runtime. Python uses [duck typing](https://en.wikipedia.org/wiki/Duck_typing), which means it cares about what objects can *do* rather than what they *are*. This provides remarkable flexibility, but results in implicit assumptions scattered throughout the code: you might pass a string to a function that expects a number, or forget what type a variable contains. Then, at runtime, things break &ndash; or fail silently.

[Type hinting](https://docs.python.org/3/library/typing.html) is a way to make these implicit assumptions explicit. It enables documentation and verification of the types in your code without sacrificing Python's flexibility. It answers the question of "what type is this supposed to be?" Though it is worth noting that a type mismatch does not necessarily mean something will go wrong. Depending on the situation, things may still work fine (for example, passing a number-like object to a function expecting an `int`), fail in an obvious and immediate way, or fail silently in a way that is difficult to diagnose.

Type hints are not enforced by Python itself. They are [metadata](https://en.wikipedia.org/wiki/Metadata). These annotation tell developers and tools what types are expected. This might sound optional, but in practice, type hints have become essential for writing maintainable research software. See [PEP 484](https://peps.python.org/pep-0484/) for the full specification.

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
    Type hints are for tools and humans, _not_ for the Python interpreter itself.

### Variable Type Hints

Variables can be annotated when they are assigned to using this syntax:

```python
name: str = "game of life"
count: int = 42
ratio: float = 0.5
is_active: bool = True
```

!!! note
    [A type checker](#type-checkers) is a tool which analyses the code to verify that the types match. These tools are also able to infer what these types are without making it explicit like in the code snippet above. For instance, the type checker will know from `#!py is_active = True` that `is_active` is a boolean.

    In this project, I have opted to make all of the types explicit.

The type annotation comes after the variable name, before the value. This tells anyone reading the code (or your IDE) what type the variable should hold.

## Why Type Hints Matter

### 1. IDE Support

When your IDE knows the type of a variable, it can help you immensely. Consider the case where you are writing code and have so far written the following:

```python
game = create_game_of_life(config)
game.
```

When you type `game.` and pause, your IDE doesn't know what properties or methods `game` has. It can't autocomplete. Now with type hints,

```python
def create_game_of_life(config: GameOfLifeConfigFrom) -> GameOfLife: # (1)
    return GameOfLife(config.num_rows, config.num_cols, grid_creator=...)

game: GameOfLife = create_game_of_life(config)
game.
```

1. The `-> GameOfLife` syntax is a type hint that specifies the return type rather than being part of the function.

Your IDE knows `game` is a `GameOfLife` object. It is able to determine this implicitly through the `-> GameOfLife` return type hint and the explicitly with the `game: GameOfLife`. Thus, your IDE can autocomplete and show you all available methods and properties: `game.step()`, `game.grid`, `game.generation`, `game.compute_next_generation()`, etc. This saves time and prevents typos.

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
def double(value: float) -> float:
    return value * 2

result: float = double("hello")  # Type checker warns: expected float, got str
```

The type checker warns you that the return type of `double` is `float`, not `str`. This catches the mismatch before the code runs.

When the Python interpreter runs this, it does not fail and it returns a valid string. If this is used in a divide operation further down in the code, it will fail there instead

```python
>>> result: float = double("hello")
>>> result
'hellohello'
>>> result/2
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: unsupported operand type(s) for /: 'str' and 'int'
```

This can make debugging particularly tricky, as the source of the bug is far removed from where it manifests.

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
    def process_data(self) -> dict[str, int]:
        ...

def process(obj: DataProcessor) -> dict[str, int]:
    return obj.process_data()
```

This makes the contract clear. `process` expects something of type `DataProcessor` (or a subclass). Your IDE can autocomplete. Type checkers can verify calls at development time.

!!! warning
    The crucial limitation is that type hints are not enforced by Python at runtime. This means that `process("hello string")` can still be invoked and Python will try to execute it. As `"hello string"` doesn't have a `process_data()` method, though, you'll get an `AttributeError` at runtime, type hints notwithstanding.

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

As mentioned, type hints alone don't enforce anything. A type checker is a necessary tool that analyzes your code and reports type mismatches. The three main type checkers for Python are,

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

Sometimes, it's advantageous to type hint using the [abstract base class of the built-in types](https://docs.python.org/3/library/collections.abc.html#collections-abstract-base-classes). For example, lists and tuples are [sequence types](https://docs.python.org/3/library/stdtypes.html#sequence-types-list-tuple-range) and dictionaries are [mapping types](https://docs.python.org/3/library/stdtypes.html#mapping-types-dict) which maps a [hashable value](https://docs.python.org/3/glossary.html#term-hashable) to an arbitrary object.

```python
from collections.abc import Sequence, Mapping, Hashable

numbers: Sequence[int] = [1, 2, 3]
names: Sequence[str, str, str] = ("Alice", "Bob", "Carol")
config: Mapping[Hashable, int] = {"rows": 50, "cols": 100}
```

`Mapping` is mainly useful when working with third party libraries.
In most Python code that only uses the standard library, mapping types are usually a child class of `dict`, e.g. [`defaultdict`](https://docs.python.org/3/library/collections.html#collections.defaultdict).

??? info "A short detour into `defaultdict` as it's fantastic"
    [`defaultdict`](https://docs.python.org/3/library/collections.html#collections.defaultdict) is a sub-class of the built in `dict` class. It very useful collection which initializes a key the first time it is accessed, rather than raising a `KeyError`. The default value is determined by a callable passed at instantiation. An example use case of this would be to group items by a key,

    ```python
    >>> from collections import defaultdict
    >>>
    >>> students = [("Alice", "A"), ("Bob", "B"), ("Carol", "A"), ("Diana", "B"), ("Eve", "A")]
    >>>
    >>> grade_groups = defaultdict(list)
    >>> for name, grade in students:
    ...     grade_groups[grade].append(name)
    ...
    >>> dict(grade_groups)
    {'A': ['Alice', 'Carol', 'Eve'], 'B': ['Bob', 'Diana']}
    ```

    It can also be used for counting occurrences, for example,

    ```python
    >>> words = ["potato", "tomato", "avocado", "tomato", "potato"]
    >>> word_counts = defaultdict(int)
    >>> for word in words:
    ...     word_counts[word] += 1
    ...
    >>> dict(word_counts)
    {'potato': 2, 'tomato': 2, 'avocado': 1}
    ```

### Optional and Union Types

What if a variable can be `None` (absent or unset)? This is where the [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional) type hint comes in,

```python
def get_config_value(key: str) -> Optional[str]:
    if key in config:
        return config[key]
    return None
```

`Optional[str]` means the return value is either a `str` or `None`. If the user forgets to handle the `None` case, a type checker will warn them.

The `|` operator is [syntactic sugar for union types](https://docs.python.org/3/library/stdtypes.html#types.UnionType). It reads more naturally as "string or None".

```python
def get_config_value(key: str) -> str | None:
    ...
```

This is also useful when a function can accept multiple types,

```python
def log(message: str | int | bool) -> None:
    print(f"[LOG] {message}")
```

This says `message` can be a string, integer, or boolean.

### Advanced: Generic Types and Type Variables

Sometimes a function works with any type. For example, a function that doubles whatever it receives,

```python
from typing import TypeVar

T = TypeVar('T')

def double(x: T) -> T:
    return x * 2
```

Here, `T` is a [*type variable*](https://docs.python.org/3/library/typing.html#typing.TypeVar). It's a placeholder for any type. The function says: "whatever type you pass in, I'll return the same type." If you pass an `int`, you get an `int` back. If you pass a `float`, you get a `float` back.

???+ info "Info: Advanced `TypeVar` usage"
    If we want to ensure that this only applies to numbers to avoid our [earlier bug where a string was passed into the `double()` function](#3-catching-bugs-early), we can [constrain `TypeVar`](https://docs.python.org/3/library/typing.html#typing.TypeVar). One way to achieve it is by [placing a bound](https://typing.python.org/en/latest/spec/generics.html#type-variables-with-an-upper-bound) so that it must be a subtype of the bound.

    ```python
    from numbers import Number # (1)
    T = TypeVar("T", bound=Number)
    ```

    1. [`number.Number`](https://docs.python.org/3.10/library/numbers.html#numbers.Number) is the parent class of all numbers in Python

    In this example, it places a bound such that `T` must be a subtype of [`number.Number`](https://docs.python.org/3.10/library/numbers.html#numbers.Number) which is at the root of the numeric hierarchy in Python. Thus, an `int`, `float` or `complex` would work.

    Alternatively, we could explicitly restrict `T` to be exactly those types with,

    ```python
    T = TypeVar("T", int, float, complex)
    ```

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
Proportion = Annotated[NonNegativeFloat, Field(le=1)] # (1)

def set_density(density: Proportion) -> None:
    ...
```

1. This reads as `Proportion` is an alias for a non-negative float that is less than or equal to 1

This is especially useful in projects, where a type such as `Proportion` appears throughout the codebase. By defining it once, it can then be easily used everywhere. If requirements change, update the definition in one place.

### Type Hints in This Project

Throughout the Game of Life project, you'll see type hints extensively:

```python title="model.py"
def compute_next_generation(self) -> NDArrayU8:
    ...
```

`NDArrayU8` is a type alias for a NumPy array of unsigned 8-bit integers. It's defined at the top of the file:

```python
import numpy.typing as npt

NDArrayU8 = npt.NDArray[np.uint8]
```

When used to annotate a value returned by a function, this communicates to readers that "this function returns a NumPy array of bytes (0-255 values)." Without the type hint, it would be ambiguous.

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

If a type hint is long and repeated, create an alias. The Game of Life project does this,

```python
import numpy.typing as npt

# Type alias for a grid of unsigned 8-bit integers
NDArrayU8 = npt.NDArray[np.uint8]

# Instead of repeating npt.NDArray[np.uint8] everywhere:
def compute_next_generation(self) -> NDArrayU8:
    ...

def _history(self) -> list[NDArrayU8]:
    ...
```

Similar to variables, we can define it once, use it everywhere. If you need to change the type, update the alias in one place.

### 4. Use Type Alias to Improve Readability

Type aliases can be used to improve readability by conveying the intent of it rather than just the type. For example,

```python
from typing import TypeAlias

Name: TypeAlias = str

def greet(name: Name) -> None:
    print(f"Hello, {name}!")
```

When the complexity increases, the effect is more pronounced. Consider the case where we have a set of students and each student takes multiple subjects. To store all of their examination results, we would need a nested dictionary, i.e. `dict[str, dict[str, int]]`. The outer dictionary would have a key that corresponds to their name, while the key is a dictionary of the name of the subject and score.

If `dict[str, dict[str, int]]` is scattered throughout the code base, it isn't particularly useful as it doesn't tell you any additional information. If we introduce type aliases as such,

```python
Subject: TypeAlias = str
Score: TypeAlias = int
StudentName: TypeAlias = str

SubjectScores: TypeAlias = dict[Subject, Score]
StudentResults: TypeAlias = dict[StudentName, SubjectScores]
```

It will be much easier to conceptualize what is in `StudentResults` or `dict[StudentName, SubjectScores]`. This helps to reduce the [cognitive load](https://en.wikipedia.org/wiki/Cognitive_load) of understanding the code base making debugging or navigating it easier.

### 5. Document Complex Types

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

### 6. Use Type Checkers in CI

Configure your type checker to run as part of your continuous integration. If code has type inconsistencies, the build fails. This is a safeguard to prevent bad code from being added to protected branches.

```yaml title="excerpt from .github/workflows/ci.yml"
{%
  include-markdown "../.github/workflows/ci.yml"
  start="uses: astral-sh/ruff-action@v3"
  end="- name: Test with pytest"
%}
```

### 7. Learn from Experience

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
