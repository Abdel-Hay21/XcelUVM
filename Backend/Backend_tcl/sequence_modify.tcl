# =====================================================================
# sequence_modify.tcl
if {$gm_type eq "RTL"} {
    # =====================================================================
    # sequence_modify.tcl
    # =====================================================================
    
    if {![info exists project_name] || ![info exists path] || ![info exists sequence_list]} {
        puts "Error: project_name, path, or sequence_list not defined."
        exit 1
    }
    
    set output_dir       "${path}${project_name}_uvm/verif"
    set sequence_dir     "${output_dir}/sequences/sequences"
    
    # Loop over all sequences to modify their generated files
    foreach current_sequence_info $sequence_list {
        set current_sequence [lindex $current_sequence_info 0]
        set sequence_file "${sequence_dir}/${project_name}_${current_sequence}_sequence.sv"
        
        if {![file exists $sequence_file]} {
            puts "Warning: sequence file not found: $sequence_file"
            continue
        }
    
        set fp   [open $sequence_file r]
        set data [read $fp]
        close $fp
    
        # Build the replacement block for this specific sequence file
        set modes_block ""
        foreach sequence_info $sequence_list {
            set sequence_name [lindex $sequence_info 0]
            
            if {$sequence_name eq $current_sequence} {
                set mode 1
            } else {
                set mode 0
            }
            
            append modes_block "          sequence_item.${sequence_name}_Constraint.constraint_mode(${mode});\n"
        }
        
        set modes_block_trimmed [string trimright $modes_block "\n"]
        set target_string "          sequence_item.USER_Constraint.constraint_mode(1_OR_0);"
        
        set new_data [string map [list $target_string $modes_block_trimmed] $data]
    
        set fp [open $sequence_file w]
        puts -nonewline $fp $new_data
        close $fp
        
        puts "Sequence file updated with constraint modes: $sequence_file"
    }
} else {
    # =====================================================================
    # sequence_modify.tcl
    # =====================================================================
    
    if {![info exists project_name] || ![info exists path] || ![info exists sequence_list]} {
        puts "Error: project_name, path, or sequence_list not defined."
        exit 1
    }
    
    set output_dir       "${path}${project_name}_uvm/verif"
    set sequence_dir     "${output_dir}/sequences/sequences"
    
    # Helper procedure to modify a single sequence file
    proc modify_sequence_file {seq_file current_sequence sequence_list} {
        if {![file exists $seq_file]} {
            puts "Warning: sequence file not found: $seq_file"
            return
        }
    
        set fp   [open $seq_file r]
        set data [read $fp]
        close $fp
    
        # Build the replacement block for this specific sequence file
        set modes_block ""
        foreach sequence_info $sequence_list {
            set sequence_name [lindex $sequence_info 0]
            
            if {$sequence_name eq $current_sequence} {
                set mode 1
            } else {
                set mode 0
            }
            
            append modes_block "          sequence_item.${sequence_name}_Constraint.constraint_mode(${mode});\n"
        }
        
        set modes_block_trimmed [string trimright $modes_block "\n"]
        set target_string "          sequence_item.USER_Constraint.constraint_mode(1_OR_0);"
        
        set new_data [string map [list $target_string $modes_block_trimmed] $data]
    
        set fp [open $seq_file w]
        puts -nonewline $fp $new_data
        close $fp
        
        puts "Sequence file updated with constraint modes: $seq_file"
    }
    
    # Loop over all sequences to modify their generated files
    foreach current_sequence_info $sequence_list {
        set current_sequence [lindex $current_sequence_info 0]
        
        if {$single_agent} {
            set sequence_file "${sequence_dir}/${project_name}_${current_sequence}_sequence.sv"
            modify_sequence_file $sequence_file $current_sequence $sequence_list
        } else {
            # Multi-agent mode: modify per-agent sequences
            global Num_AC_agent active_agent
            for {set i 1} {$i <= $Num_AC_agent} {incr i} {
                set aname [lindex [lindex $active_agent [expr {$i-1}]] 0]
                set sequence_file "${sequence_dir}/${project_name}_${aname}_${current_sequence}_sequence.sv"
                modify_sequence_file $sequence_file $current_sequence $sequence_list
            }
        }
    }
}
