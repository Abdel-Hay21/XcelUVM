# ================================================
# lib_multi_agent_test_top.tcl
# MULTI-AGENT mode — Part 3: config_obj, test, top,
# and any remaining shared templates (e.g. sequence files).
#
# Sourced at the end of lib_multi_agent_env.tcl once the
# environment file has been written.
# ================================================

# ── Generate CONFIG OBJECT (multi-agent virtual interfaces) ─────────
set cfg_data [read_template $template_dir config_obj $project_name $user_clk $suffix]
set cfg_vifs ""

# Calculate padding for config_obj virtual interfaces
set max_if_type 0
set max_vif_name 0
set all_agents {}
for {set i 1} {$i <= $Num_AC_agent} {incr i} { lappend all_agents [lindex [lindex $active_agent [expr {$i-1}]] 0] }
for {set i 1} {$i <= $Num_PA_agent} {incr i} { lappend all_agents [lindex [lindex $passive_agent [expr {$i-1}]] 0] }

foreach ag_name $all_agents {
    set if_type "${project_name}_${ag_name}_interface"
    set vif_name "${ag_name}_virtual_interface"
    if {[string length $if_type] > $max_if_type} { set max_if_type [string length $if_type] }
    if {[string length $vif_name] > $max_vif_name} { set max_vif_name [string length $vif_name] }
}

proc pad {str len} {
    set pad_len [expr {$len - [string length $str]}]
    if {$pad_len < 0} { set pad_len 0 }
    return "${str}[string repeat " " $pad_len]"
}

foreach ag_name $all_agents {
    set if_type "${project_name}_${ag_name}_interface"
    set vif_name "${ag_name}_virtual_interface"
    append cfg_vifs "       virtual [pad $if_type $max_if_type]   [pad $vif_name $max_vif_name]    ;\n"
}
set cfg_data [string map [list "       virtual ${project_name}_interface DUT_virtual_interface ;" $cfg_vifs] $cfg_data]
write_file "${output_dir}/config/${project_name}_config_obj.sv" $cfg_data

# ── Generate TEST (multi-agent: per-agent config_db get) ─────────────
set test_data [read_template $template_dir test $project_name $user_clk $suffix]

set cfg_gets ""
for {set i 1} {$i <= $Num_AC_agent} {incr i} {
    set aname [lindex [lindex $active_agent [expr {$i-1}]] 0]
    append cfg_gets "    if(!uvm_config_db #(virtual ${project_name}_${aname}_interface)::get(this,\"\",\"${project_name}_${aname}_DUT_interface\", cfg.${aname}_virtual_interface))\n"
    append cfg_gets "      \`uvm_fatal(\"build_phase\", \"Test - unable to get ${aname} virtual interface\");\n\n"
}
for {set i 1} {$i <= $Num_PA_agent} {incr i} {
    set pname [lindex [lindex $passive_agent [expr {$i-1}]] 0]
    append cfg_gets "    if(!uvm_config_db #(virtual ${project_name}_${pname}_interface)::get(this,\"\",\"${project_name}_${pname}_DUT_interface\", cfg.${pname}_virtual_interface))\n"
    append cfg_gets "      \`uvm_fatal(\"build_phase\", \"Test - unable to get ${pname} virtual interface\");\n\n"
}
set test_data [string map [list \
    "    if(!uvm_config_db #(virtual ${project_name}_interface)::get(this,\"\",\"${project_name}_DUT_interface\", cfg.DUT_virtual_interface))\n      \`uvm_fatal(\"build_phase\", \"Test - unable to get the ${project_name} DUT virtual interface from config\");" \
    $cfg_gets] $test_data]
write_file "${output_dir}/test/${project_name}_test.sv" $test_data

# ── Generate TOP (multi-agent: per-agent interface + config_db::set) ──
set top_data [read_template $template_dir top $project_name $user_clk $suffix]

set if_insts ""; set cfg_sets ""

# Calculate padding for interfaces
set all_agents {}
for {set i 1} {$i <= $Num_AC_agent} {incr i} { lappend all_agents [lindex [lindex $active_agent [expr {$i-1}]] 0] }
for {set i 1} {$i <= $Num_PA_agent} {incr i} { lappend all_agents [lindex [lindex $passive_agent [expr {$i-1}]] 0] }

set max_if_type 0
set max_if_name 0
set max_if_str 0
foreach ag_name $all_agents {
    set if_type "${project_name}_${ag_name}_interface"
    set if_name "${ag_name}_interface"
    set if_str "\"${project_name}_${ag_name}_DUT_interface\""
    if {[string length $if_type] > $max_if_type} { set max_if_type [string length $if_type] }
    if {[string length $if_name] > $max_if_name} { set max_if_name [string length $if_name] }
    if {[string length $if_str] > $max_if_str} { set max_if_str [string length $if_str] }
}

