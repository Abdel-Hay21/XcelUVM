import os
import re
from core.config import get_run_tcl, BACKEND_DIR


def parse_run_tcl():
    """Parse a run.tcl file and return a config dict."""

    data = {
        "gm_type":       "RTL",
        "project_name":  "",
        "path":          "",
        "input_ports":   [],
        "output_ports":  [],
        "sequence_list": [],
        "dut_module":    "",
        "golden_module": "",
        "assertions":    True,
        "coverage":      True,
        "code_coverage": True,
        "sb_language":   "SV",
        "single_agent":  True,
        "num_ac_agent":  1,
        "num_pa_agent":  0,
        "active_agent":  [],
        "passive_agent": [],
        "clock_name":    "clk",
        "clock_en":      True,
        "rtl_files":     [],
        "ref_files":     [],
    }

    run_tcl_path = get_run_tcl()
    if not os.path.isfile(run_tcl_path):
        return data
    content = open(run_tcl_path, "r").read()

    m = re.search(r'set\s+gm_type\s+"([^"]*)"', content)
    if m:
        data["gm_type"] = m.group(1)

    m = re.search(r'set\s+project_name\s+"([^"]*)"', content)
    if m:
        data["project_name"] = m.group(1)

    m = re.search(r'set\s+path\s+"([^"]*)"', content)
    if m:
        data["path"] = m.group(1).rstrip("/")

    # sequence_list — {name count} tuples
    m = re.search(r'set\s+sequence_list\s*\{(.*?)\}(?=\s*set\s+dut_module)', content, re.DOTALL)
    if not m:
        m = re.search(r'set\s+sequence_list\s*\{(.*?)\}', content, re.DOTALL)
    if m:
        seq_block = m.group(1)
        seqs = re.findall(r'\{(\S+)\s+(\d+)\}', seq_block)
        if seqs:
            data["sequence_list"] = [(n, int(c)) for n, c in seqs]
        else:
            data["sequence_list"] = [(n, 1) for n in seq_block.split() if n]

    # rtl_files — simple list of paths
    m = re.search(r'set\s+rtl_files\s*\{(.*?)\}', content, re.DOTALL)
    if m:
        # split on newlines or spaces and strip quotes if any
        files = []
        for line in m.group(1).splitlines():
            line = line.strip()
            if line:
                # remove surrounding quotes if present
                if line.startswith('"') and line.endswith('"'):
                    line = line[1:-1]
                elif line.startswith("'") and line.endswith("'"):
                    line = line[1:-1]
                files.append(line)
        data["rtl_files"] = files

    # ref_files — simple list of paths
    m = re.search(r'set\s+ref_files\s*\{(.*?)\}', content, re.DOTALL)
    if m:
        files = []
        for line in m.group(1).splitlines():
            line = line.strip()
            if line:
                if line.startswith('"') and line.endswith('"'):
                    line = line[1:-1]
                elif line.startswith("'") and line.endswith("'"):
                    line = line[1:-1]
                files.append(line)
        data["ref_files"] = files

    m = re.search(r'set\s+dut_module\s+"([^"]*)"', content)
    if m:
        data["dut_module"] = m.group(1)

    # TCL uses REF_module; also support golden_module for older files
    m = re.search(r'set\s+REF_module\s+"([^"]*)"', content)
    if not m:
        m = re.search(r'set\s+golden_module\s+"([^"]*)"', content)
    if m:
        data["golden_module"] = m.group(1)

    m = re.search(r'set\s+assertions\s+(\S+)', content)
    data["assertions"] = (m.group(1).lower() == "true") if m else True

    m = re.search(r'set\s+coverage\s+(\S+)', content)
    data["coverage"] = (m.group(1).lower() == "true") if m else True

    m = re.search(r'set\s+Code_Coverage\s+(\S+)', content)
    data["code_coverage"] = (m.group(1).lower() == "true") if m else True

    m = re.search(r'set\s+sb_language\s+"([^"]*)"', content)
    if m:
        data["sb_language"] = m.group(1)

    m = re.search(r'set\s+single_agent\s+(\S+)', content)
    if m:
        data["single_agent"] = (m.group(1).lower() == "true")

    m = re.search(r'set\s+Num_AC_agent\s+"?(\d+)"?', content)
    if m:
        data["num_ac_agent"] = int(m.group(1))

    m = re.search(r'set\s+Num_PA_agent\s+"?(\d+)"?', content)
    if m:
        data["num_pa_agent"] = int(m.group(1))

    # Simple single-agent ports (GM_RTL style)
    for key in ("input_ports", "output_ports"):
        m = re.search(rf'set\s+{key}\s*\{{(.*?)\n\}}', content, re.DOTALL)
        if m:
            data[key] = [
                (n, int(b))
                for n, b in re.findall(r'\{(\S+)\s+(\d+)\s+bit\}', m.group(1))
            ]

    # Multi-agent ports: input_ports_A1, output_ports_A1 (GM_SB style)
    # If found and simple ports are empty, use agent 1's ports as default
    if not data["input_ports"]:
        m = re.search(r'set\s+input_ports_A1\s*\{(.*?)\n\}', content, re.DOTALL)
        if m:
            data["input_ports"] = [
                (n, int(b))
                for n, b in re.findall(r'\{(\S+)\s+(\d+)\s+bit\}', m.group(1))
            ]
    if not data["output_ports"]:
        m = re.search(r'set\s+output_ports_A1\s*\{(.*?)\n\}', content, re.DOTALL)
        if m:
            data["output_ports"] = [
                (n, int(b))
                for n, b in re.findall(r'\{(\S+)\s+(\d+)\s+bit\}', m.group(1))
            ]

    # ----------------------------------------------------------------
    # Detect clock: the first input port with width=1 that looks like
    # a clock (name contains 'clk') is treated as the clock signal.
    # Strip it from input_ports so the UI does not show it twice.
    # ----------------------------------------------------------------
    if data["input_ports"]:
        first_name, first_width = data["input_ports"][0]
        # A port is the clock if it is the first port AND its width is 1
        # (run.tcl always lists the clock first by convention).
        data["clock_name"] = first_name
        data["clock_en"]   = True
        data["input_ports"] = data["input_ports"][1:]

    return data
