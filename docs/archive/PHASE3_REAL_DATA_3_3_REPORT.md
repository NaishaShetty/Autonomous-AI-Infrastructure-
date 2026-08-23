Yes. **Phase 2 should begin with a formal Phase 1 freeze/gate**, so we don't accidentally keep changing the foundation while doing economic experiments.

Based on the completed Phase 1 report and its recommended priorities, I’d structure Phase 2 as the **Economic Strategy & Planner Foundation** phase. The key shift is: Phase 1 established *what the game is*; Phase 2 establishes *what actually makes money and wins*.



# Kaggriculture — Phase 2 Plan

## Economic Strategy, Resource Economics & Planner Foundation

### Phase 2 objective

Build a statistically validated economic understanding of Kaggriculture and use it to construct the first **economically intelligent agent**, while preserving the Phase 1 environment, harness, mechanics reference, and baseline as frozen experimental infrastructure.

The goal is **not yet to build the final super-agent**.

The goal is to answer:

> **Given the actual 720-turn simulator, what combination of crops, animals, land, labor, fertilizer, inventory management, and market timing produces the strongest robust economic strategy?**

The Phase 1 Wheat Patroller becomes our **control condition** throughout this phase.

---

# Phase 2.0 — Phase 1 Freeze & Reproducibility Gate

This should be the first task before any new economic experiment.

### Freeze the following

* Kaggriculture simulator version: `1.32.7`
* Vendored simulator source
* Official documentation captures
* Mechanics reference
* Architecture map
* Evaluation harness
* Existing Wheat Patroller baseline
* Existing Phase 1 experiment results
* Existing seed ranges/results
* Phase 1 report

The baseline should **not be silently modified** during Phase 2.

If a bug is discovered in Phase 1 infrastructure:

> Fix → rerun affected Phase 1 experiments → version the correction → refreeze.

Do not overwrite old results.

### Reproducibility checklist

Before proceeding:

* Capture complete `pip freeze`.
* Record Python/OS/environment versions.
* Verify simulator hash/version.
* Verify vendored simulator hasn't changed.
* Verify evaluation harness produces the same Phase 1 results.
* Preserve the original Phase 1 result directories.
* Tag the Phase 1 state, e.g. `phase1-frozen`.
* Record the exact baseline implementation used for Phase 1.
* Record the exact seed ranges used.
* Confirm deterministic seeded episodes remain deterministic.

### Important rule

**Phase 1 becomes the immutable control layer.**

Every Phase 2 strategy must be evaluated against the frozen Wheat Patroller under comparable conditions.

This directly protects us from accidentally improving the benchmark while changing the experimental environment.

---

# Phase 2.1 — Economic Instrumentation

Before optimizing anything, expand the evaluation harness.

Phase 1 currently gives us final money, outcome, runtime, etc. Phase 2 needs to explain **why** an agent made money.

Add episode-level telemetry for:

### Financial

* Starting money
* Final money
* Net profit
* Total market revenue
* Total purchases
* Seed expenditure
* Animal expenditure
* Land expenditure
* Farm-hand expenditure
* Fertilizer expenditure
* Wheat/feed expenditure

### Production

* Seeds purchased
* Seeds planted
* Crops harvested
* Yield by crop
* Animals purchased
* Animals successfully placed
* Animal products harvested
* Fertilizer generated
* Fertilizer consumed
* Fertilizer sold

### Land

* Land unlocked
* Day of each land purchase
* Tiles used
* Tiles idle
* Tiles occupied by crops
* Tiles occupied by animals/structures
* Weed tiles
* Productive tile-days

### Labor

* Farmer utilization
* Farm-hand count by day
* Farm-hand cost
* Actions per worker
* Productive actions
* Movement actions
* PASS actions
* Failed/no-op actions

### Market

For every sell:

* Resource
* Quantity
* Price
* Market inventory before/after where accessible

Track:

* Average realized sell price
* Base price
* Price premium/discount
* Price trajectory
* Market inventory trajectory

### Opponent

Since the opponent's farm is public:

* Opponent land
* Opponent crops
* Opponent animals
* Opponent structures
* Opponent farmer/hands
* Opponent observable production state
* Observable market activity

