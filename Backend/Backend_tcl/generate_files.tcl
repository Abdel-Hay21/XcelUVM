# ================================================
# generate_files.tcl
# ================================================

source lib_helpers.tcl
source lib_setup.tcl

if {$gm_type eq "RTL"} {
    source lib_rtl_generate.tcl
} else {
    if {$single_agent} {
        source lib_single_agent.tcl
    } else {
        source lib_multi_agent_agents.tcl
        source lib_multi_agent_env.tcl
    }
}

if {$Code_Coverage} {
    source "generate_run_do_CC.tcl"
} else {
    source "generate_run_do.tcl"
}
