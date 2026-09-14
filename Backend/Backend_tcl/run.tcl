# ================================
# run.tcl
# Main runner script
# ================================

set gm_type          "SB"
set project_name     "Wide_ALU"
set path             "F:/Faculty/Projects/test_uvm_tool/"
set sequence_list {
    {RESET 1}
    {Mixing_All_Opcodes 1000}
    {Corner_Cases 1000}
}
set dut_module       "ALU_DUT"
set REF_module       "UART_TX"
set assertions       true
set coverage         true
set Code_Coverage    true
set sb_language      "SV"
set single_agent     true

set Num_AC_agent     "1"
set Num_PA_agent     "0"

set active_agent {
    {agent 1}
}

set passive_agent {
}

set rtl_files {
    "F:/Faculty/Projects/ALU_uvm/rtl/ALU_DUT.sv"
}

set ref_files {
}

# --------- Define interface port lists ---------
set input_ports_A1 {
    {clk_i 1 bit}
    {rst_n 1 bit}
    {in_x 12 bit}
    {in_y 12 bit}
    {valid_in 1 bit}
    {opcode 2 bit}
}

set output_ports_A1 {
    {out 24 bit}
    {valid_out 1 bit}
}

# delete file if exist
set project_dir "${path}${project_name}_uvm"

if {[file isdirectory $project_dir]} {
    file delete -force $project_dir
}

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

if {$gm_type eq "SB"} {
    source modify_coverage.tcl
    source modify_predictor.tcl
    source modify_reference_model.tcl
}
source modify_scoreboard.tcl
source generate_wave.tcl

if {$gm_type eq "RTL"} {
    source generate_src_files.tcl
}
