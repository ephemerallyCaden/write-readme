<!-- TinySim README, before: no skill

  Generated 2026-10-28 by Claude Code with:
    claude -p --bare "Write a README.md for this project."
  run on a clean clone of github.com/ephemerallyCaden/TinySim at 7cafb75,
  with no media, no rules and no skill. The original 2-line README was
  overwritten.

  Everything below this comment is the unedited output. Line numbers
  quoted in assets/readme-before-after.png count from the line after it.
-->
# TinySim

A 2D artificial-life sandbox built in Unity. A population of small creatures ("agents") lives on a procedurally generated world. They search for food, avoid poison, mate, and can hunt each other. Each agent is controlled by a neural network that evolves over time through **real-time NEAT** (NeuroEvolution of Augmenting Topologies). There is no fitness function and there are no generations: an agent that survives long enough to reproduce passes on its genes, and new species branch off as populations drift apart.

## Features

- **Evolving brains.** Each agent has a NEAT genome. Mutations perturb weights, add or disable connections, insert hidden nodes, prune nodes, and swap activation functions (Sigmoid, Tanh, ReLU, Leaky ReLU, Linear). Innovation numbers are tracked globally so crossover lines up matching genes.
- **Evolving bodies.** Physical traits are inherited and mutated alongside the brain: size, speed, vision distance and angle, diet preference (herbivore ↔ carnivore), attack damage, reproduction cooldown and cost, and each agent's own mutation rate and magnitude.
- **Speciation.** Agents are grouped by NEAT compatibility distance (excess, disjoint, and weight terms), with an added term for physical-trait differences. Species split (cladogenesis), drift into successor species over time (anagenesis), go extinct, and get procedurally generated names that keep their ancestor's prefix.
- **Environment.**
  - A Perlin-noise temperature map. Warm regions are fertile, cold regions are harsh.
  - Plant food, which is scarcer and less nutritious in the cold.
  - Poison, which spawns in cold zones.
  - Meat, which is dropped when an agent dies and decays quickly.
- **Optional predation.** Agents can evolve to attack nearby creatures. Each attack costs the attacker energy.
- **Metabolism.** Energy use scales with speed, size², brain complexity, movement, and turning. Agents age, starve, and die.
- **World creation screen.** Before a run, you can set the seed, world size, temperature shape, population and food limits, spawn pattern (Central / Clusters / Random), predation, and the starting range for every agent trait. A live preview of the temperature map updates as you edit.
- **Analytics and inspection.**
  - Click any agent to see its stats, its vision and interaction-range overlays, and a live diagram of its neural network.
  - The analytics panel has a population graph, attribute-over-time graphs, a phylogenetic tree, and per-species details with ancestry and a model preview.
- **Performance work.** The hot paths avoid allocation, and rendering uses GPU instancing. See [`OPTIMISATIONS.md`](OPTIMISATIONS.md).

## Requirements

- **Unity 6 — `6000.0.74f1`** (see `ProjectSettings/ProjectVersion.txt`). Other Unity 6 patch versions will probably work, but they haven't been tested.
- Packages are resolved automatically from `Packages/manifest.json`. The main ones are 2D Tilemap, TextMesh Pro, and uGUI.

## Getting Started

1. Clone the repository.
2. Open the project folder in Unity Hub with the editor version above.
3. Open `Assets/Scenes/WorldCreation.unity` and press **Play**.
4. Adjust the world settings and press **Start**. This loads the `Main` scene and starts the simulation.

You can also open `Assets/Scenes/Main.unity` and play it directly. It will use whatever values are currently in `Assets/SimulationConfig.asset`.

To make a standalone build, both scenes are already in Build Settings, with `WorldCreation` first.

## Controls

| Input | Action |
|---|---|
| `W` `A` `S` `D` / arrow keys | Pan camera |
| Right- or middle-mouse drag | Pan camera |
| Scroll wheel, `+` / `-` | Zoom |
| Left click | Select an agent (click empty space to deselect) |
| `P` | Pause / resume |
| `]` / `[` | Speed up / slow down (1×–20×), or use the on-screen slider |
| `Tab` | Toggle analytics panel |
| `1` / `2` / `3` | Analytics tabs: Overview / Attributes / Species |

