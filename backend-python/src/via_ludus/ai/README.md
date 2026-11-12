# Writing Your Own Agent

This directory is where student agents live. An **agent** is a Python class that plays Via Ludus: it is given the current board and the color it is playing, and it decides which cell to claim. The game takes care of everything else: turns, rules, detecting a winner, the browser app and tournaments.

If you have not read the rules yet, start with the root [README.md](../../../../README.md#the-game).

**Contents**

- [Before You Start](#before-you-start)
- [Step 1: Choose A Base Class](#step-1-choose-a-base-class)
- [Step 2: Write the Agent](#step-2-write-the-agent)
  - [Option A: Extend `Agent`](#option-a-extend-agent)
  - [Option B: Extend `ScoringAgent`](#option-b-extend-scoringagent)
- [Step 3: Register the Agent](#step-3-register-the-agent)
- [Step 4: Test Your Agent](#step-4-test-your-agent)
- [Step 5: Play Against it in the Browser](#step-5-play-against-it-in-the-browser)
- [What Your Agent Receives](#what-your-agent-receives)
- [Rules Your Agent Must Follow](#rules-your-agent-must-follow)
- [Troubleshooting](#troubleshooting)
- [Examples to Study](#examples-to-study)

## Before You Start

1. Set up the backend (Python 3.11+, a virtual environment, and `pip install -e ".[web-service,graph-agents]"`). See the [`README.md`](../../../README.md#setup) in [`backend-python/`](../../../).
2. Make sure you can run the game. See the [`README.md`](../../../../scripts/README.md) in [`scripts/`](../../../../scripts/).
3. Skim the built-in agents in [`backend-python/src/via_ludus/ai/via_ludus_agents/`](./via_ludus_agents/). Reading [`random_agent.py`](./via_ludus_agents/random_agent.py) and [`shortest_path_agent.py`](./via_ludus_agents/shortest_path_agent.py) takes five minutes and shows you the shape of an agent.

