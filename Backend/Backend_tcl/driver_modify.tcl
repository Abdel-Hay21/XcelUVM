# --------- driver_modify.tcl ---------
if {$gm_type eq "RTL"} {
    # --------- driver_modify.tcl ---------
    # This script edits the generated driver file and replaces:
    #   // virtual_interface_DUT_equal_sequence_item
    #   // virtual_interface_REF_equal_sequence_item
    # with auto-generated input signal assignments (excluding clk)
    
    # --------- Ensure project_name and path are already defined ---------
    if {![info exists project_name] || ![info exists path]} {
        puts "Error: project_name or path not defined. Please source run.tcl first."
        exit 1
    }
    
    set output_dir   "${path}${project_name}_uvm/verif"
    set driver_file  "${output_dir}/agent/${project_name}_driver.sv"
    
    if {![file exists $driver_file]} {
        puts "Error: Driver file not found at $driver_file"
        exit 1
    }
    
    # --------- Read driver file ---------
    set fp [open $driver_file r]
    set data [read $fp]
    close $fp
    
    # --------- Find max name length (excluding clk) for = alignment ---------
    set max_name_len 0
    set user_clk [expr {[llength $input_ports] > 0 ? [lindex [lindex $input_ports 0] 0] : "clk"}]
    foreach port $input_ports {
        set n [lindex $port 0]
        if {$n ne $user_clk} {
            set l [string length $n]
            if {$l > $max_name_len} { set max_name_len $l }
        }
    }
    
    # --------- Build DUT replacement text (inputs only, excluding clk) ---------
    set dut_text ""
    foreach port $input_ports {
        set name [lindex $port 0]
        if {$name ne $user_clk} {
            set pad [string repeat " " [expr {$max_name_len - [string length $name]}]]
            append dut_text "        DUT_virtual_interface.${name}${pad}    =   sequence_item.${name}${pad} ;\n"
        }
    }
    
    # --------- Build REF replacement text ---------
    set REF_text ""
    foreach port $input_ports {
        set name [lindex $port 0]
        if {$name ne $user_clk} {
            set pad [string repeat " " [expr {$max_name_len - [string length $name]}]]
            append REF_text "        REF_virtual_interface.${name}${pad}    =   sequence_item.${name}${pad} ;\n"
        }
    }
    
    # --------- Perform replacements ---------
    set new_data $data
    set new_data [string map [list "// virtual_interface_DUT_equal_sequence_item" $dut_text] $new_data]
    set new_data [string map [list "// virtual_interface_REF_equal_sequence_item" $REF_text] $new_data]
    
    # --------- Write modified data back ---------
    set fp [open $driver_file w]
    puts -nonewline $fp $new_data
    close $fp
    
    puts "Driver file updated successfully with DUT & REF assignments: $driver_file"
} else {
    # --------- driver_modify.tcl ---------
    # Edits each active agent's driver file (per-agent directory).
    
    if {![info exists project_name] || ![info exists path]} {
        puts "Error: project_name or path not defined."
        exit 1
    }
    
    set output_dir "${path}${project_name}_uvm/verif"
    set agent_dir  "${output_dir}/agent"
    
    proc modify_driver {driver_file in_ports u_clk} {
        if {![file exists $driver_file]} {
            puts "Warning: Driver file not found at $driver_file"
            return
        }
        set fp [open $driver_file r]; set data [read $fp]; close $fp
    
        set max_name_len 0
        foreach port $in_ports {
            set n [lindex $port 0]
            if {$n ne $u_clk} {
                set l [string length $n]
                if {$l > $max_name_len} { set max_name_len $l }
            }
        }
        set dut_text ""
        foreach port $in_ports {
            set name [lindex $port 0]
            if {$name ne $u_clk} {
                set pad [string repeat " " [expr {$max_name_len - [string length $name]}]]
                append dut_text "           DUT_virtual_interface.${name}${pad} = sequence_item.${name}${pad} ;\n"
            }
        }
        set golden_text ""
        foreach port $in_ports {
            set name [lindex $port 0]
            if {$name ne $u_clk} {
                set pad [string repeat " " [expr {$max_name_len - [string length $name]}]]
                append golden_text "           Golden_virtual_interface.${name}${pad} = sequence_item.${name}${pad} ;\n"
            }
        }
        set new_data [string map [list \
            "// virtual_interface_DUT_equal_sequence_item"    $dut_text \
            "// virtual_interface_Golden_equal_sequence_item" $golden_text] $data]
    
        set fp [open $driver_file w]; puts -nonewline $fp $new_data; close $fp
        puts "Driver updated: $driver_file"
    }
    
    if {$single_agent} {
        set in_ports [expr {[info exists input_ports_A1] && [llength $input_ports_A1] > 0 ? $input_ports_A1 : ( [info exists input_ports] ? $input_ports : {} )}]
        set clk_name [expr {[llength $in_ports] > 0 ? [lindex [lindex $in_ports 0] 0] : "clk"}]
        modify_driver "${agent_dir}/${project_name}_driver.sv" $in_ports $clk_name
    } else {
        for {set i 1} {$i <= $Num_AC_agent} {incr i} {
            set ai      [lindex $active_agent [expr {$i-1}]]
            set aname   [lindex $ai 0]
            set has_clk [lindex $ai 1]
            set in_var  "input_ports_A${i}"
            set in_ports [expr {[info exists $in_var] ? [set $in_var] : {}}]
            set clk_name [expr {$has_clk ? [lindex [lindex $in_ports 0] 0] : "clk"}]
            set fpath "${agent_dir}/Active/${aname}/${project_name}_${aname}_driver.sv"
            modify_driver $fpath $in_ports $clk_name
        }
    }
}
