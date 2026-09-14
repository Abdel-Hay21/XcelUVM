# modify_coverage.tcl
if {$gm_type ne "SB"} return

# =====================================================================
# modify_coverage.tcl
# In multi-agent mode: ONE unified coverage component.
# The coverage component receives all transactions from all agents.
# =====================================================================

if {![info exists project_name] || ![info exists path]} {
    puts "Error: project_name or path not defined."
    exit 1
}

set output_dir "${path}${project_name}_uvm/verif"
set env_dir    "${output_dir}/environment"
set cov_file   "${env_dir}/${project_name}_coverage.sv"

if {![file exists $cov_file]} {
    puts "Warning: Coverage file not found at $cov_file"
    return
}

# Collect all agents
set all_agents {}
for {set i 1} {$i <= $Num_AC_agent} {incr i} {
    lappend all_agents [lindex [lindex $active_agent [expr {$i-1}]] 0]
}
for {set i 1} {$i <= $Num_PA_agent} {incr i} {
    lappend all_agents [lindex [lindex $passive_agent [expr {$i-1}]] 0]
}

if {$single_agent} {
    # Single agent: nothing structural to change, it works as is
    return
}

# MULTI-AGENT MODE
set fp [open $cov_file r]; set data [read $fp]; close $fp

# Build the imports
set imports ""
foreach ag_name $all_agents {
    append imports "   import ${project_name}_${ag_name}_sequence_item_pkg::*;\n"
}

set decls ""
set item_decls ""
set build_phase ""
set connect_phase ""
set run_get ""

foreach ag_name $all_agents {
    set item_type "${project_name}_${ag_name}_sequence_item"
    append decls "       uvm_analysis_export   #(${item_type}) ${ag_name}_export ;\n"
    append decls "       uvm_tlm_analysis_fifo #(${item_type}) ${ag_name}_fifo   ;\n"
    
    append item_decls "       ${item_type} ${ag_name}_item;\n"

    append build_phase "     ${ag_name}_export = new(\"${ag_name}_export\", this);\n"
    append build_phase "     ${ag_name}_fifo   = new(\"${ag_name}_fifo\"  , this);\n"

    append connect_phase "     ${ag_name}_export.connect(${ag_name}_fifo.analysis_export);\n"

    append run_get "       ${ag_name}_fifo.get(${ag_name}_item);\n"
}
append run_get "       cover_group.sample();\n"

# 1. Imports
set data [regsub -line {^[ \t]*import templete_sequence_item_pkg::\*;[ \t]*\r?$\n} $data $imports]

# 2. Declarations
set search_decl "// Define analysis export & tlm_fifo\n       uvm_analysis_export   #(templete_sequence_item) export ;\n       uvm_tlm_analysis_fifo #(templete_sequence_item) fifo   ;"
set data [string map [list $search_decl "// Define analysis export & tlm_fifo for all agents\n${decls}"] $data]

set search_items "// sequence_item\n       templete_sequence_item sequence_item;"
set data [string map [list $search_items "// sequence_items\n${item_decls}"] $data]

# 3. Build phase
set search_build "     export = new(\"export\", this);\n     fifo   = new(\"fifo\"  , this);"
set data [string map [list $search_build $build_phase] $data]

# 4. Connect phase
set search_connect "     export.connect(fifo.analysis_export);"
set data [string map [list $search_connect $connect_phase] $data]

# 5. Run phase
set search_run "       fifo.get(sequence_item);\n       cover_group.sample();"
set data [string map [list $search_run $run_get] $data]

set fp [open $cov_file w]; puts -nonewline $fp $data; close $fp
puts "Unified Coverage updated: $cov_file"