This telemetry is going to be extremely important later.

---

# Phase 2.2 — Production Economics Model

Now establish the economic value of every production option **without assuming market prices remain at base price**.

Start with theoretical calculations, but clearly label them as model estimates.

Evaluate:

### Crops

* Wheat
* Carrot
* Tomato
* Strawberry
* Melon

### Animals

* Goose
* Cow
* Sheep

For each calculate:

* Initial capital required
* Time to first revenue
* Total expected production
* Revenue at base price
* Revenue at realistic dynamic prices
* Feed requirements
* Fertilizer opportunity cost
* Labor requirements
* Land requirements
* Setup cost
* Payback period
* Revenue per tile-day
* Revenue per farmer action
* Revenue per worker action
* Capital efficiency

The important shift from Phase 1 is that:

> **Base market price ≠ economic value.**

The official mechanics explicitly make prices dynamic, and the Phase 1 report identified market behavior as a major unanswered strategic question. 

---

# Phase 2.3 — Crop Strategy Sweep

This should be our first major experiment block.

Test isolated crop strategies.

### Strategies

At minimum:

* Wheat-only
* Carrot-only
* Tomato-only
* Strawberry-only
* Melon-only

Then combinations:

* Wheat + Carrot
* Wheat + Tomato
* Wheat + Melon
* Wheat + Strawberry
* Wheat + Melon + Tomato
* Wheat + Melon + Strawberry
* Mixed portfolio

The exact combinations can expand based on results.

### Questions

1. Is Wheat actually optimal?
2. Is Wheat merely a good low-risk baseline?
3. Do slow high-value crops outperform it over 30 days?
4. Does the 720-turn horizon favor early-return crops?
5. Does diversification reduce variance?
6. Does a crop's nominal yield/tile/day survive dynamic pricing?
7. Does fertilizer materially change crop rankings?

### Critical experimental constraint

Don't evaluate only final money.

Measure:

**profit + variance + win rate + resource utilization.**

A strategy that makes $7,000 against a passive opponent but collapses against aggressive selling may be worse than a $6,000 strategy with much higher win probability.

---

# Phase 2.4 — Fertilizer Economics

Fertilizer deserves its own experiment because it has multiple opportunity costs.

Test:

### Fertilizer sources

* Buy fertilizer
* Animal-generated fertilizer
* No fertilizer

### Usage

* Wheat
* Carrot
* Melon
* Tomato
* Strawberry

Measure:

* Additional yield
* Additional revenue
* Fertilizer cost
* Fertilizer opportunity cost
* Additional actions
* ROI

Determine:

> **When is fertilizer worth using rather than selling it?**

Also investigate whether fertilizer should be:

* immediately consumed,
* stockpiled,
* sold,
* reserved for specific crops.

---

# Phase 2.5 — Labor / Farm-Hand Economics

This is one of the most important Phase 2 questions.

The Phase 1 report specifically identified hired-hand ROI as a priority. 

Test:

* 0 hands
* 1 hand
* 2 hands
* 3 hands
* More where economically meaningful

Across different farm sizes.

Because hiring resets every day and follows the Fibonacci cost sequence, we should determine the actual optimal hiring policy rather than assuming "more workers = more profit."

### Questions

* At what cash level is a hand profitable?
* At what number of productive tiles?
* Does one additional worker increase output enough to pay for itself?
* Does movement become the bottleneck?
* Does shed logistics become the bottleneck?
* Does labor become more valuable after land expansion?
* Is hiring only useful on particular days?

This should eventually produce a rule such as:

> Hire one hand when expected additional productive revenue exceeds daily hire cost + logistical opportunity cost.

But **the threshold must come from experiments**, not intuition.

---

# Phase 2.6 — Land Expansion Economics

Current baseline uses an arbitrary safety rule:

> Buy land only when cash ≥ 3× the next land price.

That rule should now be treated explicitly as a **placeholder**, not a validated strategy. 

Test:

### Land policies

* Never expand
* Expand immediately when affordable
* Expand at fixed days
* Expand after a cash threshold
* Expand when existing land utilization exceeds threshold
* Expand based on expected future production

For each:

* $1,000 expansion
* $2,000 expansion
* $4,000 expansion

