import os
import shutil
import subprocess
from PyQt5.QtCore import QThread, pyqtSignal
from core.config import get_run_tcl, BACKEND_DIR



class TclRunner(QThread):
    output_ready = pyqtSignal(str)
    finished_ok  = pyqtSignal()
    finished_err = pyqtSignal(str)

    def __init__(self, project_name, output_path, input_ports, output_ports,
                 sequences, dut_module, golden_module, assertions=True, coverage=True, C_coverage=True,
                 gm_type="RTL", sb_language="SV", ag_mode="SINGLE",
                 Num_AC_agent="1", Num_PA_agent="0",
                 interfaces=None, rtl_files=None, ref_files=None):
        """
        interfaces: list of dicts for GM_SB, each:
            {
              'name': str,
              'kind': 'active' | 'passive',
              'has_clk': bool,
              'clk_name': str,
              'input_ports':  [(name, bits), ...],   # WITHOUT clock
              'output_ports': [(name, bits), ...]
            }
        For GM_RTL, interfaces=None and input_ports/output_ports are used flat.
        rtl_files: list of absolute paths to RTL source files to copy into the
                   generated project's rtl/ folder.
        ref_files: list of absolute paths to Reference Model source files to copy into the
                   generated project's verif/reference_model/ folder (for GM_RTL).
        """
        super().__init__()
        self.project_name       = project_name
        self.output_path        = output_path
        self.input_ports        = input_ports
        self.output_ports       = output_ports
        self.sequences          = sequences
        self.dut_module         = dut_module
        self.golden_module      = golden_module
        self.assertions         = assertions
        self.coverage           = coverage
        self.C_coverage         = C_coverage
        self.gm_type            = gm_type
        self.sb_language        = sb_language
        self.ag_mode            = ag_mode
        self.num_active_agents  = Num_AC_agent
        self.num_passive_agents = Num_PA_agent
        self.interfaces         = interfaces or []
        self.rtl_files          = rtl_files or []
        self.ref_files          = ref_files or []

    @staticmethod
    def _ports_tcl(var, ports):
        rows = "\n".join(f"    {{{n} {b} bit}}" for n, b in ports)
        return f"set {var} {{\n{rows}\n}}"

    @staticmethod
    def _seqs_tcl(var, seqs):
        rows = "\n".join(f"    {{{n} {c}}}" for n, c in seqs)
        return f"set {var} {{\n{rows}\n}}"

    @staticmethod
    def _agent_list_tcl(var, agents):
        if not agents:
            return f"set {var} {{\n}}"
        rows = "\n".join(f"    {{{name} {hc}}}" for name, hc in agents)
        return f"set {var} {{\n{rows}\n}}"

    def _generate_run_tcl_content(self):
        norm_path = self.output_path.replace("\\", "/").rstrip("/") + "/"
        aval  = "true" if self.assertions else "false"
        cval  = "true" if self.coverage else "false"
        ccval = "true" if self.C_coverage else "false"

        if self.gm_type == "SB" and self.interfaces:
            active_ifs  = [i for i in self.interfaces if i['kind'] == 'active']
            passive_ifs = [i for i in self.interfaces if i['kind'] == 'passive']
            num_active  = len(active_ifs)
            num_passive = len(passive_ifs)
            single      = "true" if (num_active + num_passive) <= 1 else "false"
            active_list  = [(i['name'], 1 if i.get('has_clk', True) else 0) for i in active_ifs]
            passive_list = [(i['name'], 1 if i.get('has_clk', True) else 0) for i in passive_ifs]

            port_blocks = []
            for idx, iface in enumerate(active_ifs, start=1):
                in_ports = list(iface['input_ports'])
                if iface.get('has_clk', True) and iface.get('clk_name'):
                    in_ports = [(iface['clk_name'], 1)] + in_ports
                port_blocks.append(self._ports_tcl(f"input_ports_A{idx}", in_ports))
                port_blocks.append(self._ports_tcl(f"output_ports_A{idx}", iface['output_ports']))

            for idx, iface in enumerate(passive_ifs, start=1):
                in_ports = list(iface['input_ports'])
                if iface.get('has_clk', True) and iface.get('clk_name'):
                    in_ports = [(iface['clk_name'], 1)] + in_ports
                port_blocks.append(self._ports_tcl(f"input_ports_P{idx}", in_ports))
                port_blocks.append(self._ports_tcl(f"output_ports_P{idx}", iface['output_ports']))

            ports_str = "\n\n".join(port_blocks)
        elif self.gm_type == "SB":
            # SB fallback without interfaces
            num_active = 1
            num_passive = 0
            single = "true"
            active_list = [("agent", 1)]
            passive_list = []
            ports_str = f"{self._ports_tcl('input_ports_A1', self.input_ports)}\n\n{self._ports_tcl('output_ports_A1', self.output_ports)}"
        else:
            # RTL mode
            num_active = int(self.num_active_agents) if self.ag_mode == "MULTI" else 1
            num_passive = int(self.num_passive_agents) if self.ag_mode == "MULTI" else 0
            single = "false" if self.ag_mode == "MULTI" else "true"
            active_list = [("agent", 1)]
            passive_list = []
            ports_str = f"{self._ports_tcl('input_ports', self.input_ports)}\n\n{self._ports_tcl('output_ports', self.output_ports)}"

        active_agent_str = self._agent_list_tcl("active_agent", active_list)
        passive_agent_str = self._agent_list_tcl("passive_agent", passive_list)
        seqs_str = self._seqs_tcl("sequence_list", self.sequences)

        rtl_files_list = "\n".join(f'    "{f}"' for f in self.rtl_files)
        rtl_files_str = f"set rtl_files {{\n{rtl_files_list}\n}}" if self.rtl_files else "set rtl_files {}"

        ref_files_list = "\n".join(f'    "{f}"' for f in self.ref_files)
        ref_files_str = f"set ref_files {{\n{ref_files_list}\n}}" if self.ref_files else "set ref_files {}"

        content = f"""# ================================
# run.tcl
# Main runner script
# ================================

set gm_type          "{self.gm_type}"
set project_name     "{self.project_name}"
set path             "{norm_path}"
{seqs_str}
set dut_module       "{self.dut_module}"
set REF_module       "{self.golden_module}"
set assertions       {aval}
set coverage         {cval}
set Code_Coverage    {ccval}
set sb_language      "{self.sb_language}"
set single_agent     {single}

set Num_AC_agent     "{num_active}"
set Num_PA_agent     "{num_passive}"

{active_agent_str}

{passive_agent_str}

{rtl_files_str}

{ref_files_str}

# --------- Define interface port lists ---------
{ports_str}

# delete file if exist
set project_dir "${{path}}${{project_name}}_uvm"

if {{[file isdirectory $project_dir]}} {{
    file delete -force $project_dir
}}

# --------- Call sub-scripts ---------
source generate_files.tcl
source seq_item_modify.tcl
source generate_interface.tcl
source driver_modify.tcl
source monitor_modify.tcl
source generate_sequence.tcl
source sequence_modify.tcl
source virtual_sequence_modify.tcl
source test_modify.tcl
source custum_coverage.tcl

if {{$gm_type eq "SB"}} {{
    source modify_coverage.tcl
    source modify_predictor.tcl
    source modify_reference_model.tcl
}}
source modify_scoreboard.tcl
source generate_wave.tcl

if {{$gm_type eq "RTL"}} {{
    source generate_src_files.tcl
}}
"""
        return content, norm_path, aval, cval, ccval

    def run(self):
        run_tcl_path = get_run_tcl()
        try:
            content, norm, aval, cval, ccval = self._generate_run_tcl_content()
            with open(run_tcl_path, "w", encoding="utf-8") as f:
                f.write(content)

            self.output_ready.emit(f'\u2714  project_name  \u2192 "{self.project_name}"\n')
            self.output_ready.emit(f'\u2714  output path   \u2192 "{norm}"\n')
            self.output_ready.emit(f'\u2714  dut_module    \u2192 "{self.dut_module}"\n')
            self.output_ready.emit(f'\u2714  golden_module \u2192 "{self.golden_module}"\n')
            self.output_ready.emit(f'\u2714  assertions    \u2192 {aval}\n')
            self.output_ready.emit(f'\u2714  coverage      \u2192 {cval}\n')
            self.output_ready.emit(f'\u2714  Code coverage \u2192 {ccval}\n')
            self.output_ready.emit(f'\u2714  input_ports   \u2192 {len(self.input_ports)} port(s)\n')
            self.output_ready.emit(f'\u2714  output_ports  \u2192 {len(self.output_ports)} port(s)\n')
            self.output_ready.emit(f'\u2714  sequences     \u2192 {len(self.sequences)} sequence(s)\n\n')

        except Exception as e:
            self.finished_err.emit(f"Failed to write run.tcl:\n{e}")
            return

        try:
            target_cwd = BACKEND_DIR
            creation_flags = 0
            if os.name == 'nt':
                creation_flags = subprocess.CREATE_NO_WINDOW

            run_tcl_path = get_run_tcl()
            
            # --- Check for bundled tclsh ---
            local_tclsh = os.path.join(BACKEND_DIR, "tcl_bin", "tclsh.exe")
            tcl_exe = local_tclsh if os.path.isfile(local_tclsh) else "tclsh"

            proc = subprocess.Popen(
                [tcl_exe, run_tcl_path], cwd=target_cwd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                creationflags=creation_flags)
            for line in proc.stdout:
                self.output_ready.emit(line)
            proc.wait()
            if proc.returncode == 0:
                # --- Copy RTL source files into the generated rtl/ folder ---
                if self.rtl_files:
                    norm_path = self.output_path.replace("\\", "/").rstrip("/") + "/"
                    rtl_dest  = os.path.join(norm_path, f"{self.project_name}_uvm", "rtl")
                    os.makedirs(rtl_dest, exist_ok=True)
                    self.output_ready.emit("\n\U0001f4c2  Copying RTL source files...\n")
                    for src in self.rtl_files:
                        if os.path.isfile(src):
                            dest = os.path.join(rtl_dest, os.path.basename(src))
                            try:
                                shutil.copy2(src, dest)
                                self.output_ready.emit(f"   \u2714  {os.path.basename(src)}\n")
                            except Exception as e:
                                self.output_ready.emit(f"   \u2716  Error copying {os.path.basename(src)}: {e}\n")
                        else:
                            self.output_ready.emit(f"   \u26a0  Not found (skipped): {src}\n")

                # --- Copy Reference Model source files into verif/reference_model/ folder ---
                if self.gm_type == "RTL" and self.ref_files:
                    norm_path = self.output_path.replace("\\", "/").rstrip("/") + "/"
                    ref_dest  = os.path.join(norm_path, f"{self.project_name}_uvm", "verif", "reference_model")
                    os.makedirs(ref_dest, exist_ok=True)
                    self.output_ready.emit("\n📂  Copying Reference Model source files...\n")
                    for src in self.ref_files:
                        if os.path.isfile(src):
                            dest = os.path.join(ref_dest, os.path.basename(src))
                            try:
                                shutil.copy2(src, dest)
                                self.output_ready.emit(f"   ✔  {os.path.basename(src)}\n")
                            except Exception as e:
                                self.output_ready.emit(f"   ✖  Error copying {os.path.basename(src)}: {e}\n")
                        else:
                            self.output_ready.emit(f"   ⚠  Not found (skipped): {src}\n")

                self.finished_ok.emit()
            else:
                self.finished_err.emit(f"tclsh exited with code {proc.returncode}")
        except FileNotFoundError:
            self.finished_err.emit(
                "❌  tclsh not found!\n\n"
                "The Tcl interpreter is required to generate the UVM environment.\n\n"
                "► How to fix:\n"
                "  1. Add a standalone 'tclsh.exe' file directly inside the 'Backend/Backend_tcl' folder.\n\n"
                "  OR if you want to install it on your system:\n"
                "  1. Download and install Tcl from: https://www.activestate.com/products/tcl/\n"
                "  2. During installation, make sure 'Add to PATH' is checked.\n"
                "  3. Restart XcelUVM after installation."
            )
        except Exception as e:
            self.finished_err.emit(str(e))
