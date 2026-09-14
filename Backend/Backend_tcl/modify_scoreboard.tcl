# --------- modify_scoreboard.tcl ---------
if {$gm_type eq "RTL"} {
    # =====================================================================
    # RTL MODE: Scoreboard
    # =====================================================================
    
    if {![info exists project_name] || ![info exists path] || ![info exists output_ports]} {
        puts "Error: project_name, path, or output_ports not defined."
        exit 1
    }
    
    set scoreboard_file "${path}${project_name}_uvm/verif/environment/${project_name}_scoreboard.sv"
    
    if {![file exists $scoreboard_file]} {
        puts "Error: Scoreboard file not found at $scoreboard_file"
        exit 1
    }
    
    # Find maximum length of port names for alignment
    set max_port_len 0
    foreach port_info $output_ports {
        set port_name [lindex $port_info 0]
        set len [string length $port_name]
        if {$len > $max_port_len} {
            set max_port_len $len
        }
    }
    
    # Construct the equality checks for outputs only
    set port_checks {}
    foreach port_info $output_ports {
        set port_name [lindex $port_info 0]
        set left_side "DUT_sequence_item.${port_name}"
        set right_side "REF_sequence_item.${port_name}"
        
        # Pad left side
        set padding [string repeat " " [expr {$max_port_len - [string length $port_name]}]]
        
        lappend port_checks "(${left_side}${padding} == ${right_side})"
    }
    
    if {[llength $port_checks] > 0} {
        set combined_check [join $port_checks " &&\n               "]
    } else {
        set combined_check "1 /* No output ports defined */"
    }
    
    # Read the scoreboard file
    set fp [open $scoreboard_file r]
    set data [read $fp]
    close $fp
    
    # Replace the target comment with the combined check
    set new_data [string map [list \
        "/* Output_REF == Output_DUT*/"    $combined_check \
        "/* Golden_Output == DUT_Output*/" $combined_check \
        "/* Output_Golden == Output_DUT*/" $combined_check \
        "DUT_sequence_item.compare(REF_sequence_item)" $combined_check] $data]
    
    # Write back to the scoreboard file
    set fp [open $scoreboard_file w]
    puts -nonewline $fp $new_data
    close $fp
    
    puts "Scoreboard file updated successfully with dynamic port comparisons."

} else {
    # =====================================================================
    # SB MODE: Scoreboard (Single Agent or Multi-Agent)
    # =====================================================================
    
    if {![info exists project_name] || ![info exists path]} {
        puts "Error: project_name or path not defined."
        exit 1
    }
    
    set output_dir "${path}${project_name}_uvm/verif"
    set env_dir    "${output_dir}/environment"
    set sb_file    "${env_dir}/${project_name}_scoreboard.sv"
    
    if {![file exists $sb_file]} {
        puts "Warning: Scoreboard file not found at $sb_file"
        return
    }
    
    if {$single_agent} {
        # ── SINGLE AGENT MODE ─────────────────────────────────────────────
        set out_ports [expr {[info exists output_ports_A1] && [llength $output_ports_A1] > 0 ? $output_ports_A1 : ( [info exists output_ports] ? $output_ports : {} )}]
        
        set max_port_len 0
        foreach port_info $out_ports {
            set port_name [lindex $port_info 0]
            set len [string length $port_name]
            if {$len > $max_port_len} {
                set max_port_len $len
            }
        }
        
        set port_checks {}
        foreach port_info $out_ports {
            set port_name [lindex $port_info 0]
            set left_side "DUT_sequence_item.${port_name}"
            set right_side "REF_sequence_item.${port_name}"
            set padding [string repeat " " [expr {$max_port_len - [string length $port_name]}]]
            lappend port_checks "(${left_side}${padding} == ${right_side})"
        }
        
        if {[llength $port_checks] > 0} {
            set combined_check [join $port_checks " &&\n                   "]
        } else {
            set combined_check "1 /* No output ports defined */"
        }
        
        set fp [open $sb_file r]; set data [read $fp]; close $fp
        set new_data [string map [list \
            "/* Output_Golden == Output_DUT*/" $combined_check \
            "/* Golden_Output == DUT_Output*/" $combined_check \
            "/* Output_REF == Output_DUT*/"    $combined_check \
            "DUT_sequence_item.compare(REF_sequence_item)" $combined_check] $data]
        set fp [open $sb_file w]; puts -nonewline $fp $new_data; close $fp
        puts "Scoreboard updated: $sb_file"
    
    } else {
        # ── MULTI-AGENT MODE: Unified Scoreboard ──────────────────────────
        set fp [open $sb_file r]; set data [read $fp]; close $fp
    
        # Build the imports
        set imports ""
        for {set i 1} {$i <= $Num_AC_agent} {incr i} {
            set aname [lindex [lindex $active_agent [expr {$i-1}]] 0]
            append imports "   import ${project_name}_${aname}_sequence_item_pkg::*;\n"
        }
        for {set i 1} {$i <= $Num_PA_agent} {incr i} {
            set pname [lindex [lindex $passive_agent [expr {$i-1}]] 0]
            append imports "   import ${project_name}_${pname}_sequence_item_pkg::*;\n"
        }
    
        # Calculate Max Lengths for Alignment
        set all_agents {}
        for {set i 1} {$i <= $Num_AC_agent} {incr i} { lappend all_agents [lindex [lindex $active_agent [expr {$i-1}]] 0] }
        for {set i 1} {$i <= $Num_PA_agent} {incr i} { lappend all_agents [lindex [lindex $passive_agent [expr {$i-1}]] 0] }
    
        set max_type_len 0
        set max_ag_len 0
        foreach ag_name $all_agents {
            set item_type "${project_name}_${ag_name}_sequence_item"
            if {[string length $item_type] > $max_type_len} { set max_type_len [string length $item_type] }
            if {[string length $ag_name] > $max_ag_len} { set max_ag_len [string length $ag_name] }
        }
        proc pad {str len} {
            set pad_len [expr {$len - [string length $str]}]
            if {$pad_len < 0} { set pad_len 0 }
            return "${str}[string repeat " " $pad_len]"
        }
    
        # Build declarations for ports, fifos, and items
        set dut_decls ""
        set dut_fifo ""
        set ref_decls ""
        set ref_fifo ""
        set item_decls ""
        set build_phase_DUT ""
        set build_phase_REF ""
        set connect_phase ""
        set run_get ""
        set checks ""
    
        # Helper for adding agent logic
        proc add_agent_to_sb {ag_name out_ports} {
            upvar 1 dut_decls dut_decls
            upvar 1 dut_fifo dut_fifo
            upvar 1 ref_decls ref_decls
            upvar 1 ref_fifo ref_fifo
            upvar 1 item_decls item_decls
            upvar 1 build_phase_DUT build_phase_DUT
            upvar 1 build_phase_REF build_phase_REF
            upvar 1 connect_phase connect_phase
            upvar 1 run_get run_get
            upvar 1 checks checks
            upvar 1 project_name project_name
            upvar 1 max_type_len max_type_len
            upvar 1 max_ag_len max_ag_len
    
            set item_type "${project_name}_${ag_name}_sequence_item"
            set dut_exp_name "DUT_${ag_name}_export"
            set dut_fifo_name "DUT_${ag_name}_fifo"
            set ref_exp_name "REF_${ag_name}_export"
            set ref_fifo_name "REF_${ag_name}_fifo"
            
            set dut_item_name "DUT_${ag_name}_item"
            set ref_item_name "REF_${ag_name}_item"
    
            set max_exp_name [expr {11 + $max_ag_len}]
            set max_fifo_name [expr {9 + $max_ag_len}]
            set max_item_name [expr {9 + $max_ag_len}]
    
            # 1. Declarations
            append dut_decls "         uvm_analysis_export   #( [pad $item_type $max_type_len] ) [pad $dut_exp_name $max_exp_name]  ;\n"
            append dut_fifo  "         uvm_tlm_analysis_fifo #( [pad $item_type $max_type_len] ) [pad $dut_fifo_name $max_exp_name]  ;\n"
            append ref_decls "         uvm_analysis_export   #( [pad $item_type $max_type_len] ) [pad $ref_exp_name $max_exp_name]  ;\n"
            append ref_fifo  "         uvm_tlm_analysis_fifo #( [pad $item_type $max_type_len] ) [pad $ref_fifo_name $max_exp_name]  ;\n"
            
            append item_decls "         [pad $item_type $max_type_len]   [pad $dut_item_name $max_item_name]  ;\n"
            append item_decls "         [pad $item_type $max_type_len]   [pad $ref_item_name $max_item_name]  ;\n"
    
            # 2. Build phase (new)
            append build_phase_DUT "               [pad $dut_exp_name $max_exp_name] = new([pad "\"$dut_exp_name\"" [expr {$max_exp_name + 2}]], this);\n"
            append build_phase_DUT "               [pad $dut_fifo_name $max_exp_name] = new([pad "\"$dut_fifo_name\"" [expr {$max_exp_name + 2}]], this);\n"
            append build_phase_REF "               [pad $ref_exp_name $max_exp_name] = new([pad "\"$ref_exp_name\"" [expr {$max_exp_name + 2}]], this);\n"
            append build_phase_REF "               [pad $ref_fifo_name $max_exp_name] = new([pad "\"$ref_fifo_name\"" [expr {$max_exp_name + 2}]], this);\n"
    
            # 3. Connect phase
            set max_fifo_export_len [expr {$max_fifo_name + 16}] ; # length of `DUT_xxxx_fifo.analysis_export`
            set fifo_exp_dut "${dut_fifo_name}.analysis_export"
            set fifo_exp_ref "${ref_fifo_name}.analysis_export"
            
            append connect_phase "         [pad $dut_exp_name $max_exp_name] .connect  ( [pad $fifo_exp_dut $max_fifo_export_len] );\n"
            append connect_phase "         [pad $ref_exp_name $max_exp_name] .connect  ( [pad $fifo_exp_ref $max_fifo_export_len] );\n"
    
            # 4. Run phase (get)
            append run_get "               [pad $dut_fifo_name $max_exp_name] .get  ( [pad $dut_item_name $max_item_name]   );\n"
            append run_get "               [pad $ref_fifo_name $max_exp_name] .get  ( [pad $ref_item_name $max_item_name]   );\n"
    
            # 5. Output comparison checks
            set max_port_len 0
            foreach port_info $out_ports {
                set port_name [lindex $port_info 0]
                set len [string length $port_name]
                if {$len > $max_port_len} { set max_port_len $len }
            }
            
            set port_checks {}
            foreach port_info $out_ports {
                set port_name [lindex $port_info 0]
                set left_side "DUT_${ag_name}_item.${port_name}"
                set right_side "REF_${ag_name}_item.${port_name}"
                set padding [string repeat " " [expr {$max_port_len - [string length $port_name]}]]
                lappend port_checks "(${left_side}${padding} == ${right_side})"
            }
            
            if {[llength $port_checks] > 0} {
                set combined_check [join $port_checks " &&\n                   "]
            } else {
                set combined_check "1 /* No output ports for ${ag_name} */"
            }
            
            append checks "               if (${combined_check}) begin\n"
            append checks "                   correct_count++;\n"
            append checks "               end else begin\n"
            append checks "                   error_count++;\n"
            append checks "                   `uvm_error(\"run_phase\", \$sformatf(\"Time:%0t  In: ${ag_name} --> comparison failed\", \$time));\n"
            append checks "               end\n\n"
        }
    
        for {set i 1} {$i <= $Num_AC_agent} {incr i} {
            set aname   [lindex [lindex $active_agent [expr {$i-1}]] 0]
            set out_var "output_ports_A${i}"
            set out_ports [expr {[info exists $out_var] ? [set $out_var] : {}}]
            add_agent_to_sb $aname $out_ports
        }
        for {set i 1} {$i <= $Num_PA_agent} {incr i} {
            set pname   [lindex [lindex $passive_agent [expr {$i-1}]] 0]
            set out_var "output_ports_P${i}"
            set out_ports [expr {[info exists $out_var] ? [set $out_var] : {}}]
            add_agent_to_sb $pname $out_ports
        }
    
        # Execute text replacements
        # 1. Imports
        set data [regsub -line "^\[ \t\]*import ${project_name}_sequence_item_pkg::\\*;\[ \t\]*\\r?\\n" $data $imports]
        
        # 2. Declarations
        set search_dut "// Define analysis Port & tlm_fifo for DUT (Actual)\n         uvm_analysis_export   #(${project_name}_sequence_item) DUT_export     ;\n         uvm_tlm_analysis_fifo #(${project_name}_sequence_item) DUT_fifo       ;"
        set data [string map [list $search_dut "// Define analysis Ports & tlm_fifos for DUT (Actual)\n${dut_decls}${dut_fifo}"] $data]
        
        set search_ref "// Define analysis Port & tlm_fifo for REF (Expected)\n         uvm_analysis_export   #(${project_name}_sequence_item) REF_export     ;\n         uvm_tlm_analysis_fifo #(${project_name}_sequence_item) REF_fifo       ;"
        set data [string map [list $search_ref "// Define analysis Ports & tlm_fifos for REF (Expected)\n${ref_decls}${ref_fifo}"] $data]
        
        set search_items "// sequence_items for DUT and REF\n         ${project_name}_sequence_item DUT_sequence_item    ;\n         ${project_name}_sequence_item REF_sequence_item    ;"
        set data [string map [list $search_items "// sequence_items for DUT and REF\n${item_decls}"] $data]
        
        # 3. Build phase
        set search_build_dut "         // DUT\n            DUT_export    = new(\"DUT_export\"     , this);\n            DUT_fifo      = new(\"DUT_fifo\"       , this);"
        set search_build_ref "         // REF\n            REF_export    = new(\"REF_export\"     , this);\n            REF_fifo      = new(\"REF_fifo\"       , this);"
        set data [string map [list $search_build_dut "" $search_build_ref "         // Create all ports and fifos\n            // DUT\n${build_phase_DUT}\n            // REF\n${build_phase_REF}"] $data]
        
        # 4. Connect phase
        set search_connect "         DUT_export.connect(DUT_fifo.analysis_export);\n         REF_export.connect(REF_fifo.analysis_export);"
        set data [string map [list $search_connect $connect_phase] $data]
        
        # 5. Run phase
        set search_get "               DUT_fifo.get(DUT_sequence_item);\n               REF_fifo.get(REF_sequence_item);"
        set data [string map [list $search_get $run_get] $data]
        
        # 6. Comparisons
        set search_compare "            // Compare the outputs\n               if(/* Golden_Output == DUT_Output*/)\n               begin\n                   correct_count++;       \n               end\n               else begin\n                   error_count++;\n                   \`uvm_error(\"run_phase\", \$sformatf(\"Time:%0t  In: ${project_name} --> comparison failed\", \$time));\n               end"
        set data [string map [list $search_compare "            // Compare the outputs for all agents\n${checks}"] $data]
    
        # Save
        set fp [open $sb_file w]; puts -nonewline $fp $data; close $fp
        puts "Unified Scoreboard updated: $sb_file"
    }
}
