# ================================================
# lib_multi_agent_env.tcl
# MULTI-AGENT mode — Part 2: shared environment-level files.
# ================================================

set sb_data [read_template $template_dir scoreboard $project_name $user_clk $suffix]
write_file "${output_dir}/environment/${project_name}_scoreboard.sv" $sb_data

if {![info exists sb_language] || $sb_language eq ""} { set sb_language "SV" }
set lang_lower [string tolower $sb_language]
switch -glob -- $lang_lower {
    "sv*" {
        set pred_tmpl "predictor_v"
    }
    "c*" {
        set pred_tmpl "predictor_c"
    }
    "py*" -
    "ex*" -
    default {
        set pred_tmpl "predictor_ex"
    }
}
set pred_data [read_template $template_dir $pred_tmpl $project_name $user_clk]
write_file "${output_dir}/environment/${project_name}_predictor.sv" $pred_data

if {$c_flag} {
    set cov_data [read_template $template_dir coverage $project_name $user_clk]
    write_file "${output_dir}/environment/${project_name}_coverage.sv" $cov_data
}

switch -glob -- $lang_lower {
    "sv*" {
        set ref_src "${template_dir}/reference_model_v.sv"
        set ref_dst "${output_dir}/reference_model/${project_name}_reference_model.sv"
    }
    "c*" {
        set ref_src "${template_dir}/reference_model_proxy_c.sv"
        set ref_dst "${output_dir}/reference_model/${project_name}_reference_model_proxy.sv"
    }
    "py*" -
    "ex*" -
    default {
        set ref_src "${template_dir}/reference_model_proxy_ex.sv"
        set ref_dst "${output_dir}/reference_model/SV/${project_name}_reference_model_proxy.sv"
    }
}
set fh [open $ref_src r]; set ref_data [read $fh]; close $fh
set ref_data [string map [list templete $project_name USER_CLK $user_clk] $ref_data]
write_file $ref_dst $ref_data

set env_data [read_template $template_dir environment $project_name $user_clk $suffix]

set env_imports ""
if {$c_flag} {
    append env_imports "  import ${project_name}_coverage_pkg::*;\n"
}
for {set i 1} {$i <= $Num_AC_agent} {incr i} {
    set aname [lindex [lindex $active_agent [expr {$i-1}]] 0]
    append env_imports "  import ${project_name}_${aname}_agent_pkg::*;\n"
}
for {set i 1} {$i <= $Num_PA_agent} {incr i} {
    set pname [lindex [lindex $passive_agent [expr {$i-1}]] 0]
    append env_imports "  import ${project_name}_${pname}_agent_pkg::*;\n"
}

set all_agents {}
for {set i 1} {$i <= $Num_AC_agent} {incr i} { lappend all_agents [lindex [lindex $active_agent [expr {$i-1}]] 0] }
for {set i 1} {$i <= $Num_PA_agent} {incr i} { lappend all_agents [lindex [lindex $passive_agent [expr {$i-1}]] 0] }

set max_type_len [string length "${project_name}_scoreboard"]
set max_inst_len [string length "scoreboard"]
foreach ag_name $all_agents {
    set type_len [string length "${project_name}_${ag_name}_agent"]
    set inst_len [string length "${ag_name}_agent"]
    if {$type_len > $max_type_len} { set max_type_len $type_len }
    if {$inst_len > $max_inst_len} { set max_inst_len $inst_len }
}

set agent_decls ""
append agent_decls "        [pad "${project_name}_predictor" $max_type_len]  [pad "predictor" $max_inst_len] ;\n"
append agent_decls "        [pad "${project_name}_scoreboard" $max_type_len]  [pad "scoreboard" $max_inst_len] ;\n"
if {$c_flag} {
    append agent_decls "        [pad "${project_name}_coverage" $max_type_len]  [pad "coverage" $max_inst_len] ; // Case_NO_Coverage\n"
}
foreach ag_name $all_agents {
    append agent_decls "        [pad "${project_name}_${ag_name}_agent" $max_type_len]  [pad "${ag_name}_agent" $max_inst_len] ;\n"
}

