# =====================================================================
# seq_item_modify.tcl
# =====================================================================

if {$gm_type eq "RTL"} {
    # =====================================================================
    # RTL MODE: Single seq_item file
    # =====================================================================
    
    if {![info exists project_name] || ![info exists path] || ![info exists sequence_list]} {
        puts "Error: project_name, path, or sequence_list not defined."
        exit 1
    }
    
    set output_dir  "${path}${project_name}_uvm/verif"
    set seq_item_file "${output_dir}/agent/${project_name}_seq_item.sv"
    
    if {![file exists $seq_item_file]} {
        puts "Error: seq_item file not found at $seq_item_file"
        exit 1
    }
    
    set fp   [open $seq_item_file r]
    set data [read $fp]
    close $fp
    
    set class_name "${project_name}_sequence_item"
    
    # ── Constraints Block ──────────────────────────────────────────────
    set constraints_block ""
    foreach seq_info $sequence_list {
        set seq_name [lindex $seq_info 0]
        append constraints_block \
    "     // Here write your ${seq_name} constraints\n" \
    "     // ${seq_name}_Constraint means the constraints that you want to apply to this sequence only\n" \
    "        constraint ${seq_name}_Constraint{\n" \
    "           // Here write your ${seq_name} Constraints\n" \
    "        }\n\n"
    }
    set constraints_block_trimmed [string trimright $constraints_block "\n"]
    set new_data [regsub {//\s*Here\s+write\s+your\s+User\s+constraints[^\n]*\n\s*//\s*USER_Constraint[^\n]*\n\s*constraint\s+USER_Constraint\s*\{[^\n]*\n\s*//[^\n]*\n\s*\}} $data $constraints_block_trimmed]
    
    # ── Calculate Maximum Lengths ──────────────────────────────────────
    set user_clk [expr {[llength $input_ports] > 0 ? [lindex [lindex $input_ports 0] 0] : "clk"}]
    set max_w_len 0
    set max_pname_len 0
    foreach port [concat $input_ports $output_ports] {
        set pname [lindex $port 0]
        if {$pname eq $user_clk} continue
        
        if {[string length $pname] > $max_pname_len} {
            set max_pname_len [string length $pname]
        }
        
        set width [lindex $port 1]
        if {$width > 1} {
            set w_str "\[[expr {$width - 1}]:0\]"
            if {[string length $w_str] > $max_w_len} {
                set max_w_len [string length $w_str]
            }
        }
    }
    
    # ── Generate Signals Block ─────────────────────────────────────────
    set signals_block ""
    foreach port $input_ports {
        set pname [lindex $port 0]
        set width [lindex $port 1]
        set type  [expr {[llength $port] >= 3 && [lindex $port 2] ne "" ? [lindex $port 2] : "bit"}]
        if {$pname eq $user_clk} continue
        
        set w_str ""
        if {$width > 1} { set w_str "\[[expr {$width - 1}]:0\]" }
        set w_pad [string repeat " " [expr {$max_w_len - [string length $w_str]}]]
        set p_pad [string repeat " " [expr {$max_pname_len - [string length $pname]}]]
        
        if {$max_w_len > 0} {
            append signals_block "      rand ${type}  ${w_str}${w_pad} ${pname}${p_pad} ;\n"
        } else {
            append signals_block "      rand ${type} ${pname}${p_pad} ;\n"
        }
    }
    
    foreach port $output_ports {
        set pname [lindex $port 0]
        set width [lindex $port 1]
        set type  [expr {[llength $port] >= 3 && [lindex $port 2] ne "" ? [lindex $port 2] : "bit"}]
        
        set w_str ""
        if {$width > 1} { set w_str "\[[expr {$width - 1}]:0\]" }
        set w_pad [string repeat " " [expr {$max_w_len - [string length $w_str]}]]
        set p_pad [string repeat " " [expr {$max_pname_len - [string length $pname]}]]
        
        if {$max_w_len > 0} {
            append signals_block "           ${type}  ${w_str}${w_pad} ${pname}${p_pad} ;\n"
        } else {
            append signals_block "           ${type} ${pname}${p_pad} ;\n"
        }
    }
    
    # ── Generate Field Macros Block ────────────────────────────────────
    set field_macros "     `uvm_object_utils_begin(${class_name})\n\n"
    set has_in 0
    foreach port $input_ports {
        set pname [lindex $port 0]
        if {$pname eq $user_clk} continue
        set p_pad [string repeat " " [expr {$max_pname_len - [string length $pname]}]]
        append field_macros "         `uvm_field_int(${pname}${p_pad}, UVM_ALL_ON)\n"
        set has_in 1
    }
    if {$has_in && [llength $output_ports] > 0} {
        append field_macros "\n"
    }
    foreach port $output_ports {
        set pname [lindex $port 0]
        set p_pad [string repeat " " [expr {$max_pname_len - [string length $pname]}]]
        append field_macros "         `uvm_field_int(${pname}${p_pad}, UVM_ALL_ON)\n"
    }
    append field_macros "\n     `uvm_object_utils_end"
    
    # Replace signals & field macros
    set new_data [string map [list \
        "// Here write your signals" [string trimright $signals_block "\n"] \
        "// Here write your field macros" $field_macros \
        "`uvm_object_utils(${class_name})" "" \
    ] $new_data]
    
    # Clean any leftover standalone `uvm_object_utils(...) if template had it
    set new_data [regsub -line {^[ \t]*`uvm_object_utils\([^\)]+\)[ \t]*\n} $new_data ""]
    
    # ── Generate convert2string Block ──────────────────────────────────
    set c2s_block "function string convert2string();\n"
    append c2s_block "        string s;\n"
    append c2s_block "        s = super.convert2string();\n"
    
    set args_list {}
    lappend args_list "\"\\n=================================================\\n\""
    lappend args_list "\"  Inputs:\\n\""
    
    foreach port $input_ports {
        set pname [lindex $port 0]
        set width [lindex $port 1]
        if {$pname eq $user_clk} continue
        set pad [string repeat " " [expr {$max_pname_len - [string length $pname]}]]
        set fmt [expr {$width == 1 ? "'b%0b" : "'h%0x"}]
        lappend args_list "\"    ${pname}${pad} = ${fmt}\\n\", ${pname}"
    }
    
    lappend args_list "\"  Outputs:\\n\""
    foreach port $output_ports {
        set pname [lindex $port 0]
        set width [lindex $port 1]
        set pad [string repeat " " [expr {$max_pname_len - [string length $pname]}]]
        set fmt [expr {$width == 1 ? "'b%0b" : "'h%0x"}]
        lappend args_list "\"    ${pname}${pad} = ${fmt}\\n\", ${pname}"
    }
    
    lappend args_list "\"=================================================\\n\""
    
    set max_arg_len 0
    foreach arg $args_list {
        set len [string length $arg]
        if {$len > $max_arg_len} {
            set max_arg_len $len
        }
    }
    
    foreach arg $args_list {
        set arg_pad [string repeat " " [expr {$max_arg_len - [string length $arg]}]]
        append c2s_block "        s = { s, \$sformatf(${arg}${arg_pad} ) };\n"
    }
    
    append c2s_block "        return s;\n"
    append c2s_block "     endfunction"
    
    set new_data [regsub {function\s+string\s+convert2string\(\);[^\n]*\n\s*return[^\n]*\n\s*endfunction} $new_data $c2s_block]
    
    set fp [open $seq_item_file w]
    puts -nonewline $fp $new_data
    close $fp
    
    puts "seq_item file updated successfully with constraints: $seq_item_file"

} else {
    # =====================================================================
    # SB MODE: Single or Multi-Agent seq_item files
    # =====================================================================
    
    if {![info exists project_name] || ![info exists path] || ![info exists sequence_list]} {
        puts "Error: project_name, path, or sequence_list not defined."
        exit 1
    }
    
    set output_dir  "${path}${project_name}_uvm/verif"
    set agent_dir   "${output_dir}/agent"
    
    # ── Helper: modify one seq_item file ──────────────────────────────────────
    proc modify_seq_item {file_path in_ports out_ports u_clk seq_list item_class_name} {
        if {![file exists $file_path]} {
            puts "Warning: seq_item file not found at $file_path"
            return
        }
        set fp [open $file_path r]; set data [read $fp]; close $fp
    
        # --- Constraints Block ---
        set constraints_block ""
        foreach seq_info $seq_list {
            set seq_name [lindex $seq_info 0]
            append constraints_block \
    "     // Here write your ${seq_name} constraints\n" \
    "     // ${seq_name}_Constraint means the constraints that you want to apply to this sequence only\n" \
    "        constraint ${seq_name}_Constraint{\n" \
    "           // Here write your ${seq_name} Constraints\n" \
    "        }\n\n"
        }
        set constraints_block_trimmed [string trimright $constraints_block "\n"]
        set new_data [regsub {//\s*Here\s+write\s+your\s+User\s+constraints[^\n]*\n\s*//\s*USER_Constraint[^\n]*\n\s*constraint\s+USER_Constraint\s*\{[^\n]*\n\s*//[^\n]*\n\s*\}} $data $constraints_block_trimmed]
    
        # --- Calculate Maximum Lengths ---
        set max_w_len 0; set max_pname_len 0
        foreach port [concat $in_ports $out_ports] {
            set pname [lindex $port 0]
            if {$pname eq $u_clk} continue
            if {[string length $pname] > $max_pname_len} { set max_pname_len [string length $pname] }
            set width [lindex $port 1]
            if {$width > 1} {
                set w_str "\[[expr {$width - 1}]:0\]"
                if {[string length $w_str] > $max_w_len} { set max_w_len [string length $w_str] }
            }
        }
        
        # --- Signals Block ---
        set signals_block ""
        foreach port $in_ports {
            set pname [lindex $port 0]; set width [lindex $port 1]
            set type  [expr {[llength $port] >= 3 && [lindex $port 2] ne "" ? [lindex $port 2] : "bit"}]
            if {$pname eq $u_clk} continue
            set w_str [expr {$width > 1 ? "\[[expr {$width-1}]:0\]" : ""}]
            set w_pad [string repeat " " [expr {$max_w_len - [string length $w_str]}]]
            set p_pad [string repeat " " [expr {$max_pname_len - [string length $pname]}]]
            if {$max_w_len > 0} {
                append signals_block "      rand ${type}  ${w_str}${w_pad} ${pname}${p_pad} ;\n"
            } else {
                append signals_block "      rand ${type} ${pname}${p_pad} ;\n"
            }
        }
        foreach port $out_ports {
            set pname [lindex $port 0]; set width [lindex $port 1]
            set type  [expr {[llength $port] >= 3 && [lindex $port 2] ne "" ? [lindex $port 2] : "bit"}]
            set w_str [expr {$width > 1 ? "\[[expr {$width-1}]:0\]" : ""}]
            set w_pad [string repeat " " [expr {$max_w_len - [string length $w_str]}]]
            set p_pad [string repeat " " [expr {$max_pname_len - [string length $pname]}]]
            if {$max_w_len > 0} {
                append signals_block "           ${type}  ${w_str}${w_pad} ${pname}${p_pad} ;\n"
            } else {
                append signals_block "           ${type} ${pname}${p_pad} ;\n"
            }
        }
        
        # --- Field Macros Block ---
        set field_macros "     `uvm_object_utils_begin(${item_class_name})\n\n"
        set has_in 0
        foreach port $in_ports {
            set pname [lindex $port 0]
            if {$pname eq $u_clk} continue
            set p_pad [string repeat " " [expr {$max_pname_len - [string length $pname]}]]
            append field_macros "         `uvm_field_int(${pname}${p_pad}, UVM_ALL_ON)\n"
            set has_in 1
        }
        if {$has_in && [llength $out_ports] > 0} {
            append field_macros "\n"
        }
        foreach port $out_ports {
            set pname [lindex $port 0]
            set p_pad [string repeat " " [expr {$max_pname_len - [string length $pname]}]]
            append field_macros "         `uvm_field_int(${pname}${p_pad}, UVM_ALL_ON)\n"
        }
        append field_macros "\n     `uvm_object_utils_end"
        
        # Replace signals & field macros
        set new_data [string map [list \
            "// Here write your signals" [string trimright $signals_block "\n"] \
            "// Here write your field macros" $field_macros \
            "`uvm_object_utils(${item_class_name})" "" \
        ] $new_data]
        
        # Clean any leftover standalone `uvm_object_utils(...) if template had it
        set new_data [regsub -line {^[ \t]*`uvm_object_utils\([^\)]+\)[ \t]*\n} $new_data ""]
        
        # --- convert2string Block ---
        set c2s_block "function string convert2string();\n"
        append c2s_block "        string s;\n"
        append c2s_block "        s = super.convert2string();\n"
        set args_list {}
        lappend args_list "\"\\n=================================================\\n\""
        lappend args_list "\"  Inputs:\\n\""
        foreach port $in_ports {
            set pname [lindex $port 0]; set width [lindex $port 1]
            if {$pname eq $u_clk} continue
            set pad [string repeat " " [expr {$max_pname_len - [string length $pname]}]]
            set fmt [expr {$width == 1 ? "'b%0b" : "'h%0x"}]
            lappend args_list "\"    ${pname}${pad} = ${fmt}\\n\", ${pname}"
        }
        lappend args_list "\"  Outputs:\\n\""
        foreach port $out_ports {
            set pname [lindex $port 0]; set width [lindex $port 1]
            set pad [string repeat " " [expr {$max_pname_len - [string length $pname]}]]
            set fmt [expr {$width == 1 ? "'b%0b" : "'h%0x"}]
            lappend args_list "\"    ${pname}${pad} = ${fmt}\\n\", ${pname}"
        }
        lappend args_list "\"=================================================\\n\""
        set max_arg_len 0
        foreach arg $args_list { if {[string length $arg] > $max_arg_len} { set max_arg_len [string length $arg] } }
        foreach arg $args_list {
            set arg_pad [string repeat " " [expr {$max_arg_len - [string length $arg]}]]
            append c2s_block "        s = { s, \$sformatf(${arg}${arg_pad} ) };\n"
        }
        append c2s_block "        return s;\n"
        append c2s_block "     endfunction"
        set new_data [regsub {function\s+string\s+convert2string\(\);[^\n]*\n\s*return[^\n]*\n\s*endfunction} $new_data $c2s_block]
    
        set fp [open $file_path w]; puts -nonewline $fp $new_data; close $fp
        puts "seq_item updated: $file_path"
    }
    
    # ── Dispatch per agent ──────────────────────────────────────────────────────
    if {$single_agent} {
        set in_ports  [expr {[info exists input_ports_A1] && [llength $input_ports_A1] > 0 ? $input_ports_A1 : ( [info exists input_ports] ? $input_ports : {} )}]
        set out_ports [expr {[info exists output_ports_A1] && [llength $output_ports_A1] > 0 ? $output_ports_A1 : ( [info exists output_ports] ? $output_ports : {} )}]
        set clk_name  [expr {[llength $in_ports] > 0 ? [lindex [lindex $in_ports 0] 0] : "clk"}]
        modify_seq_item "${agent_dir}/${project_name}_seq_item.sv" $in_ports $out_ports $clk_name $sequence_list "${project_name}_sequence_item"
    } else {
        # Active agents
        for {set i 1} {$i <= $Num_AC_agent} {incr i} {
            set ai      [lindex $active_agent [expr {$i-1}]]
            set aname   [lindex $ai 0]
            set has_clk [lindex $ai 1]
            set in_var  "input_ports_A${i}"
            set out_var "output_ports_A${i}"
            set in_ports  [expr {[info exists $in_var]  ? [set $in_var]  : {}}]
            set out_ports [expr {[info exists $out_var] ? [set $out_var] : {}}]
            set clk_name  [expr {$has_clk ? [lindex [lindex $in_ports 0] 0] : "clk"}]
            set fpath "${agent_dir}/Active/${aname}/${project_name}_${aname}_seq_item.sv"
            modify_seq_item $fpath $in_ports $out_ports $clk_name $sequence_list "${project_name}_${aname}_sequence_item"
        }
        # Passive agents
        for {set i 1} {$i <= $Num_PA_agent} {incr i} {
            set pi      [lindex $passive_agent [expr {$i-1}]]
            set pname   [lindex $pi 0]
            set has_clk [lindex $pi 1]
            set in_var  "input_ports_P${i}"
            set out_var "output_ports_P${i}"
            set in_ports  [expr {[info exists $in_var]  ? [set $in_var]  : {}}]
            set out_ports [expr {[info exists $out_var] ? [set $out_var] : {}}]
            set clk_name  [expr {$has_clk ? [lindex [lindex $in_ports 0] 0] : "clk"}]
            set fpath "${agent_dir}/Passive/${pname}/${project_name}_${pname}_seq_item.sv"
            modify_seq_item $fpath $in_ports $out_ports $clk_name $sequence_list "${project_name}_${pname}_sequence_item"
        }
    }
}
