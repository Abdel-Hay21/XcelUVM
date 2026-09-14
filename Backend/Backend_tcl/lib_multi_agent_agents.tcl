# ================================================
# lib_multi_agent_agents.tcl
# MULTI-AGENT mode — Part 1: per-agent files.
# ================================================

set agent_dir "${output_dir}/agent"
file mkdir "${agent_dir}/Active"
file mkdir "${agent_dir}/Passive"

proc pad {str len} {
    set pad_len [expr {$len - [string length $str]}]
    if {$pad_len < 0} { set pad_len 0 }
    return "${str}[string repeat " " $pad_len]"
}

# ── ACTIVE AGENTS ──────────────────────────────────────────────────
for {set i 1} {$i <= $Num_AC_agent} {incr i} {
    set ai      [lindex $active_agent [expr {$i-1}]]
    set aname   [lindex $ai 0]
    set has_clk [lindex $ai 1]
    set in_var  "input_ports_A${i}"
    set out_var "output_ports_A${i}"
    set a_in    [expr {[info exists $in_var]  ? [set $in_var]  : {}}]
    set a_out   [expr {[info exists $out_var] ? [set $out_var] : {}}]
    set a_clk   [expr {$has_clk ? [lindex [lindex $a_in 0] 0] : "clk"}]

    set active_ag_dir "${agent_dir}/Active/${aname}"
    file mkdir $active_ag_dir

    set data [read_template $template_dir seq_item $project_name $a_clk $suffix]
    set data [string map [list \
        "${project_name}_sequence_item_pkg" "${project_name}_${aname}_sequence_item_pkg" \
        "${project_name}_sequence_item"     "${project_name}_${aname}_sequence_item"] $data]
    write_file "${active_ag_dir}/${project_name}_${aname}_seq_item.sv" $data

    set data [read_template $template_dir sequencer $project_name $a_clk $suffix]
    set data [string map [list \
        "${project_name}_sequence_item_pkg" "${project_name}_${aname}_sequence_item_pkg" \
        "${project_name}_sequence_item"     "${project_name}_${aname}_sequence_item" \
        "${project_name}_sequencer_pkg"     "${project_name}_${aname}_sequencer_pkg" \
        "${project_name}_sequencer"         "${project_name}_${aname}_sequencer"] $data]
    write_file "${active_ag_dir}/${project_name}_${aname}_sequencer.sv" $data

    set data [read_template $template_dir driver $project_name $a_clk $suffix]
    set data [string map [list \
        "${project_name}_sequence_item_pkg" "${project_name}_${aname}_sequence_item_pkg" \
        "${project_name}_sequence_item"     "${project_name}_${aname}_sequence_item" \
        "${project_name}_driver_pkg"        "${project_name}_${aname}_driver_pkg" \
        "${project_name}_driver"            "${project_name}_${aname}_driver" \
        "${project_name}_interface"         "${project_name}_${aname}_interface"] $data]
    write_file "${active_ag_dir}/${project_name}_${aname}_driver.sv" $data

    set data [read_template $template_dir monitor $project_name $a_clk $suffix]
    set data [string map [list \
        "${project_name}_sequence_item_pkg" "${project_name}_${aname}_sequence_item_pkg" \
        "${project_name}_sequence_item"     "${project_name}_${aname}_sequence_item" \
        "${project_name}_monitor_pkg"       "${project_name}_${aname}_monitor_pkg" \
        "${project_name}_monitor"           "${project_name}_${aname}_monitor" \
        "${project_name}_interface"         "${project_name}_${aname}_interface"] $data]
    write_file "${active_ag_dir}/${project_name}_${aname}_monitor.sv" $data

    set data [read_template $template_dir agent $project_name $a_clk $suffix]
    set data [string map [list \
        "${project_name}_sequence_item_pkg" "${project_name}_${aname}_sequence_item_pkg" \
        "${project_name}_sequence_item"     "${project_name}_${aname}_sequence_item" \
        "${project_name}_sequencer_pkg"     "${project_name}_${aname}_sequencer_pkg" \
        "${project_name}_sequencer"         "${project_name}_${aname}_sequencer" \
        "${project_name}_driver_pkg"        "${project_name}_${aname}_driver_pkg" \
        "${project_name}_driver"            "${project_name}_${aname}_driver" \
        "${project_name}_monitor_pkg"       "${project_name}_${aname}_monitor_pkg" \
        "${project_name}_monitor"           "${project_name}_${aname}_monitor" \
        "${project_name}_agent_pkg"         "${project_name}_${aname}_agent_pkg" \
        "${project_name}_agent"             "${project_name}_${aname}_agent" \
        "${project_name}_interface"         "${project_name}_${aname}_interface" \
        "cfg.DUT_virtual_interface"         "cfg.${aname}_virtual_interface" \
        "is_active = UVM_ACTIVE"            "is_active = UVM_ACTIVE"] $data]

    set type_seq "${project_name}_${aname}_sequencer"
    set type_drv "${project_name}_${aname}_driver"
    set type_mon "${project_name}_${aname}_monitor"
    set type_cfg "${project_name}_config"
    set max_type_len [string length $type_seq]
    if {[string length $type_drv] > $max_type_len} { set max_type_len [string length $type_drv] }
    if {[string length $type_mon] > $max_type_len} { set max_type_len [string length $type_mon] }
    if {[string length $type_cfg] > $max_type_len} { set max_type_len [string length $type_cfg] }
    
    set data [regsub -line "(\[ \\t\]*)${type_seq}\[ \\t\]+sequencer\[ \\t\]*;" $data "\\1[pad $type_seq $max_type_len]    sequencer ;"]
    set data [regsub -line "(\[ \\t\]*)${type_drv}\[ \\t\]+driver\[ \\t\]*;" $data "\\1[pad $type_drv $max_type_len]    driver    ;"]
    set data [regsub -line "(\[ \\t\]*)${type_mon}\[ \\t\]+monitor\[ \\t\]*;" $data "\\1[pad $type_mon $max_type_len]    monitor   ;"]
    set data [regsub -line "(\[ \\t\]*)${type_cfg}\[ \\t\]+cfg\[ \\t\]*;" $data "\\1[pad $type_cfg $max_type_len]    cfg       ;"]

    write_file "${active_ag_dir}/${project_name}_${aname}_agent.sv" $data
}