set agent_creates ""
append agent_creates "        [pad "predictor" $max_inst_len] = [pad "${project_name}_predictor::" [expr {$max_type_len + 2}]] type_id::create([pad "\"predictor\"" [expr {$max_inst_len + 2}]], this);\n"
append agent_creates "        [pad "scoreboard" $max_inst_len] = [pad "${project_name}_scoreboard::" [expr {$max_type_len + 2}]] type_id::create([pad "\"scoreboard\"" [expr {$max_inst_len + 2}]], this);\n"
if {$c_flag} {
    append agent_creates "        [pad "coverage" $max_inst_len] = [pad "${project_name}_coverage::" [expr {$max_type_len + 2}]] type_id::create([pad "\"coverage\"" [expr {$max_inst_len + 2}]], this); // Case_NO_Coverage\n"
}
foreach ag_name $all_agents {
    append agent_creates "        [pad "${ag_name}_agent" $max_inst_len] = [pad "${project_name}_${ag_name}_agent::" [expr {$max_type_len + 2}]] type_id::create([pad "\"${ag_name}_agent\"" [expr {$max_inst_len + 2}]], this);\n"
}

set agent_connects ""
for {set i 1} {$i <= $Num_AC_agent} {incr i} {
    set aname [lindex [lindex $active_agent [expr {$i-1}]] 0]
    append agent_connects "        // ${aname} (Active) → Predictor, Scoreboard, Coverage\n"
    append agent_connects "           ${aname}_agent.DUT_analysis_port.connect(predictor.${aname}_export);\n"
    append agent_connects "           ${aname}_agent.DUT_analysis_port.connect(scoreboard.DUT_${aname}_export);\n"
    append agent_connects "           predictor.expected_${aname}_port.connect(scoreboard.REF_${aname}_export);\n"
    if {$c_flag} {
        append agent_connects "           ${aname}_agent.DUT_analysis_port.connect(coverage.${aname}_export); // Case_NO_Coverage\n"
    }
    append agent_connects "\n"
}
for {set i 1} {$i <= $Num_PA_agent} {incr i} {
    set pname [lindex [lindex $passive_agent [expr {$i-1}]] 0]
    append agent_connects "        // ${pname} (Passive) → Predictor, Scoreboard, Coverage\n"
    append agent_connects "           ${pname}_agent.DUT_analysis_port.connect(predictor.${pname}_export);\n"
    append agent_connects "           ${pname}_agent.DUT_analysis_port.connect(scoreboard.DUT_${pname}_export);\n"
    append agent_connects "           predictor.expected_${pname}_port.connect(scoreboard.REF_${pname}_export);\n"
    if {$c_flag} {
        append agent_connects "           ${pname}_agent.DUT_analysis_port.connect(coverage.${pname}_export); // Case_NO_Coverage\n"
    }
    append agent_connects "\n"
}

set env_data [string map [list "  import ${project_name}_agent_pkg::*;" $env_imports] $env_data]

set old_decls \
"        ${project_name}_agent      agent      ;
        ${project_name}_predictor  predictor  ;
        ${project_name}_scoreboard scoreboard ;
        ${project_name}_coverage   coverage   ;  // Case_NO_Coverage"
set env_data [string map [list $old_decls [string trimright $agent_decls]] $env_data]

set old_creates \
"        agent       =  ${project_name}_agent::      type_id:: create(\"agent\"     , this);
        predictor   =  ${project_name}_predictor::  type_id:: create(\"predictor\" , this);
        scoreboard  =  ${project_name}_scoreboard:: type_id:: create(\"scoreboard\", this);
        coverage    =  ${project_name}_coverage::   type_id:: create(\"coverage\"  , this); // Case_NO_Coverage"
set env_data [string map [list $old_creates [string trimright $agent_creates]] $env_data]

set old_connect \
"        // Predictor: Connect Monitor to Predictor\n           agent.DUT_analysis_port.connect(predictor.analysis_export);\n\n        // Scoreboard: Connect Monitor to Scoreboard (DUT/Actual)\n           agent.DUT_analysis_port.connect(scoreboard.DUT_export);\n\n        // Scoreboard: Connect Predictor to Scoreboard (REF/Expected)\n           predictor.expected_port.connect(scoreboard.REF_export);\n\n        // Coverage: connect Monitor to Coverage // Case_NO_Coverage\n           agent.DUT_analysis_port.connect(coverage.export         ); // Case_NO_Coverage"
set env_data [string map [list $old_connect $agent_connects] $env_data]

write_file "${output_dir}/environment/${project_name}_environment.sv" $env_data

source [file join [file dirname [info script]] lib_multi_agent_test_top.tcl]
