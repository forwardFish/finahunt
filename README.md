# finahunt

Agent-native scaffold for the compliance information source access system defined in `docs/03_架构/Agent 体系设计文档 v1.0 正式落地版.md`.

## Scope

This repository now includes:

- three-plane agent directories and implementations
- shared schemas, state management, checkpoint, and audit utilities
- LangGraph graph definitions for build, runtime, and governance planes
- workflow entrypoints, default rules, and smoke tests

## Quick Start

1. Create a Python 3.11+ environment.
2. Install dependencies with `pip install -e .`.
3. Run tests with `pytest`.

## Layout

The repository follows the directory structure defined in the design document:

- `agents/`
- `skills/`
- `packages/`
- `config/`
- `graphs/`
- `tests/`
- `workflows/`
- `docker/`
- `workspace/`
