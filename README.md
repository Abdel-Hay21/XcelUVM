<div align="center">

<img width="1092" height="1114" alt="Logo" src="https://github.com/user-attachments/assets/ce583188-cfcd-42bc-bbeb-4dbb42fbe588" />

# XcelUVM

**AI-Powered UVM Testbench Generator**

*From RTL to a complete, cycle-accurate UVM verification environment — in seconds.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyQt5](https://img.shields.io/badge/PyQt5-GUI-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://pypi.org/project/PyQt5/)
[![SystemVerilog](https://img.shields.io/badge/SystemVerilog-UVM-8A2BE2?style=for-the-badge)](https://www.systemverilog.io/)
[![Tcl](https://img.shields.io/badge/Tcl-Code%20Engine-E4A82D?style=for-the-badge)](https://www.tcl.tk/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

</div>

---

## Overview

**XcelUVM** is a desktop application that automates the creation of complete, production-ready **UVM (Universal Verification Methodology)** testbenches directly from your RTL design. It combines a modern **PyQt5 GUI** with an intelligent **Tcl code-generation engine** and an optional **AI layer** (powered by your choice of LLM) to deliver a cycle-accurate, standards-compliant verification environment with minimal manual effort.

> Built for hardware verification engineers, EDA students, and VLSI teams who want to spend less time writing boilerplate UVM code and more time actually verifying their designs.

---

## ✨ Key Features

### 🖥️ Modern Desktop GUI
- Dark-themed, **animated PyQt5 interface** with smooth page transitions, hero warp effects, and a cinematic AI overlay
- Intuitive **multi-step wizard** (7 configurable steps) that guides you through the full project setup
- **Step progress bar** with visual state tracking and animated step indicators
- Non-blocking, **background-threaded** code generation — the UI stays responsive at all times
- Real-time **log output panel** showing generation progress line by line

---

### 📐 Reference Model Modes

XcelUVM supports two distinct verification architectures, selectable via animated card UI:

| Mode | Description |
|------|-------------|
| **Software Reference (SB)** | Use a behavioral model written in **SystemVerilog**, **C/C++**, or **Python** as the golden reference. The Scoreboard compares DUT output against the model every clock cycle. |
| **RTL Reference (RTL)** | Instantiate a **second RTL module** (golden model) alongside the DUT. The Scoreboard compares both modules port-by-port, cycle-by-cycle. |

---

### 🤖 AI-Assisted Code Completion

After generating the structural skeleton, XcelUVM launches a **cinematic AI generation phase** powered by any major LLM:

#### Supported LLM Providers

| Provider | Example Models | Key Format |
|----------|---------------|------------|
| 🟦 Google Gemini | `gemini-2.5-flash`, `gemini-2.5-pro` | `AIza...` |
| 🟩 OpenAI | `gpt-4o`, `gpt-4.1`, `gpt-5` | `sk-...` |
| 🟧 Anthropic Claude | `claude-3-5-sonnet-20241022`, `claude-opus-4` | `sk-ant-...` |
| 🌐 OpenRouter | Any model (meta-llama, mistral, etc.) | `sk-or-...` |

> **Custom model support:** Type any model ID manually — the API call is routed automatically based on the key prefix.

#### AI-Generated Artifacts

- **`*_assertions.sv`** — cycle-accurate SVA properties covering every output signal, derived from the RTL
- **`*_coverage.sv`** — functional covergroup with bins, transition arcs, and cross coverage
- **`*_reference_model.sv / .c / .py`** — behavioral golden model that mirrors the RTL FSM cycle-exactly
- **`*_sequence_item.sv`** — randomized sequence item with protocol-aware constraints

#### RAG Prompt Architecture

Every AI call is constructed with a structured **5-section prompt**:

| Section | Content |
|---------|---------|
| **Section 0** | Tool Architecture — mandatory cycle-by-cycle facts |
| **Section 1** | Style & Format Reference — UVM coding conventions |
| **Section 2** | Project Context — your RTL + generated interface files |
| **Section 3** | Target Skeleton — the file the AI must fill |
| **Section 4** | User Instructions + 8–10 Task-Specific Critical Rules |

Each task (`assertions`, `coverage`, `random_constraints`, `reference_model_sv/c/py`) has its own verified ruleset that prevents common LLM verification mistakes: dead code, missing output assignments, wrong SVA implication operators, incorrect clock divider handling, and more.

---

### 🔧 Full UVM Component Generation

XcelUVM generates every layer of a standard UVM testbench:

```
<project_name>_uvm/
├── rtl/                              ← Your RTL files (auto-copied)
├── verif/
│   ├── agent/
│   │   ├── <proj>_seq_item.sv        ← Sequence Item (rand fields + constraints)
│   │   ├── <proj>_sequencer.sv       ← Sequencer
│   │   ├── <proj>_driver.sv          ← Driver (cycle-by-cycle)
│   │   ├── <proj>_monitor.sv         ← Monitor (captures ALL signals every cycle)
│   │   └── <proj>_agent.sv           ← Agent wrapper
│   ├── environment/
│   │   ├── <proj>_environment.sv     ← Environment (top-level env)
│   │   ├── <proj>_scoreboard.sv      ← Scoreboard (DUT vs Reference comparison)
│   │   ├── <proj>_predictor.sv       ← Predictor (routes items to reference model)
│   │   ├── <proj>_coverage.sv        ← Coverage Collector (AI-filled covergroup)
│   │   ├── <proj>_sequence.sv        ← Base + named sequences
│   │   └── <proj>_virtual_sequencer.sv
│   ├── reference_model/
│   │   └── <proj>_reference_model.sv / .c / .py
│   └── assertions/
│       ├── <proj>_assertions.sv      ← SVA bind module (AI-filled)
│       └── <proj>_bind.sv
├── test/
│   ├── <proj>_test.sv                ← UVM Test class
│   └── <proj>_config_obj.sv          ← Config Object
├── top/
│   └── <proj>_top.sv                 ← Simulation top (DUT + Interface)
├── <proj>_interface.sv               ← SystemVerilog Interface
├── run.do                            ← QuestaSim/ModelSim run script
├── wave.do                           ← Waveform setup script
└── doc/
    └── <proj>_uvm.pdf                ← Architecture reference PDF
```

---

### 🧩 Agent Topology Options

| Topology | Description |
|----------|-------------|
| **Single Agent** | One active agent (driver + monitor + sequencer) — ideal for single-interface DUTs |
| **Multi-Agent** | Configurable number of **active agents** (driver+monitor) and **passive agents** (monitor-only) — for complex SoCs, multi-channel designs, and bus protocols |

Each agent in multi-agent mode gets its own named interface, independently configured port list, and optional clock signal.

---

### 📋 Port Configuration

- **Automatic RTL Parsing:** Point XcelUVM to your `.sv` / `.v` files and it automatically parses all top-level module ports — including bit-widths, directions, parameterized types, and custom `typedef` widths.
- **Manual Port Entry:** Add, remove, or modify ports through an interactive port editor.
- **Drag & Drop file ordering** — the first file is automatically marked as the top module.
- **Per-agent port assignment** in multi-agent mode — each interface gets its own input/output port list.
- **Clock signal detection** — specify which port is the clock per interface.

---

### 🧪 Test Sequences

- Define **named UVM sequences** with configurable transaction counts directly from the GUI
- Built-in: `RESET` sequence + any number of custom sequences (e.g., `Corner_Cases`, `Stress_Test`)
- All sequences automatically wired into the **Virtual Sequencer** and **UVM Test** class
- The generated test class iterates through all sequences in order

---

### ⚙️ Optional Verification Features

Toggle each feature independently from the Options step:

| Feature | What Gets Generated |
|---------|-------------------|
| ✅ **Assertions** | A full SVA bind module. AI fills in cycle-accurate properties for every output signal. |
| ✅ **Functional Coverage** | A covergroup inside the coverage collector. AI fills bins, transitions, and cross coverage. |
| ✅ **Code Coverage** | Enables code coverage flags in the simulation run script (`run.do`). |

---

### 📄 Auto-Generated Documentation

An **architecture PDF guide** is automatically copied into the `doc/` folder, matched to your configuration:
- **Single-Agent vs Multi-Agent**
- **SB (Software Reference) vs RTL (RTL Reference)**
- **With or without** Assertions / Coverage

---

### 🌊 Waveform Setup

Auto-generates a **`wave.do`** QuestaSim/ModelSim script that adds all interface signals to the waveform viewer on launch — no manual signal hunting required.

---

### 💾 Session Persistence

- All project settings are written to a `run.tcl` configuration file.
- Re-opening XcelUVM **automatically restores** the last used configuration — no re-entry needed.
- State persists across: project name, output path, port lists, sequences, module names, source files, agent topology, all toggles.

---

## 🏗️ Application Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      XcelUVM Application                     │
│                                                              │
│  ┌─────────────────────┐      ┌──────────────────────────┐   │
│  │   Frontend (PyQt5)  │      │   Backend (Tcl Engine)   │   │
│  │                     │      │                          │   │
│  │  7-Step Wizard      │─────▶│  34 Tcl Scripts          │──▶│──▶ UVM Project
│  │  Animated UI        │      │  32 SV Templates         │   │    Files
│  │  Real-time Log      │      │  Port Substitution       │   │
│  └──────────┬──────────┘      └──────────────────────────┘   │
│             │                                                 │
│             ▼                                                 │
│  ┌─────────────────────┐      ┌──────────────────────────┐   │
│  │   AI Overlay        │      │   LLM Client             │   │
│  │   (Cinematic UX)    │─────▶│                          │──▶│──▶ AI-Filled
│  │                     │      │  Gemini / OpenAI         │   │    .sv/.c/.py
│  │  API Key Entry      │      │  Claude / OpenRouter     │   │
│  │  Model Selection    │      │  RAG Prompt Builder      │   │
│  │  Phase Navigation   │      │  Prose Stripper          │   │
│  └─────────────────────┘      └──────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

**Cycle-by-Cycle Data Flow (enforced by both the tool and AI rules):**

```
Sequence ──randomize()──▶ seq_item ──drive()──▶ DUT
                                                  │
Monitor ◀──── captures ALL signals (in + out) ◀──┘
    │
    ├──▶ Scoreboard / Predictor  (DUT output vs Reference Model)
    └──▶ Coverage Collector      (samples covergroup every cycle)
```

---

## 🚀 Getting Started

### Prerequisites

| Requirement | Version | Install |
|------------|---------|---------|
| Python | 3.10+ | [python.org](https://python.org) |
| PyQt5 | 5.15+ | `pip install PyQt5` |
| Tcl/Tk | 8.6+ | Bundled in `Backend/Backend_tcl/tcl_bin/` **or** [ActiveTcl](https://www.activestate.com/products/tcl/) |
| google-genai | latest | `pip install google-genai` |
| openai | latest | `pip install openai` |
| anthropic | latest | `pip install anthropic` *(optional, for Claude)* |

### Installation

```bash
git clone https://github.com/Abdel-Hay21/XcelUVM.git
cd XcelUVM
pip install -r requirements.txt
```

### Run

```bash
python Frontend/main.py
```

---

## 📖 Step-by-Step Usage

| Step | Action |
|------|--------|
| **1 — Project** | Set project name and output directory |
| **2 — Reference Model** | Choose SB (SW model) or RTL mode; select language if SB |
| **3 — Options** | Toggle Assertions, Functional Coverage, Code Coverage |
| **4 — Agents** | Select Single or Multi-Agent; configure active/passive counts |
| **5 — Module Names** | Enter DUT (and Golden Model for RTL mode) names; add source files |
| **6 — Ports** | Configure port lists per agent (auto-parse RTL or enter manually) |
| **7 — Sequences** | Define test sequences with names and transaction counts |
| **⚡ Generate** | Click **GENERATE UVM** and watch the real-time log |
| **🤖 AI Phase** | Enter API key, pick a model, provide optional instructions, generate |

---

## 📁 Repository Structure

```
XcelUVM/
├── Frontend/
│   ├── main.py                      ← Entry point
│   ├── core/
│   │   ├── config.py                ← Paths & constants
│   │   ├── parser.py                ← run.tcl state loader
│   │   ├── runner.py                ← Background Tcl thread
│   │   └── theme.py                 ← Dark title bar
│   └── ui/
│       ├── main_window.py           ← 7-step wizard
│       ├── ai_prompt_overlay.py     ← Cinematic AI overlay
│       ├── agent_cards.py           ← Agent topology cards
│       ├── gm_cards.py              ← Reference model cards
│       ├── sections.py              ← Port & sequence editors
│       ├── widgets.py               ← Shared custom widgets
│       ├── prompt_input_widget.py   ← AI prompt input bar
│       └── aura_wheel.py            ← Animated background wheel
├── Backend/
│   ├── Backend_tcl/
│   │   ├── run.tcl                  ← Main runner (auto-generated)
│   │   ├── templete_uvm/            ← 32 UVM template files
│   │   ├── doc/                     ← Architecture PDF guides
│   │   └── *.tcl                    ← 34 generation scripts
│   ├── Backend_AI/
│   │   ├── llm_client.py            ← Multi-provider LLM client
│   │   ├── prompt_builder.py        ← RAG prompt builder
│   │   └── rag_chunks.json          ← UVM style reference chunks
│   └── Backend_self/
│       └── sv_parser.py             ← SystemVerilog port parser
└── README.md
```

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add your feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Abdel-Hay** — Hardware Verification Engineer & VLSI Enthusiast

[![GitHub](https://img.shields.io/badge/GitHub-Abdel--Hay21-181717?style=for-the-badge&logo=github)](https://github.com/Abdel-Hay21)

---

<div align="center">

*Built with ❤️ for the hardware verification community*

**XcelUVM — Accelerate Your Verification**

</div>