# ── PASSIVE AGENTS ─────────────────────────────────────────────────
for {set i 1} {$i <= $Num_PA_agent} {incr i} {
    set pi      [lindex $passive_agent [expr {$i-1}]]
    set pname   [lindex $pi 0]
    set has_clk [lindex $pi 1]
    set in_var  "input_ports_P${i}"
    set out_var "output_ports_P${i}"
    set p_in    [expr {[info exists $in_var]  ? [set $in_var]  : {}}]
    set p_out   [expr {[info exists $out_var] ? [set $out_var] : {}}]
    set p_clk   [expr {$has_clk ? [lindex [lindex $p_in 0] 0] : "clk"}]

    set passive_ag_dir "${agent_dir}/Passive/${pname}"
    file mkdir $passive_ag_dir

    set data [read_template $template_dir seq_item $project_name $p_clk $suffix]
    set data [string map [list \
        "${project_name}_sequence_item_pkg" "${project_name}_${pname}_sequence_item_pkg" \
        "${project_name}_sequence_item"     "${project_name}_${pname}_sequence_item"] $data]
    set data [regsub -all {\n[ \t]*// Here write your Global constraints[ \t]*\n[ \t]*// Global_Constraint[^\n]*\n[ \t]*constraint Global_Constraint\{.*?\}} $data ""]
    write_file "${passive_ag_dir}/${project_name}_${pname}_seq_item.sv" $data

    set data [read_template $template_dir monitor $project_name $p_clk $suffix]
    set data [string map [list \
        "${project_name}_sequence_item_pkg" "${project_name}_${pname}_sequence_item_pkg" \
        "${project_name}_sequence_item"     "${project_name}_${pname}_sequence_item" \
        "${project_name}_monitor_pkg"       "${project_name}_${pname}_monitor_pkg" \
        "${project_name}_monitor"           "${project_name}_${pname}_monitor" \
        "${project_name}_interface"         "${project_name}_${pname}_interface"] $data]
    write_file "${passive_ag_dir}/${project_name}_${pname}_monitor.sv" $data

    set data [read_template $template_dir agent $project_name $p_clk $suffix]
    set data [string map [list \
        "${project_name}_sequence_item_pkg" "${project_name}_${pname}_sequence_item_pkg" \
        "${project_name}_sequence_item"     "${project_name}_${pname}_sequence_item" \
        "${project_name}_sequencer_pkg"     "${project_name}_${pname}_sequencer_pkg" \
        "${project_name}_sequencer"         "${project_name}_${pname}_sequencer" \
        "${project_name}_driver_pkg"        "${project_name}_${pname}_driver_pkg" \
        "${project_name}_driver"            "${project_name}_${pname}_driver" \
        "${project_name}_monitor_pkg"       "${project_name}_${pname}_monitor_pkg" \
        "${project_name}_monitor"           "${project_name}_${pname}_monitor" \
        "${project_name}_agent_pkg"         "${project_name}_${pname}_agent_pkg" \
        "${project_name}_agent"             "${project_name}_${pname}_agent" \
        "${project_name}_interface"         "${project_name}_${pname}_interface" \
        "cfg.DUT_virtual_interface"         "cfg.${pname}_virtual_interface" \
        "is_active = UVM_ACTIVE"            "is_active = UVM_PASSIVE"] $data]

    set type_mon "${project_name}_${pname}_monitor"
    set type_cfg "${project_name}_config"
    set max_type_len [string length $type_mon]
    if {[string length $type_cfg] > $max_type_len} { set max_type_len [string length $type_cfg] }
    
    set data [regsub -line "(\[ \\t\]*)${type_mon}\[ \\t\]+monitor\[ \\t\]*;" $data "\\1[pad $type_mon $max_type_len]    monitor   ;"]
    set data [regsub -line "(\[ \\t\]*)${type_cfg}\[ \\t\]+cfg\[ \\t\]*;" $data "\\1[pad $type_cfg $max_type_len]    cfg       ;"]

    set data [regsub -all -line {^import [A-Za-z0-9_]+_sequencer_pkg::\*;[ \t]*\r?$\n} $data ""]
    set data [regsub -all -line {^import [A-Za-z0-9_]+_driver_pkg::\*;[ \t]*\r?$\n} $data ""]
    set data [regsub -all -line {^[ \t]+[A-Za-z0-9_]+_sequencer[ \t]+sequencer[ \t]*;[ \t]*\r?$\n} $data ""]
    set data [regsub -all -line {^[ \t]+[A-Za-z0-9_]+_driver[ \t]+driver[ \t]*;[ \t]*\r?$\n} $data ""]
    
    set build_block "    if( is_active == UVM_ACTIVE ) begin\n      sequencer  = ${project_name}_${pname}_sequencer:: type_id:: create(\"sequencer\",this);\n      driver     = ${project_name}_${pname}_driver::    type_id:: create(\"driver\"   ,this);\n    end"
    set connect_block "     // Driver and Sequencer Connection\n       if(is_active == UVM_ACTIVE) begin\n         // Interface\n            driver.DUT_virtual_interface = cfg.${pname}_virtual_interface;\n         // Transaction   \n            driver.seq_item_port.connect(sequencer.seq_item_export);\n       end"
    set data [string map [list $build_block "" $connect_block ""] $data]
    write_file "${passive_ag_dir}/${project_name}_${pname}_agent.sv" $data
}
