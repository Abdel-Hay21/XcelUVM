# ================================================
# lib_single_agent.tcl
# SINGLE-AGENT mode for SB
# ================================================

set template_files [glob -nocomplain -directory $template_dir *]
if {[llength $template_files] == 0} { exit 1 }

set filtered_templates {}
foreach file $template_files {
    set filename [file tail $file]
    if {[string match "*_RTL.sv" $filename]} { continue }
    
    if {!$a_flag && [string match "*_assertions*" $filename]} { continue }
    if {!$c_flag && [string match "*_coverage*"   $filename]} { continue }
    if {[string match "*predictor_v.sv"  $filename] ||
        [string match "*predictor_c.sv"  $filename] ||
        [string match "*predictor_ex.sv" $filename]} { continue }
    if {[string match "reference_model_v.sv"       $filename] ||
        [string match "reference_model_proxy_c.sv" $filename] ||
        [string match "reference_model_proxy_ex.sv" $filename]} { continue }
        
    lappend filtered_templates $file
}

foreach file $filtered_templates {
    set filename [file tail $file]
    set base_filename [string map {"_SB.sv" ".sv"} $filename]
    set new_filename [string map [list templete $project_name] $base_filename]
    
    set fp [open $file r]; set data [read $fp]; close $fp
    set new_data [string map [list templete $project_name USER_CLK $user_clk] $data]

    if {[string match "*_top*" $filename]} {
        set assertions_str "${project_name}_assertions"
        set col1_max [expr {$a_flag ?
            max([string length $dut_module],[string length $golden_module],[string length $assertions_str]) :
            max([string length $dut_module],[string length $golden_module])}]
        set port_map_dut "(\n"
        set all_ports [concat $input_ports $output_ports]
        set max_port_len 0
        foreach port $all_ports { set n [string length [lindex $port 0]]; if {$n > $max_port_len} { set max_port_len $n } }
        set idx 0
        foreach port $all_ports {
            set pname [lindex $port 0]; incr idx
            set pad [string repeat " " [expr {$max_port_len - [string length $pname]}]]
            if {$idx < [llength $all_ports]} {
                append port_map_dut "       .${pname}${pad} ( DUT_interface.${pname}${pad} ) ,\n"
            } else {
                append port_map_dut "       .${pname}${pad} ( DUT_interface.${pname}${pad} )\n     )"
            }
        }
        if {$a_flag} {
            set new_data [string map [list "NODUT_COL1" [_pad $dut_module $col1_max] "DOGOLDEN_COL1" [_pad $golden_module $col1_max] "ASSERTIONS_COL1" [_pad $assertions_str $col1_max] "DUT_PORT_MAP" $port_map_dut] $new_data]
        } else {
            set new_data [string map [list "NODUT_COL1" [_pad $dut_module $col1_max] "DOGOLDEN_COL1" [_pad $golden_module $col1_max] "DUT_PORT_MAP" $port_map_dut] $new_data]
            set new_data [regsub -line {^[ \t]*ASSERTIONS_COL1.*\n} $new_data ""]
            set new_data [string map {"// DUT, Golden and Assertions" "// DUT, Golden"} $new_data]
        }
    }

    set subdir [get_template_subdir $filename]
    write_file "${output_dir}/${subdir}/${new_filename}" $new_data
}

# Single-agent: predictor and reference model
if {![info exists sb_language] || $sb_language eq ""} { set sb_language "SV" }
set lang_lower [string tolower $sb_language]
switch -glob -- $lang_lower {
    "sv*" {
        set pred_src "${template_dir}/templete_predictor_v.sv"
    }
    "c*" {
        set pred_src "${template_dir}/templete_predictor_c.sv"
    }
    "py*" -
    "ex*" -
    default {
        set pred_src "${template_dir}/templete_predictor_ex.sv"
    }
}
set fh [open $pred_src r]; set pred_data [read $fh]; close $fh
set pred_data [string map [list templete $project_name USER_CLK $user_clk] $pred_data]
write_file "${output_dir}/environment/${project_name}_predictor.sv" $pred_data

switch -glob -- $lang_lower {
    "sv*" {
        set ref_src "${template_dir}/reference_model_v.sv"
        set ref_dst "${output_dir}/reference_model/${project_name}_reference_model.sv"
    }
    "c*" {
        set ref_src "${template_dir}/reference_model_proxy_c.sv"
        set ref_dst "${output_dir}/reference_model/${project_name}_reference_model_proxy.sv"
    }
    "py*" -
    "ex*" -
    default {
        set ref_src "${template_dir}/reference_model_proxy_ex.sv"
        set ref_dst "${output_dir}/reference_model/SV/${project_name}_reference_model_proxy.sv"
    }
}
set fh [open $ref_src r]; set ref_data [read $fh]; close $fh
set ref_data [string map [list templete $project_name USER_CLK $user_clk] $ref_data]
write_file $ref_dst $ref_data


