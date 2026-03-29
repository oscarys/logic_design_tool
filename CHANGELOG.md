# Changelog

All notable changes to this project will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.0.0] — 2025

### Added
- **Combinational Design tab** — truth table editor with don't-care support,
  bus grouping/ungrouping, VHDL-2008 generation
- **Sequential Design tab (Moore ASM)** — visual ASM chart canvas with
  StateItem, DiamondItem, HexagonItem, UnconditionalItem blocks
- **Owned condition model** — each state owns its condition block;
  blocks snap below state, move with it, cannot be detached
- **VHDL-2008 generator** — three concurrent `when-else` statements,
  no processes; failsafe `current_state` default in next-state logic
- **ASM validator** — error and warning messages before generation
- **Signal manager** — scalar and bus signals, group/ungroup for combinational
- **Project save / load** — `.vhdlt` JSON format, dirty tracking,
  "Save before closing?" guard
- **FSM Simulation** — step / run / pause / reset, adjustable speed,
  per-input controls, amber glow ring on current state
- **Live timing diagram** — logic-analyzer style waveform updates in real time
- **Timing diagram PNG export**
- **Dark mode** — instant toggle, persisted via QSettings
- **License** — GNU General Public License v3.0