## How It Works

Each fixed-timestep tick, `SimulationManager` advances world time by `fixedDeltaTime × simulationSpeed`. It then updates all agents and the food spawner.

On every tick, each agent does the following:

1. **Senses.** It finds the nearest agent, plant, meat, and poison inside its vision cone.
2. **Thinks.** It builds 22 normalised inputs and feeds them through its network.
3. **Acts.** It applies the 4 outputs: moving, turning, eating, mating, and attacking.

**Inputs:** Control (bias), Health, Age, Hunger, Temperature, See Agent, Agent Proximity, Agent Angle, Agent Health, Agent Energy, Agent Size, Same Species, See Food, Food Proximity, Food Angle, See Meat, Meat Proximity, Meat Angle, See Poison, Poison Proximity, Poison Angle, Desire.

**Outputs:** Move, Turn, Desire (fed back as an input next tick), Attack.

**Reproduction.** Two agents can mate if both are fertile (cooldown expired and enough energy) and close enough to each other. The child's genome comes from crossing over both parents' genomes, and its attributes are inherited and then mutated. The child is assigned to a compatible species, or founds a new one. Each additional offspring makes future reproduction more expensive.

**Diet.** `dietPreference` runs from 0 (herbivore) to 1 (carnivore). It sets how much energy an agent gets from plants (`1 − diet`) and from meat (`diet`). An agent won't eat a food type when its efficiency for that type is below `dietEfficiencyThreshold`. Poison is always eaten on contact and drains both energy and health.

## Configuration

Every tunable parameter is stored in a single ScriptableObject, **`Assets/SimulationConfig.asset`**, defined in `Assets/Scripts/Core/SimulationConfig.cs`. You can edit it in the Inspector. Its sections are World, Temperature, Spawn, Population, Metabolism, Health & Aging, Reproduction, Mutation, Attribute Clamps, Initial Agent Ranges, Food, Poison, Meat, Predation, and Speciation.

To create additional presets, use **Assets → Create → TinySim → Simulation Config** and assign the new asset to the `SimulationManager` in `Main.unity`.

> **Note:** The World Creation screen writes directly into the assigned `SimulationConfig` asset. In the Editor, those changes persist after you exit Play mode and will appear as modifications to `SimulationConfig.asset` in version control. Revert the file if you didn't mean to change the defaults.

A `seed` of `-1` picks a random seed. Any other value seeds the shared `SimRandom` generator, which drives world generation and simulation randomness.

## Project Structure

```
Assets/
├── Scenes/            WorldCreation (setup UI) and Main (simulation)
├── Scripts/
│   ├── Agents/        Agent behaviour, attributes, spawning, manager, instanced renderer
│   ├── Camera/        Pan/zoom camera controller
│   ├── Core/          SimulationManager, SimulationConfig, SimRandom, SimEvents, species naming, diagnostics
│   ├── Environment/   Food, meat, poison, and the food spawner
│   ├── Evolution/     Crossover, mutation, innovation tracking, reproduction, speciation, species history
│   ├── Generation/    World setup and temperature map (plus an unused tilemap terrain generator)
│   ├── NeuralNetworks/ Genome, network evaluation, activation functions, node labels
│   ├── UI/            Stats panels, graphs, phylogeny, NN visualiser, overlays, world creation UI
│   └── Utility/       Agent selection, component cache, instanced rendering, drawing helpers
├── Prefabs/           Agent, food variants, NN visualiser nodes/connections, UI widgets
├── Shaders/           Unlit instanced agent shader, tilemap shader
├── Materials/, Sprites/, Tilemap/, Palettes/
└── SimulationConfig.asset
```

`SimEvents` is a static event bus (agent born/died, food consumed, species created/extinct). The UI and analytics subscribe to it, so they stay decoupled from the simulation.

## References

- Stanley, K. O. & Miikkulainen, R. (2002). *Evolving Neural Networks through Augmenting Topologies.* Evolutionary Computation, 10(2).
- Stanley, K. O., Bryant, B. D. & Miikkulainen, R. (2005). *Real-Time Neuroevolution in the NERO Video Game.* IEEE Transactions on Evolutionary Computation, 9(6).