Measure:

* Payback time
* Additional productive tile-days
* Additional revenue
* Lost capital opportunity
* Final money
* Win rate

The desired result is an **adaptive land-expansion rule**, not merely "buy land at day X."

---

# Phase 2.7 — Animal Economics

This is currently almost entirely unexplored.

Build dedicated animal baselines for:

### Goose

Evaluate:

* Setup cost
* Feed consumption
* First production
* Ongoing production
* Care bonus
* Fertilizer generation
* Harvest logistics
* Market value

### Cow

Same analysis.

### Sheep

Same analysis.

Then compare:

**animal vs crop on equivalent land and labor.**

Especially:

* Goose vs Wheat
* Cow vs Melon
* Sheep vs Strawberry
* Mixed animal/crop farms

Important:

Animals aren't just "buy animal → receive product."

They require:

* structure
* purchase
* shed pickup
* placement
* daily feeding
* potentially care
* harvesting
* fertilizer collection

Those action/logistical costs must be included.

---

# Phase 2.8 — Mixed Farm Portfolio Optimization

Once individual components are understood, combine them.

Candidate portfolios:

### Conservative

Wheat-heavy.

### Balanced

Wheat + Melon + one ongoing crop.

### High-capital

Melon/animals.

### Production machine

Multiple crops + farm hands.

### Animal-heavy

Goose/Cow/Sheep mix.

### Adaptive

Portfolio changes based on:

* Day
* Cash
* Land
* Market
* Town demand
* Opponent behavior

This is where we start moving from **strategy testing** toward an actual planner.

---

# Phase 2.9 — Market Economics

This is probably the most strategically important subsection.

The simulator explicitly uses a dynamic market where player sales, purchases, and town consumption affect market inventory/prices. 

We need to understand the market experimentally.

### First: passive-market experiments

Run agents that produce but don't sell immediately.

Compare:

* Immediate selling
* End-of-day selling
* Scheduled selling
* Threshold selling
* Price-aware selling

### Then characterize

For every major product:

* Price response to selling
* Price response to buying
* Recovery after selling
* Effect of town consumption
* Price floor behavior
* Price ceiling behavior
* Market inventory trajectory

### Crucial question

Is it better to:

**produce more and sell into the market**

or

**produce less and wait for favorable prices?**

---

# Phase 2.10 — Head-to-Head Market Interaction

This deserves its own stage rather than being mixed into normal market testing.

Phase 1 explicitly did **not** test aggressive-aggressive opponents. 

Now test:

### Same-product competition

* Wheat vs Wheat
* Melon vs Melon
* Tomato vs Tomato
* etc.

### Different-product competition

* Wheat vs Melon
* Wheat vs Animal
* Mixed vs Wheat

### Behavior

* Passive seller vs aggressive seller
* Early seller vs late seller
* Market-aware vs market-blind
* High-volume seller vs low-volume seller

Measure:

* Price destruction
* Relative profit
* Win rate
* Market recovery
* Strategic interaction.

This is where we begin optimizing for **winning**, rather than farming in isolation.

---

# Phase 2.11 — Town Demand Analysis

Town demand creates an external source of market inventory consumption.

Investigate:

* Shop unlock timing
* Duplicate shop behavior
* Product demand
* Consumption frequency
* Demand-driven price changes
* Whether producing for an upcoming demand spike is advantageous
* Whether town consumption provides predictable price-recovery opportunities

The goal is to determine whether town behavior can become a **predictable market signal**.

---

# Phase 2.12 — Build the Economic Planner v1

Only after the above experiments.

The first planner should not be ML.

It should be a deterministic economic decision system.

Conceptually:

```text
OBSERVATION
    ↓
Economic State Estimator
    ↓
Production Opportunities
    ↓
Expected ROI
    ↓
Resource Constraints
    ↓
Market Adjustment
    ↓
Opponent Adjustment
    ↓
Action Priority
    ↓
EXECUTION
```

It should reason about:

* Current cash
* Available land
* Occupied tiles
* Crops
* Animals
* Workers
* Fertilizer
* Inventory
* Market prices
* Town demand
* Day remaining
* Opponent observable state

And select between:

