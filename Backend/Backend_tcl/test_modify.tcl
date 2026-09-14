# =====================================================================
# test_modify.tcl
if {$gm_type eq "RTL"} {
    # =====================================================================
    # test_modify.tcl
    # Reads sequence_list from run.tcl (already in scope via source)
    # Replaces the single "my" placeholder in templete_test with one
    # block per sequence, keeping all = and ; signs column-aligned.
    # =====================================================================
    
    # --------- Verify prerequisites ---------
    if {![info exists project_name] || ![info exists path] || ![info exists sequence_list]} {
        puts "Error: project_name, path, or sequence_list not defined."
        exit 1
    }
    
    set output_dir  "${path}${project_name}_uvm/verif"
    set test_file   "${output_dir}/test/${project_name}_test.sv"
    
    if {![file exists $test_file]} {
        puts "Error: Test file not found at $test_file"
        exit 1
    }
    
    # --------- Read generated test file ---------
    set fp   [open $test_file r]
    set data [read $fp]
    close $fp
    
    # =====================================================================
    # Helper: pad a string on the RIGHT to a given total width
    # =====================================================================
    proc rpad {str width} {
        set len [string length $str]
        if {$len >= $width} { return $str }
        return "${str}[string repeat { } [expr {$width - $len}]]"
    }
    
    # =====================================================================
    # Pre-compute column widths for perfect alignment
    # We need the longest versions of several fields:
    #
    #   seq_type   = ${project_name}_${SeqName}_sequence
    #   seq_var    = ${SeqName}_sequence
    #   seq_handle = ${project_name}_${SeqName}_sequence::
    # =====================================================================
    set max_type_len   0   ;# width of "${project}_${SeqName}_sequence"
    set max_var_len    0   ;# width of "${SeqName}_sequence"
    set max_handle_len 0   ;# width of "${project}_${SeqName}_sequence::"
    set max_msg_len    0   ;# width of "${SeqName} Asserted"
    set max_iter_len   0   ;# width of iteration number
    
    foreach seq_info $sequence_list {
        set seq [lindex $seq_info 0]
        set iter [lindex $seq_info 1]
        set type_str   "${project_name}_${seq}_sequence"
        set var_str    "${seq}_sequence"
        set handle_str "${project_name}_${seq}_sequence::"
        set msg_str    "\"${seq} Deasserted\""
    
        if {[string length $type_str]   > $max_type_len}   { set max_type_len   [string length $type_str]   }
        if {[string length $var_str]    > $max_var_len}    { set max_var_len    [string length $var_str]    }
        if {[string length $handle_str] > $max_handle_len} { set max_handle_len [string length $handle_str] }
        if {[string length $msg_str]    > $max_msg_len}    { set max_msg_len    [string length $msg_str]    }
        if {[string length $iter]       > $max_iter_len}   { set max_iter_len   [string length $iter]       }
    }
    
    # =====================================================================
    # Build the three replacement blocks
    # =====================================================================
    
    # ── 1. Variable declarations (replace: templete_my_sequence     my_seq;) ──
    set decl_block ""
    foreach seq_info $sequence_list {
        set seq [lindex $seq_info 0]
        set type_str  "${project_name}_${seq}_sequence"
        set var_str   "${seq}_sequence"
        
        set type_pad  [rpad $type_str  $max_type_len]
        set var_pad   [rpad $var_str   $max_var_len]
        
        append decl_block "     ${type_pad}  ${var_pad} ;\n"
    }
    
    # ── 2. type_id::create lines (replace: my_seq = templete_my_sequence:: type_id:: create(...)) ──
    # Extra left padding to match the env_wrapper line already in the file ("    env_wrapper      = ...")
    set create_block ""
    set max_create_str_len [expr {$max_var_len + 2}] ;# add 2 for quotes
    foreach seq_info $sequence_list {
        set seq [lindex $seq_info 0]
        set var_str    "${seq}_sequence"
        set handle_str "${project_name}_${seq}_sequence::"
        set create_str "\"${seq}_sequence\""
    
        set var_pad    [rpad $var_str    $max_var_len]
        set handle_pad [rpad $handle_str $max_handle_len]
        set create_str_pad [rpad $create_str $max_create_str_len]
    
        append create_block \
            "       ${var_pad} =    ${handle_pad} type_id:: create(${create_str_pad} ,this);\n"
    }
    
    # ── 3. run_phase blocks (replace: // my sequence ... uvm_info x3 lines) ──
    set run_block ""
    foreach seq_info $sequence_list {
        set seq [lindex $seq_info 0]
        set var_str  "${seq}_sequence"
        set assert_msg   "\"${seq} Asserted\""
        set deassert_msg "\"${seq} Deasserted\""
        set assert_pad   [rpad $assert_msg   $max_msg_len]
        set deassert_pad [rpad $deassert_msg $max_msg_len]
    
        append run_block \
            "    // ${seq} sequence\n" \
            "       \`uvm_info(\"run_phase\", ${assert_pad} , UVM_LOW)\n" \
            "        ${var_str}.start(environment.agent.sequencer);     \n" \
            "       \`uvm_info(\"run_phase\", ${deassert_pad} , UVM_LOW)\n" \
            "\n"
    }
    
    # ── 4. Repeat numbers (replace: my_seq.repeat_number = TAKE_NUM_FROM_USER ;) ──
    set repeat_block ""
    set max_repeat_var_len [expr {$max_var_len + 14}] ;# ".repeat_number" is 14 chars
    foreach seq_info $sequence_list {
        set seq  [lindex $seq_info 0]
        set iter [lindex $seq_info 1]
        set var_str "${seq}_sequence.repeat_number"
        set var_pad [rpad $var_str $max_repeat_var_len]
        set iter_pad [rpad $iter $max_iter_len]
        append repeat_block "       ${var_pad} = ${iter_pad} ;\n"
    }
    
    # ── 5. Import packages (replace: import ${project_name}_sequence_pkg::*; ) ──
    set import_block ""
    foreach seq_info $sequence_list {
        set seq [lindex $seq_info 0]
        append import_block "import ${project_name}_${seq}_sequence_pkg::*;\n"
    }
    
    # =====================================================================
    # Perform replacements in the generated file
    # =====================================================================
    
    # The single placeholder lines/blocks inserted by generate_files.tcl
    # still carry the word "my" (inherited from the template).
    # We target the exact patterns that survive after the templete→project
    # substitution done by generate_files.tcl.
    
    # -- Declaration line --
    set new_data [regsub \
        "${project_name}_my_sequence\\s+my_seq;" \
        $data \
        $decl_block]
    
    # -- create line (within build_phase) --
    set new_data [regsub \
        "my_seq\\s+=\\s+${project_name}_my_sequence::\\s+type_id:: create\\(\"my_seq\"\\s*,this\\);" \
        $new_data \
        $create_block]
    
    # -- run_phase block --
    set new_data [regsub \
        "// my sequence\[^\n\]*\n\\s+\`uvm_info\[^\n\]*\n\\s+my_seq\\.start\[^\n\]*\n\\s+\`uvm_info\[^\n\]*\n" \
        $new_data \
        $run_block]
    
    # -- repeat_number block --
    set new_data [regsub \
        "\\s+my_seq\\.repeat_number\\s*=\\s*TAKE_NUM_FROM_USER\\s*;" \
        $new_data \
        "\n$repeat_block"]
    
    # -- import block --
    set new_data [regsub \
        "import ${project_name}_sequence_pkg::\\*;" \
        $new_data \
        [string trimright $import_block "\n"]]
    
    # =====================================================================
    # Write back
    # =====================================================================
    set fp [open $test_file w]
    puts -nonewline $fp $new_data
    close $fp
    
    puts "Test file updated successfully: $test_file"
} else {
    # =====================================================================
    # test_modify.tcl
    # =====================================================================
    
    if {![info exists project_name] || ![info exists path] || ![info exists sequence_list]} {
        puts "Error: project_name, path, or sequence_list not defined."
        exit 1
    }
    
    set output_dir  "${path}${project_name}_uvm/verif"
    set test_file   "${output_dir}/test/${project_name}_test.sv"
    
    if {![file exists $test_file]} {
        puts "Error: Test file not found at $test_file"
        exit 1
    }
    
    set fp   [open $test_file r]
    set data [read $fp]
    close $fp
    
    proc rpad {str width} {
        set len [string length $str]
        if {$len >= $width} { return $str }
        return "${str}[string repeat { } [expr {$width - $len}]]"
    }
    
    set max_type_len   0
    set max_var_len    0
    set max_handle_len 0
    set max_msg_len    0
    set max_iter_len   0
    
    # Build a flattened list of {agent_prefix sequence_name iter}
    set expanded_seqs {}
    
    if {$single_agent} {
        foreach seq_info $sequence_list {
            lappend expanded_seqs [list "" [lindex $seq_info 0] [lindex $seq_info 1]]
        }
    } else {
        for {set i 1} {$i <= $Num_AC_agent} {incr i} {
            set aname [lindex [lindex $active_agent [expr {$i-1}]] 0]
            foreach seq_info $sequence_list {
                lappend expanded_seqs [list "${aname}_" [lindex $seq_info 0] [lindex $seq_info 1]]
            }
        }
    }
    
    foreach seq_info $expanded_seqs {
        set aprefix [lindex $seq_info 0]
        set seq     [lindex $seq_info 1]
        set iter    [lindex $seq_info 2]
        
        set type_str   "${project_name}_${aprefix}${seq}_sequence"
        set var_str    "${aprefix}${seq}_sequence"
        set handle_str "${project_name}_${aprefix}${seq}_sequence::"
        set msg_str    "\"${aprefix}${seq} Deasserted\""
    
        if {[string length $type_str]   > $max_type_len}   { set max_type_len   [string length $type_str]   }
        if {[string length $var_str]    > $max_var_len}    { set max_var_len    [string length $var_str]    }
        if {[string length $handle_str] > $max_handle_len} { set max_handle_len [string length $handle_str] }
        if {[string length $msg_str]    > $max_msg_len}    { set max_msg_len    [string length $msg_str]    }
        if {[string length $iter]       > $max_iter_len}   { set max_iter_len   [string length $iter]       }
    }
    
    # ── 1. Variable declarations ──
    set decl_block ""
    foreach seq_info $expanded_seqs {
        set aprefix [lindex $seq_info 0]
        set seq     [lindex $seq_info 1]
        set type_str  "${project_name}_${aprefix}${seq}_sequence"
        set var_str   "${aprefix}${seq}_sequence"
        set type_pad  [rpad $type_str  $max_type_len]
        set var_pad   [rpad $var_str   $max_var_len]
        append decl_block "     ${type_pad}  ${var_pad} ;\n"
    }
    
    # ── 2. type_id::create lines ──
    set create_block ""
    set max_create_str_len [expr {$max_var_len + 2}]
    foreach seq_info $expanded_seqs {
        set aprefix [lindex $seq_info 0]
        set seq     [lindex $seq_info 1]
        set var_str    "${aprefix}${seq}_sequence"
        set handle_str "${project_name}_${aprefix}${seq}_sequence::"
        set create_str "\"${aprefix}${seq}_sequence\""
        set var_pad    [rpad $var_str    $max_var_len]
        set handle_pad [rpad $handle_str $max_handle_len]
        set create_str_pad [rpad $create_str $max_create_str_len]
        append create_block "       ${var_pad} =    ${handle_pad} type_id:: create(${create_str_pad} ,this);\n"
    }
    
    # ── 3. run_phase blocks ──
    set run_block ""
    foreach seq_info $sequence_list {
        set seq [lindex $seq_info 0]
        
        append run_block "    // ${seq} sequence\n"
        
        if {$single_agent} {
            set assert_msg   "\"${seq} Asserted\""
            set deassert_msg "\"${seq} Deasserted\""
            set assert_pad   [rpad $assert_msg   $max_msg_len]
            set deassert_pad [rpad $deassert_msg $max_msg_len]
            set var_str  "${seq}_sequence"
    
            append run_block "       \`uvm_info(\"run_phase\", ${assert_pad} , UVM_LOW)\n"
            append run_block "        ${var_str}.start(environment.agent.sequencer);     \n"
            append run_block "       \`uvm_info(\"run_phase\", ${deassert_pad} , UVM_LOW)\n\n"
        } else {
            set assert_msg   "\"${seq} Asserted\""
            set deassert_msg "\"${seq} Deasserted\""
            set assert_pad   [rpad $assert_msg   $max_msg_len]
            set deassert_pad [rpad $deassert_msg $max_msg_len]
            
            append run_block "       \`uvm_info(\"run_phase\", ${assert_pad} , UVM_LOW)\n"
            append run_block "        fork\n"
            for {set i 1} {$i <= $Num_AC_agent} {incr i} {
                set aname [lindex [lindex $active_agent [expr {$i-1}]] 0]
                set var_str  "${aname}_${seq}_sequence"
                append run_block "           ${var_str}.start(environment.${aname}_agent.sequencer);\n"
            }
            append run_block "        join\n"
            append run_block "       \`uvm_info(\"run_phase\", ${deassert_pad} , UVM_LOW)\n\n"
        }
    }
    
    # ── 4. Repeat numbers ──
    set repeat_block ""
    set max_repeat_var_len [expr {$max_var_len + 14}]
    foreach seq_info $expanded_seqs {
        set aprefix [lindex $seq_info 0]
        set seq  [lindex $seq_info 1]
        set iter [lindex $seq_info 2]
        set var_str "${aprefix}${seq}_sequence.repeat_number"
        set var_pad [rpad $var_str $max_repeat_var_len]
        set iter_pad [rpad $iter $max_iter_len]
        append repeat_block "       ${var_pad} = ${iter_pad} ;\n"
    }
    
    # ── 5. Import sequences packages ──
    set import_block ""
    foreach seq_info $expanded_seqs {
        set aprefix [lindex $seq_info 0]
        set seq [lindex $seq_info 1]
        append import_block "import ${project_name}_${aprefix}${seq}_sequence_pkg::*;\n"
    }
    
    # ── 6. Import agent packages (multi-agent replaces single agent/sequencer imports) ──
    if {$single_agent} {
        set agent_import_old  "import ${project_name}_agent_pkg::*;"
        set agent_import_new  "import ${project_name}_agent_pkg::*;"
        set seq_import_old    "import ${project_name}_sequencer_pkg::*;"
        set seq_import_new    "import ${project_name}_sequencer_pkg::*;"
    } else {
        # Build multi-agent imports: one per active agent (agent + sequencer)
        set agent_import_old  "import ${project_name}_agent_pkg::*;"
        set agent_import_new  ""
        for {set i 1} {$i <= $Num_AC_agent} {incr i} {
            set aname [lindex [lindex $active_agent [expr {$i-1}]] 0]
            append agent_import_new "import ${project_name}_${aname}_agent_pkg::*;\n"
        }
        for {set i 1} {$i <= $Num_PA_agent} {incr i} {
            set pname [lindex [lindex $passive_agent [expr {$i-1}]] 0]
            append agent_import_new "import ${project_name}_${pname}_agent_pkg::*;\n"
        }
        set agent_import_new [string trimright $agent_import_new "\n"]
    
        # Sequencer imports: only active agents have sequencers
        set seq_import_old  "import ${project_name}_sequencer_pkg::*;"
        set seq_import_new  ""
        for {set i 1} {$i <= $Num_AC_agent} {incr i} {
            set aname [lindex [lindex $active_agent [expr {$i-1}]] 0]
            append seq_import_new "import ${project_name}_${aname}_sequencer_pkg::*;\n"
        }
        set seq_import_new [string trimright $seq_import_new "\n"]
    }
    
    # Perform replacements
    set new_data [regsub "${project_name}_my_sequence\\s+my_seq;" $data $decl_block]
    set new_data [regsub "my_seq\\s+=\\s+${project_name}_my_sequence::\\s+type_id:: create\\(\"my_seq\"\\s*,this\\);" $new_data $create_block]
    set new_data [regsub "// my sequence\[^\n\]*\n\\s+\`uvm_info\[^\n\]*\n\\s+my_seq\\.start\[^\n\]*\n\\s+\`uvm_info\[^\n\]*\n" $new_data $run_block]
    set new_data [regsub "\\s+my_seq\\.repeat_number\\s*=\\s*TAKE_NUM_FROM_USER\\s*;" $new_data "\n$repeat_block"]
    set new_data [regsub "import ${project_name}_sequence_pkg::\\*;" $new_data [string trimright $import_block "\n"]]
    set new_data [string map [list $agent_import_old $agent_import_new] $new_data]
    set new_data [string map [list $seq_import_old   $seq_import_new]   $new_data]
    
    set fp [open $test_file w]
    puts -nonewline $fp $new_data
    close $fp
    
    puts "Test file updated successfully: $test_file"
}
