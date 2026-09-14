# ================================================
# lib_setup.tcl
# Resolves configuration defaults, builds directory layout,
# copies the frontend doc, and prepares variables.
# ================================================

array set dir_map {
    driver             agent
    monitor            agent
    sequencer          agent
    seq_item           agent
    agent              agent
    environment        environment
    coverage           environment
    scoreboard         environment
    predictor          environment
    sequence           environment
    virtual_sequencer  environment
    config_obj         config
    test               test
    top                top
    assertions         assertions
    bind               assertions
    virtual_sequence   sequences/virtual
}

set template_dir  "templete_uvm"
set root_dir      "${path}${project_name}_uvm"
set output_dir    "${root_dir}/verif"

set suffix [expr {$gm_type eq "RTL" ? "_RTL" : "_SB"}]

if {![info exists dut_module]    || $dut_module    eq ""} { set dut_module    "DUT_MODULE" }
if {![info exists golden_module] || $golden_module eq ""} { set golden_module "GOLDEN_MODULE" }
if {![info exists REF_module]    || $REF_module    eq ""} { set REF_module    "REF_MODULE" }
if {![info exists assertions]}                            { set assertions true }
if {![info exists coverage]}                              { set coverage true }

if {$gm_type eq "RTL"} {
    set user_clk [expr {[llength $input_ports] > 0 ? [lindex [lindex $input_ports 0] 0] : "clk"}]
} else {
    # Resolve the global user_clk from first active agent that has_clk=1
    set user_clk "clk"
    for {set i 1} {$i <= $Num_AC_agent} {incr i} {
        set agent_info [lindex $active_agent [expr {$i - 1}]]
        set has_clk    [lindex $agent_info 1]
        if {$has_clk eq ""} { set has_clk 0 }
        set in_var     "input_ports_A${i}"
        if {$has_clk && [info exists $in_var]} {
            set user_clk [lindex [lindex [set $in_var] 0] 0]
            break
        }
    }
}

if {![file exists $root_dir]} { file mkdir $root_dir }
file mkdir $output_dir
file mkdir "${root_dir}/test"
file mkdir "${root_dir}/doc"

if {$gm_type eq "RTL"} {
    file mkdir "${root_dir}/verif/reference_model"
    file mkdir "${root_dir}/rtl"
} else {
    file mkdir "${root_dir}/rtl"
    if {[file exists "${root_dir}/rtl/Golden_model"]} { file delete -force "${root_dir}/rtl/Golden_model" }
}

set a_flag [expr {($assertions eq "true" || $assertions eq 1 || $assertions eq "True") ? 1 : 0}]
set c_flag [expr {($coverage eq "true" || $coverage eq 1 || $coverage eq "True") ? 1 : 0}]
set pdf_name "C_${c_flag}__A_${a_flag}.pdf"

if {$gm_type eq "RTL"} {
    set frontend_doc [expr {$single_agent ? "./doc/GM_RTL_SA/${pdf_name}" : "./doc/GM_RTL_MA/${pdf_name}"}]
} else {
    set frontend_doc [expr {$single_agent ? "./doc/GM_SB_SA/${pdf_name}" : "./doc/GM_SB_MA/${pdf_name}"}]
}

if {[file exists $frontend_doc]} {
    file copy -force $frontend_doc "${root_dir}/doc/${project_name}_uvm.pdf"
}

if {$gm_type eq "SB" && [info exists sb_language] && ([string match "py*" [string tolower $sb_language]] || [string match "ex*" [string tolower $sb_language]])} {
    set net_doc_dir "./doc/GM_SB_network"
    if {[file exists $net_doc_dir]} {
        foreach pdf_f [glob -nocomplain -directory $net_doc_dir "*.pdf"] {
            file copy -force $pdf_f "${root_dir}/doc/[file tail $pdf_f]"
        }
    }
}

set subdir_list {agent environment interface config sequences test top}
if {$gm_type eq "SB"} { lappend subdir_list reference_model }
if {$a_flag} { lappend subdir_list assertions }

foreach subdir $subdir_list {
    set d "${output_dir}/${subdir}"
    if {![file exists $d]} { file mkdir $d }
}

if {$gm_type eq "SB"} {
    if {![info exists sb_language] || $sb_language eq ""} { set sb_language "SV" }
    set lang_lower [string tolower $sb_language]
    if {[string match "c*" $lang_lower]} {
        set c_dir "${output_dir}/reference_model/c"
        if {![file exists $c_dir]} { file mkdir $c_dir }
        set c_src_file "${c_dir}/${project_name}_reference_model.c"
        set c_hdr_file "${c_dir}/${project_name}_reference_model.h"
        set fp [open $c_src_file w]; close $fp
        set fp [open $c_hdr_file w]; close $fp
    } elseif {[string match "py*" $lang_lower] || [string match "ex*" $lang_lower]} {
        set sv_dir  "${output_dir}/reference_model/SV"
        set dpi_dir "${output_dir}/reference_model/dpi"
        set py_dir  "${output_dir}/reference_model/python"
        
        file mkdir $sv_dir
        file mkdir $dpi_dir
        file mkdir $py_dir
        
        # Empty SV helper files
        foreach sv_f {protocol_pkg.sv protocol_encoder.sv protocol_decoder.sv} {
            set fp [open "${sv_dir}/${sv_f}" w]; close $fp
        }
        # Empty DPI files
        foreach dpi_f {dpi_socket.c socket_transport.c socket_transport.h protocol.h} {
            set fp [open "${dpi_dir}/${dpi_f}" w]; close $fp
        }
        # Empty Python files
        foreach py_f [list "${project_name}_reference_model.py" protocol.py server.py] {
            set fp [open "${py_dir}/${py_f}" w]; close $fp
        }
    }
}

if {!$a_flag} { file delete -force "${output_dir}/assertions" }
if {!$c_flag} { file delete -force "${output_dir}/environment/${project_name}_coverage.sv" }
file delete -force "${output_dir}/reference_model/${project_name}_reference_model.sv"
file delete -force "${output_dir}/reference_model/${project_name}_reference_model_proxy.sv"
if {$gm_type eq "RTL"} {
    file delete -force "${output_dir}/environment/${project_name}_predictor.sv"
}

if {$gm_type eq "SB" && $single_agent} {
    if {[info exists input_ports_A1] && [llength $input_ports_A1] > 0} {
        set input_ports $input_ports_A1
    } elseif {[info exists input_ports]} {
        set input_ports_A1 $input_ports
    } else {
        set input_ports {}
        set input_ports_A1 {}
    }
    if {[info exists output_ports_A1] && [llength $output_ports_A1] > 0} {
        set output_ports $output_ports_A1
    } elseif {[info exists output_ports]} {
        set output_ports_A1 $output_ports
    } else {
        set output_ports {}
        set output_ports_A1 {}
    }
}
