# Model-View-Controller Architecture

The Model-View-Controller (MVC) architecture is a widely used ways to organize code. You'll find it in web applications, desktop software and mobile apps. It's a well-established pattern because it has proven its effectiveness,  it separates concerns so different parts of your code can be understood, modified, and extended independently.

This principle is just as valuable in research software. When you write code to solve a real problem, whether simulating Conway's Game of Life or analyzing experimental data, you quickly run into a challenge: different parts of your code are responsible for fundamentally different things. Your simulation logic shouldn't know or care whether results are being printed to a terminal, saved to a file, or displayed as an interactive plot. Equally, your user interface shouldn't need to understand the underlying mathematical rules. Yet, these pieces must still communicate and work together.

MVC is a time-tested way to strike that balance. It's not a rigid rulebook. Instead, it's a principle for thinking about how to structure larger projects, keeping the simulation, display, and user interaction cleanly separated while remaining well-coordinated. This page walks through MVC at a high level, focusing on why it matters for research software. Later tutorials dive into how each part works in practice.
