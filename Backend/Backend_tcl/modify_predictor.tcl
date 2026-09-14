# modify_predictor.tcl
if {$gm_type ne "SB"} return

# =====================================================================
# modify_predictor.tcl
# In multi-agent mode: Transforms the generic predictor into a multi-port
# component that receives from all agents and predicts expected outputs.
# Uses string map / regsub to modify the template file directly.
# =====================================================================

if {![info exists project_name] || ![info exists path]} {
    puts "Error: project_name or path not defined."
    exit 1
}

if {![info exists sb_language] || $sb_language eq ""} { set sb_language "SV" }

set output_dir "${path}${project_name}_uvm/verif"
set pred_file  "${output_dir}/environment/${project_name}_predictor.sv"
set ref_filename "${project_name}_reference_model.sv"

if {![file exists "${output_dir}/reference_model/${project_name}_reference_model.sv"]} {
    set ref_filename "${project_name}_reference_model_proxy.sv"
}

if {![file exists $pred_file]} {
    puts "Warning: Predictor file not found at $pred_file"
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

set fp [open $pred_file r]; set data [read $fp]; close $fp

if {$single_agent} {
    # Single-agent mode: Just rename the reference model type if needed (for SV mode)
    if {$sb_language eq "SV"} {
        set data [string map [list "reference_model REF;" "${project_name}_reference_model REF;"] $data]
        set data [string map [list "REF = reference_model::type_id::create" "REF = ${project_name}_reference_model::type_id::create"] $data]
    }
    set fp [open $pred_file w]; puts -nonewline $fp $data; close $fp
    return
}

# ─── MULTI-AGENT MODE ──────────────────────────────────────────────────────

# 1. Imports
set imports ""
foreach ag_name $all_agents {
    append imports "   import ${project_name}_${ag_name}_sequence_item_pkg::*;\n"
}
set search_imports "   import ${project_name}_sequence_item_pkg::*;"
set data [string map [list $search_imports $imports] $data]


# 2. Macros & Class Inheritance
set macros ""
foreach ag_name $all_agents {
    append macros "   \`uvm_analysis_imp_decl(_${ag_name})\n"
}
set search_class "   class ${project_name}_predictor extends uvm_subscriber #(${project_name}_sequence_item);"
set data [string map [list $search_class "${macros}\n   class ${project_name}_predictor extends uvm_component;"] $data]

# --- Calculate Max Lengths for Alignment ---
proc pad {str len} {
    set pad_len [expr {$len - [string length $str]}]
    if {$pad_len < 0} { set pad_len 0 }
    return "${str}[string repeat " " $pad_len]"
}

set max_imp_prefix 0
set max_imp_inner 0
set max_item_len 0
set max_ex_inst 0
set max_po_inst 0
foreach ag_name $all_agents {
    set item_type "${project_name}_${ag_name}_sequence_item"
    set imp_prefix "uvm_analysis_imp_${ag_name}"
    set imp_inner "${item_type}, ${project_name}_predictor"
    set ex_inst "${ag_name}_export"
    set po_inst "expected_${ag_name}_port"
    
    if {[string length $imp_prefix] > $max_imp_prefix} { set max_imp_prefix [string length $imp_prefix] }
    if {[string length $imp_inner] > $max_imp_inner} { set max_imp_inner [string length $imp_inner] }
    if {[string length $item_type] > $max_item_len} { set max_item_len [string length $item_type] }
    if {[string length $ex_inst] > $max_ex_inst} { set max_ex_inst [string length $ex_inst] }
    if {[string length $po_inst] > $max_po_inst} { set max_po_inst [string length $po_inst] }
}

# 3. Ports Declarations
set decls ""
set ports ""
append decls "      // Analysis Import for Each Agent\n"
append ports "      // Analysis Port for Expected Transaction\n"
foreach ag_name $all_agents {
    set item_type "${project_name}_${ag_name}_sequence_item"
    set imp_prefix "uvm_analysis_imp_${ag_name}"
    set imp_inner "${item_type}, ${project_name}_predictor"
    
    append decls "         [pad $imp_prefix $max_imp_prefix] #( [pad $imp_inner $max_imp_inner] ) [pad "${ag_name}_export" $max_ex_inst] ;\n"
    append ports "         uvm_analysis_port #( [pad $item_type $max_item_len] ) [pad "expected_${ag_name}_port" $max_po_inst] ;\n"
}
set search_ports "// Analysis Port for Expected Transaction\n         uvm_analysis_port #(${project_name}_sequence_item) expected_port;"
set data [string map [list $search_ports "${decls}\n${ports}"] $data]

# 4. Reference Model / Proxy Type Rename
if {$sb_language eq "SV"} {
    set data [string map [list "reference_model REF;" "${project_name}_reference_model REF;"] $data]
    set data [string map [list "REF = reference_model::type_id::create" "REF = ${project_name}_reference_model::type_id::create"] $data]
}

# 5. Build Phase (Create Ports)
set creates_ex ""
set creates_po ""
foreach ag_name $all_agents {
    append creates_ex "         [pad "${ag_name}_export" $max_ex_inst] = new([pad "\"${ag_name}_export\"" [expr {$max_ex_inst + 2}]], this);\n"
    append creates_po "         [pad "expected_${ag_name}_port" $max_po_inst] = new([pad "\"expected_${ag_name}_port\"" [expr {$max_po_inst + 2}]], this);\n"
}
set search_build "         expected_port = new(\"expected_port\", this);"
set data [string map [list $search_build "         // Exports from Monitors\n${creates_ex}\n         // Ports to Scoreboard\n${creates_po}"] $data]

# 6. Write Functions
set ref_target [expr {$sb_language eq "C" ? "REF_proxy" : "REF"}]
set write_funcs ""
foreach ag_name $all_agents {
    set item_type "${project_name}_${ag_name}_sequence_item"
    append write_funcs "      //------------------------------------------------------------\n"
    append write_funcs "      // Write ${ag_name}\n"
    append write_funcs "      //------------------------------------------------------------\n"
    append write_funcs "      function void write_${ag_name}(${item_type} t);\n"
    append write_funcs "         ${item_type} expected_transaction;\n"
    append write_funcs "         \`uvm_info(\"PREDICTOR\", {\"Received Actual Transaction from ${ag_name} Monitor:\\n\", t.convert2string()}, UVM_HIGH)\n"
    append write_funcs "         expected_transaction = ${ref_target}.execute_${ag_name}(t);\n"
    append write_funcs "         expected_${ag_name}_port.write(expected_transaction);\n"
    append write_funcs "      endfunction\n\n"
}
set data [regsub -all {\n[ \t]*//-+\n[ \t]*// Write\n[ \t]*//-+\n.*?endfunction} $data "\n${write_funcs}"]

set fp [open $pred_file w]
puts -nonewline $fp $data
close $fp
puts "Unified Predictor updated: $pred_file"
