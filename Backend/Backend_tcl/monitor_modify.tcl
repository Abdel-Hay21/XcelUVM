# --------- monitor_modify.tcl ---------
if {$gm_type eq "RTL"} {
    # --------- monitor_modify.tcl ---------
    # This script edits the generated monitor file and replaces:
    #   // DUT_sequence_item_equal_virtual_interface
    #   // REF_sequence_item_equal_virtual_interface
    # with auto-generated port assignments for DUT and REF (excluding clk)
    
    # --------- Ensure project_name and path are already defined ---------
    if {![info exists project_name] || ![info exists path]} {
        puts "Error: project_name or path not defined. Please source run.tcl first."
        exit 1
    }
    
    set output_dir   "${path}${project_name}_uvm/verif"
    set monitor_file "${output_dir}/agent/${project_name}_monitor.sv"
    
    if {![file exists $monitor_file]} {
        puts "Error: Monitor file not found at $monitor_file"
        exit 1
    }
    
    # --------- Read the monitor file ---------
    set fp [open $monitor_file r]
    set data [read $fp]
    close $fp
    
    # --------- Find max name length (excluding clk) for = alignment ---------
    set max_name_len 0
    set user_clk [expr {[llength $input_ports] > 0 ? [lindex [lindex $input_ports 0] 0] : "clk"}]
    foreach port [concat $input_ports $output_ports] {
        set n [lindex $port 0]
        if {$n ne $user_clk} {
            set l [string length $n]
            if {$l > $max_name_len} { set max_name_len $l }
        }
    }
    
    # --------- Build DUT replacement text ---------
    set dut_text ""
    foreach port [concat $input_ports $output_ports] {
        set name [lindex $port 0]
        if {$name ne $user_clk} {
            set pad [string repeat " " [expr {$max_name_len - [string length $name]}]]
            append dut_text "            DUT_sequence_item.${name}${pad}    =   DUT_virtual_interface.${name}${pad}    ;\n"
        }
    }
    
    # --------- Build REF replacement text ---------
    set REF_text ""
    foreach port [concat $input_ports $output_ports] {
        set name [lindex $port 0]
        if {$name ne $user_clk} {
            set pad [string repeat " " [expr {$max_name_len - [string length $name]}]]
            append REF_text "            REF_sequence_item.${name}${pad}    =   REF_virtual_interface.${name}${pad}    ;\n"
        }
    }
    
    # --------- Perform replacements ---------
    set new_data $data
    set new_data [string map [list "// DUT_sequence_item_equal_virtual_interface" $dut_text] $new_data]
    set new_data [string map [list "// REF_sequence_item_equal_virtual_interface" $REF_text] $new_data]
    
    # --------- Write back the modified file ---------
    set fp [open $monitor_file w]
    puts -nonewline $fp $new_data
    close $fp
    
    puts "Monitor file updated successfully with DUT & REF assignments: $monitor_file"
} else {
    # --------- monitor_modify.tcl ---------
    # Edits each agent's monitor file (per-agent directory).
    
    if {![info exists project_name] || ![info exists path]} {
        puts "Error: project_name or path not defined."
        exit 1
    }
    
    set output_dir "${path}${project_name}_uvm/verif"
    set agent_dir  "${output_dir}/agent"
    
    proc modify_monitor {monitor_file in_ports out_ports u_clk} {
        if {![file exists $monitor_file]} {
            puts "Warning: Monitor file not found at $monitor_file"
            return
        }
        set fp [open $monitor_file r]; set data [read $fp]; close $fp
    
        set max_name_len 0
        foreach port [concat $in_ports $out_ports] {
            set n [lindex $port 0]
            if {$n ne $u_clk} {
                set l [string length $n]
                if {$l > $max_name_len} { set max_name_len $l }
            }
        }
        set dut_text ""
        foreach port [concat $in_ports $out_ports] {
            set name [lindex $port 0]
            if {$name ne $u_clk} {
                set pad [string repeat " " [expr {$max_name_len - [string length $name]}]]
                append dut_text "            DUT_sequence_item.${name}${pad} = DUT_virtual_interface.${name}${pad} ;\n"
            }
        }
        set golden_text ""
        foreach port [concat $in_ports $out_ports] {
            set name [lindex $port 0]
            if {$name ne $u_clk} {
                set pad [string repeat " " [expr {$max_name_len - [string length $name]}]]
                append golden_text "            Golden_sequence_item.${name}${pad} = Golden_virtual_interface.${name}${pad} ;\n"
            }
        }
        set new_data [string map [list \
            "// DUT_sequence_item_equal_virtual_interface"    $dut_text \
            "// Golden_sequence_item_equal_virtual_interface" $golden_text] $data]
    
        set fp [open $monitor_file w]; puts -nonewline $fp $new_data; close $fp
        puts "Monitor updated: $monitor_file"
    }
    
    if {$single_agent} {
        set in_ports  [expr {[info exists input_ports_A1] && [llength $input_ports_A1] > 0 ? $input_ports_A1 : ( [info exists input_ports] ? $input_ports : {} )}]
        set out_ports [expr {[info exists output_ports_A1] && [llength $output_ports_A1] > 0 ? $output_ports_A1 : ( [info exists output_ports] ? $output_ports : {} )}]
        set clk_name  [expr {[llength $in_ports] > 0 ? [lindex [lindex $in_ports 0] 0] : "clk"}]
        modify_monitor "${agent_dir}/${project_name}_monitor.sv" $in_ports $out_ports $clk_name
    } else {
        for {set i 1} {$i <= $Num_AC_agent} {incr i} {
            set ai      [lindex $active_agent [expr {$i-1}]]
            set aname   [lindex $ai 0]; set has_clk [lindex $ai 1]
            set in_var  "input_ports_A${i}"; set out_var "output_ports_A${i}"
            set in_ports  [expr {[info exists $in_var]  ? [set $in_var]  : {}}]
            set out_ports [expr {[info exists $out_var] ? [set $out_var] : {}}]
            set clk_name  [expr {$has_clk ? [lindex [lindex $in_ports 0] 0] : "clk"}]
            modify_monitor "${agent_dir}/Active/${aname}/${project_name}_${aname}_monitor.sv" \
                           $in_ports $out_ports $clk_name
        }
        for {set i 1} {$i <= $Num_PA_agent} {incr i} {
            set pi      [lindex $passive_agent [expr {$i-1}]]
            set pname   [lindex $pi 0]; set has_clk [lindex $pi 1]
            set in_var  "input_ports_P${i}"; set out_var "output_ports_P${i}"
            set in_ports  [expr {[info exists $in_var]  ? [set $in_var]  : {}}]
            set out_ports [expr {[info exists $out_var] ? [set $out_var] : {}}]
            set clk_name  [expr {$has_clk ? [lindex [lindex $in_ports 0] 0] : "clk"}]
            modify_monitor "${agent_dir}/Passive/${pname}/${project_name}_${pname}_monitor.sv" \
                           $in_ports $out_ports $clk_name
        }
    }
}