* Plant
* Water
* Harvest
* Fertilize
* Feed
* Care
* Buy
* Sell
* Hire
* Expand
* Move
* Wait

---

# Phase 2.13 — Economic Planner vs Wheat Patroller

Now establish whether the planner actually improves the baseline.

Minimum comparison:

**Wheat Patroller vs Economic Planner v1**

Across:

* At least 100 episodes initially
* Multiple disjoint seed ranges
* Multiple opponent types

Not just PASS.

We should introduce progressively stronger opponents.

### Report

* Win rate
* Mean final money
* Median
* Standard deviation
* Worst case
* Best case
* Profit
* Action efficiency
* Market efficiency
* Worker efficiency
* Land efficiency

The key metric remains:

> **Win probability.**

---

# Phase 2.14 — Robustness & Ablation

Once Planner v1 looks promising, determine **why** it works.

Run ablations:

* Without market awareness
* Without land planning
* Without worker planning
* Without animal planning
* Without fertilizer planning
* Without opponent awareness
* Without crop diversification
* Without price-aware selling

This tells us which components actually matter.

We don't want a giant planner containing ten complicated modules where only one actually contributes.

---

# Phase 2.15 — Phase 2 Gate

Phase 2 should **not** be considered complete merely because we have a more profitable agent.

It should pass only when we have:

### Infrastructure

* [ ] Phase 1 formally frozen.
* [ ] Reproducible environment snapshot.
* [ ] Phase 1 results preserved.
* [ ] Extended economic telemetry.
* [ ] Evaluation harness validated.

### Economic understanding

* [ ] Crop economics measured.
* [ ] Fertilizer economics measured.
* [ ] Farm-hand economics measured.
* [ ] Land economics measured.
* [ ] Animal economics measured.
* [ ] Mixed-farm economics measured.
* [ ] Market behavior characterized.
* [ ] Town-demand effects characterized.
* [ ] Head-to-head market interaction tested.

### Strategy

* [ ] Economic Planner v1 implemented.
* [ ] Planner compared against frozen Wheat Patroller.
* [ ] Multiple seeds tested.
* [ ] Multiple opponents tested.
* [ ] Variance reported.
* [ ] Ablations performed.
* [ ] No cherry-picking.
* [ ] No test-seed tuning.

### Research integrity

* [ ] Documented mechanics remain distinct from implementation observations.
* [ ] Hypotheses are explicitly labeled.
* [ ] Raw experiment data preserved.
* [ ] Every major strategy change has a hypothesis.
* [ ] Negative results documented.
* [ ] No overfitting to individual seeds.
* [ ] No use of private opponent information.

---

# The Phase 2 experiment hierarchy

I would **not** let an agent execute all of these arbitrarily. The order matters:

```text
PHASE 1 FREEZE
      ↓
Economic Telemetry
      ↓
Crop Economics
      ↓
Fertilizer Economics
      ↓
Labor Economics
      ↓
Land Economics
      ↓
Animal Economics
      ↓
Mixed Production
      ↓
Market Characterization
      ↓
Town Demand
      ↓
Head-to-Head Market
      ↓
Economic Planner v1
      ↓
Ablation
      ↓
Robustness
      ↓
PHASE 2 GATE
```

### One thing I'd emphasize

**Don't start Phase 2 by writing the planner.**

Start by making the simulator tell us *where the money is*.

The Phase 1 Wheat Patroller's ~$5.1k–$5.4k final bank gives us a useful control, but we currently don't know whether its advantage comes from wheat economics, low complexity, low capital risk, market behavior, or simply the fact that it is substantially better than the weak built-ins. Phase 2's job is to decompose that.

The biggest strategic questions from Phase 1 are therefore exactly the ones I'd attack first: **parallel production, hired-hand ROI, animals, land timing, and genuine head-to-head market interaction.** 

And I would make **Phase 2.0 — Freeze Phase 1** mandatory, not optional. That gives us a clean scientific boundary:

> **Phase 1 = frozen environment/control foundation.**
> **Phase 2 = economic discovery.**
> **Phase 3 = strategy/planner sophistication based on validated economics.**

That keeps us from turning the competition into a giant pile of undocumented tweaks.