for {set i 1} {$i <= $Num_AC_agent} {incr i} {
    set ai      [lindex $active_agent [expr {$i-1}]]
    set aname   [lindex $ai 0]; set has_clk [lindex $ai 1]
    set clk_arg [expr {$has_clk ? " ${user_clk} " : ""}]
    
    set if_type "${project_name}_${aname}_interface"
    set if_name "${aname}_interface"
    set if_str "\"${project_name}_${aname}_DUT_interface\""
    
    append if_insts "     [pad $if_type $max_if_type]   [pad $if_name $max_if_name] (${clk_arg}) ;\n"
    append cfg_sets "    uvm_config_db#( virtual [pad $if_type $max_if_type] )::set(null,  \"*\", [pad $if_str $max_if_str] , [pad $if_name $max_if_name] ) ;\n"
}
for {set i 1} {$i <= $Num_PA_agent} {incr i} {
    set pi      [lindex $passive_agent [expr {$i-1}]]
    set pname   [lindex $pi 0]; set has_clk [lindex $pi 1]
    set clk_arg [expr {$has_clk ? " ${user_clk} " : ""}]
    
    set if_type "${project_name}_${pname}_interface"
    set if_name "${pname}_interface"
    set if_str "\"${project_name}_${pname}_DUT_interface\""
    
    append if_insts "     [pad $if_type $max_if_type]   [pad $if_name $max_if_name] (${clk_arg}) ;\n"
    append cfg_sets "    uvm_config_db#( virtual [pad $if_type $max_if_type] )::set(null,  \"*\", [pad $if_str $max_if_str] , [pad $if_name $max_if_name] ) ;\n"
}

set all_dut_ports {}
for {set i 1} {$i <= $Num_AC_agent} {incr i} {
    set aname [lindex [lindex $active_agent [expr {$i-1}]] 0]
    set in_var "input_ports_A${i}"
    set out_var "output_ports_A${i}"
    if {[info exists $in_var]} {
        foreach p [set $in_var] {
            lappend all_dut_ports [list [lindex $p 0] "${aname}_interface"]
        }
    }
    if {[info exists $out_var]} {
        foreach p [set $out_var] {
            lappend all_dut_ports [list [lindex $p 0] "${aname}_interface"]
        }
    }
}
for {set i 1} {$i <= $Num_PA_agent} {incr i} {
    set pname [lindex [lindex $passive_agent [expr {$i-1}]] 0]
    set in_var "input_ports_P${i}"
    set out_var "output_ports_P${i}"
    if {[info exists $in_var]} {
        foreach p [set $in_var] {
            lappend all_dut_ports [list [lindex $p 0] "${pname}_interface"]
        }
    }
    if {[info exists $out_var]} {
        foreach p [set $out_var] {
            lappend all_dut_ports [list [lindex $p 0] "${pname}_interface"]
        }
    }
}

set max_port_len 0
foreach port_entry $all_dut_ports {
    set n [string length [lindex $port_entry 0]]
    if {$n > $max_port_len} { set max_port_len $n }
}

set port_map_dut "(\n"
set idx 0
set total_ports [llength $all_dut_ports]
foreach port_entry $all_dut_ports {
    set pname   [lindex $port_entry 0]
    set if_inst [lindex $port_entry 1]
    incr idx
    set pad [string repeat " " [expr {$max_port_len - [string length $pname]}]]
    if {$idx < $total_ports} {
        append port_map_dut "       .${pname}${pad} ( ${if_inst}.${pname}${pad} ) ,\n"
    } else {
        append port_map_dut "       .${pname}${pad} ( ${if_inst}.${pname}${pad} )\n     )"
    }
}

set col1_max [string length $dut_module]
set top_data [string map [list \
    "  // Interfaces\n     ${project_name}_interface     DUT_interface    (      ${user_clk}      ) ;   // create ${project_name} interface of DUT" \
    "  // Interfaces\n${if_insts}" \
    "    uvm_config_db#(virtual ${project_name}_interface)::set(null, \"*\", \"${project_name}_DUT_interface\", DUT_interface);" \
    $cfg_sets \
    "NODUT_COL1"   [_pad $dut_module $col1_max] \
    "DUT_PORT_MAP" $port_map_dut] $top_data]

if {$a_flag} {
    set first_ac [lindex [lindex $active_agent 0] 0]
    set top_data [string map [list \
        "ASSERTIONS_COL1" "${project_name}_assertions" \
        "( DUT_interface )" "( ${first_ac}_interface )" \
    ] $top_data]
} else {
    set top_data [regsub -line {^[ \t]*ASSERTIONS_COL1.*\n} $top_data ""]
}
write_file "${output_dir}/top/${project_name}_top.sv" $top_data
puts "Generated: top/${project_name}_top.sv"

# ── Generate all remaining shared templates (sequence, etc.) ────────
set template_files [glob -nocomplain -directory $template_dir *]
foreach file $template_files {
    set filename [file tail $file]
    if {[string match "*_RTL.sv" $filename]} { continue }
    
    # Skip anything already generated above
    if {[string match "*_agent*"     $filename] ||
        [string match "*_driver*"    $filename] ||
        [string match "*_monitor*"   $filename] ||
        [string match "*_seq_item*"  $filename] ||
        [string match "*_sequencer*" $filename] ||
        [string match "*_environment*" $filename] ||
        [string match "*_scoreboard*"  $filename] ||
        [string match "*_coverage*"    $filename] ||
        [string match "*predictor*"   $filename] ||
        [string match "reference_model*" $filename] ||
        [string match "*_test*"      $filename] ||
        [string match "*_top*"       $filename] ||
        [string match "*_config_obj*" $filename]} { continue }

    if {!$a_flag && [string match "*_assertions*" $filename]} { continue }

    set base_filename [string map {"_SB.sv" ".sv"} $filename]
    set new_filename [string map [list templete $project_name] $base_filename]
    set fp [open $file r]; set data [read $fp]; close $fp
    set new_data [string map [list templete $project_name USER_CLK $user_clk] $data]

    set subdir [get_template_subdir $filename]
    write_file "${output_dir}/${subdir}/${new_filename}" $new_data
}
