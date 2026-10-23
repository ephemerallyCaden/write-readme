<!-- write-readme session transcript

  Detected: Game (Unity project structure, Physics2D, scene files)
  Note: Auto-detected as Game due to Unity engine, but this is a
  simulation with no player agency. User corrected type.

  Solo project: yes (1 contributor, 3 stars)

  > This looks like both a Game and an ML project. Which is its
  > primary identity?
  It's a simulation — there's no player, no win state. Agents evolve autonomously.

  Options:
    License:       [Skip]
    Contributing:  [Skip — solo project]
    Verbosity:     [Standard]
    Screenshots:   [Add later — Unity project, can't capture headlessly]

-->

# TinySim

![Unity](https://img.shields.io/badge/Unity-6000.0.74f1-black?logo=unity)
![C#](https://img.shields.io/badge/C%23-239120?logo=csharp&logoColor=white)

A 2D ecosystem simulator where neural-network-driven agents evolve through the NEAT algorithm. Agents forage, hunt, reproduce, and speciate — governed by natural selection. Watch species emerge, compete, and go extinct in real time.

<!-- screenshot:hero | type=game | description=Simulation running with agents, food, terrain visible and neural network visualiser open | priority=MUST | format=gif -->

## Getting Started

Requires [Unity 6](https://unity.com/releases/editor/archive) (version 6000.0.74f1 or compatible).

1. Clone the repository
2. Open in Unity Hub
3. Open `Assets/Scenes/WorldCreation.unity` to configure parameters, or `Assets/Scenes/Main.unity` for defaults
4. Press Play

## Features

- **NEAT Neural Networks** -- Evolving topology networks with 22 sensory inputs and 4 behavioral outputs
- **Speciation** -- Compatibility distance calculation with excess, disjoint, and weight coefficients; anagenesis detection for genetic drift
- **Predator-Prey Dynamics** -- Herbivore-to-carnivore diet spectrum, attack mechanics, meat drops, poison hazards
- **Procedural World** -- Perlin noise temperature maps with biome-influenced food spawning
- **11 Heritable Traits** -- Size, speed, vision range/angle, diet preference, attack damage, mutation rate modifiers
- **Visualisation** -- Real-time neural network visualiser, phylogenetic tree, population graphs, species detail panels, ancestry views
- **World Creation UI** -- Configurable parameters with range sliders and temperature map preview

## How It Works

Agents sense their environment through 22 inputs (internal state, nearest agent properties, food/poison/meat proximity) and produce 4 outputs (movement speed, turning rate, reproduction desire, attack intent). Offspring inherit a crossover of both parents' NEAT genomes and physical attributes, subject to mutation. Species form automatically via NEAT compatibility distance.

## Project Structure

```
Assets/Scripts/
├── Agents/          # Behaviour, attributes, lifecycle, rendering
├── Core/            # SimulationManager, config, events, RNG
├── Environment/     # Food types, spawning, rendering
├── Evolution/       # Crossover, mutation, speciation, reproduction
├── Generation/      # World, terrain, temperature maps
├── NeuralNetworks/  # Genome, network, activation functions
├── UI/              # Stats, graphs, visualisers
└── Utility/         # Instanced rendering, caching, math
```

See [OPTIMISATIONS.md](OPTIMISATIONS.md) for performance engineering notes.

## References

Stanley, K. O., & Miikkulainen, R. (2002). Evolving Neural Networks through Augmenting Topologies. *Evolutionary Computation*, 10(2), 99-127.

## License

All rights reserved.
