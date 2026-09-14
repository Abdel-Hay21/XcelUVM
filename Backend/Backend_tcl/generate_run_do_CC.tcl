# =====================================================================
# generate_run_do_CC.tcl
# =====================================================================

if {![info exists project_name] || ![info exists path] || ![info exists dut_module]} { exit 1 }

if {![info exists assertions]}  { set assertions "false" }
if {![info exists coverage]}    { set coverage "false" }
if {![info exists sb_language]} { set sb_language "SV" }

set output_dir  "${path}${project_name}_uvm/test"
set do_file     "${output_dir}/run.do"
if {![file exists $output_dir]} { file mkdir $output_dir }

set a_flag [expr {($assertions eq "true" || $assertions eq 1 || $assertions eq "True") ? 1 : 0}]
set c_flag [expr {($coverage   eq "true" || $coverage   eq 1 || $coverage   eq "True") ? 1 : 0}]

set lang_lower [string tolower $sb_language]
set is_python  [expr {[string match "py*" $lang_lower] || [string match "ex*" $lang_lower]}]
set is_c       [expr {[string match "c*" $lang_lower]}]

set fp [open $do_file w]

puts $fp "# QuestaSim compilation & execution script (Code Coverage)"
puts $fp "vlib work\nvmap work work\n"

if {$gm_type eq "SB" && $is_python} {
    puts $fp "# 0. Start Python Reference Model Server in Background"
    puts $fp "puts \"\\\[QuestaSim\\\] Starting Python Reference Model Server...\""
    puts $fp "catch {exec python ../verif/reference_model/python/server.py &}"
    puts $fp "after 1500\n"
}

puts $fp "# 1. Compile Interfaces"
if {$gm_type eq "RTL" || $single_agent} {
    puts $fp "vlog -work work +cover -covercells ../verif/interface/${project_name}_interface.sv"
} else {
    for {set i 1} {$i <= $Num_AC_agent} {incr i} {
        set aname [lindex [lindex $active_agent [expr {$i-1}]] 0]
        puts $fp "vlog -work work ../verif/interface/${project_name}_${aname}_interface.sv"
    }
    for {set i 1} {$i <= $Num_PA_agent} {incr i} {
        set pname [lindex [lindex $passive_agent [expr {$i-1}]] 0]
        puts $fp "vlog -work work ../verif/interface/${project_name}_${pname}_interface.sv"
    }
}
puts $fp ""

puts $fp "# 2. Compile RTL"
puts $fp "set dut_v_files \[glob -nocomplain ../rtl/*.v\]"
set vlog_cov "vlog -work work +cover -covercells"
if {$gm_type eq "SB"} { set vlog_cov "vlog -cover bcst -work work" }

puts $fp "if {\[llength \$dut_v_files\] > 0} { $vlog_cov {*}\$dut_v_files }"
puts $fp "set dut_sv_files \[glob -nocomplain ../rtl/*.sv\]"
puts $fp "if {\[llength \$dut_sv_files\] > 0} { $vlog_cov {*}\$dut_sv_files }"

if {$gm_type eq "RTL" && [info exists REF_module] && $REF_module ne ""} {
    puts $fp "set gm_v_files \[glob -nocomplain ../verif/reference_model/*.v\]"
    puts $fp "if {\[llength \$gm_v_files\] > 0} { vlog -work work +cover -covercells {*}\$gm_v_files }"
    puts $fp "set gm_sv_files \[glob -nocomplain ../verif/reference_model/*.sv\]"
    puts $fp "if {\[llength \$gm_sv_files\] > 0} { vlog -work work +cover -covercells {*}\$gm_sv_files }"
}
puts $fp ""

puts $fp "# 3. Compile UVM Components"
set comp_cov "vlog -work work +cover -covercells"
if {$gm_type eq "SB"} { set comp_cov "vlog -work work" }
puts $fp "$comp_cov ../verif/config/${project_name}_config_obj.sv"

if {$gm_type eq "RTL" || $single_agent} {
    puts $fp "$comp_cov ../verif/agent/${project_name}_seq_item.sv"
    puts $fp "$comp_cov ../verif/agent/${project_name}_driver.sv"
    puts $fp "$comp_cov ../verif/agent/${project_name}_monitor.sv"
    puts $fp "$comp_cov ../verif/agent/${project_name}_sequencer.sv"
    puts $fp "$comp_cov ../verif/agent/${project_name}_agent.sv"
} else {
    for {set i 1} {$i <= $Num_AC_agent} {incr i} {
        set aname [lindex [lindex $active_agent [expr {$i-1}]] 0]
        puts $fp "vlog -work work ../verif/agent/Active/${aname}/${project_name}_${aname}_seq_item.sv"
        puts $fp "vlog -work work ../verif/agent/Active/${aname}/${project_name}_${aname}_sequencer.sv"
        puts $fp "vlog -work work ../verif/agent/Active/${aname}/${project_name}_${aname}_driver.sv"
        puts $fp "vlog -work work ../verif/agent/Active/${aname}/${project_name}_${aname}_monitor.sv"
        puts $fp "vlog -work work ../verif/agent/Active/${aname}/${project_name}_${aname}_agent.sv"
    }
    for {set i 1} {$i <= $Num_PA_agent} {incr i} {
        set pname [lindex [lindex $passive_agent [expr {$i-1}]] 0]
        puts $fp "vlog -work work ../verif/agent/Passive/${pname}/${project_name}_${pname}_seq_item.sv"
        puts $fp "vlog -work work ../verif/agent/Passive/${pname}/${project_name}_${pname}_monitor.sv"
        puts $fp "vlog -work work ../verif/agent/Passive/${pname}/${project_name}_${pname}_agent.sv"
    }
}

if {$gm_type eq "SB"} {
    if {$is_python} {
        puts $fp "# Python Golden Model SV & DPI Compilation"
        puts $fp "vlog -work work ../verif/reference_model/SV/protocol_pkg.sv"
        puts $fp "vlog -work work ../verif/reference_model/SV/protocol_encoder.sv"
        puts $fp "vlog -work work ../verif/reference_model/SV/protocol_decoder.sv"
        puts $fp "vlog -work work ../verif/reference_model/SV/${project_name}_reference_model_proxy.sv"
        puts $fp "vlog -work work ../verif/reference_model/dpi/socket_transport.c ../verif/reference_model/dpi/dpi_socket.c"
    } elseif {$is_c} {
        puts $fp "# C Golden Model Compilation"
        puts $fp "vlog -work work -dpiheader ../verif/reference_model/c/${project_name}_dpiheader.h ../verif/reference_model/${project_name}_reference_model_proxy.sv"
        puts $fp "vlog -work work ../verif/reference_model/c/${project_name}_reference_model.c"
    } else {
        puts $fp "# SystemVerilog Golden Model Compilation"
        puts $fp "vlog -work work ../verif/reference_model/${project_name}_reference_model.sv"
    }
}
set env_cov $comp_cov
if {$gm_type eq "SB"} { set env_cov "vlog -coveropt 3 +cover +acc -work work" }

if {$c_flag} {
    puts $fp "$env_cov ../verif/environment/${project_name}_coverage.sv"
}
puts $fp "$env_cov ../verif/environment/${project_name}_scoreboard.sv"
if {$gm_type eq "SB"} {
    puts $fp "$env_cov ../verif/environment/${project_name}_predictor.sv"
}
puts $fp "$comp_cov ../verif/environment/${project_name}_virtual_sequencer.sv"
puts $fp "$comp_cov ../verif/environment/${project_name}_environment.sv"
puts $fp "$comp_cov ../verif/sequences/sequences/*.sv"
puts $fp "$comp_cov ../verif/sequences/virtual/${project_name}_virtual_sequence.sv"

puts $fp "$comp_cov ../verif/test/${project_name}_test.sv"
if {$a_flag} {
    puts $fp "$comp_cov ../verif/assertions/${project_name}_assertions.sv"
    puts $fp "$comp_cov ../verif/assertions/${project_name}_bind.sv"
}
puts $fp ""

puts $fp "# 4. Compile Top Module"
puts $fp "$comp_cov ../verif/top/${project_name}_top.sv\n"

puts $fp "# 5. Run Simulation"
if {$a_flag} {
    puts $fp "vsim -coverage -voptargs=+acc work.${project_name}_top work.${project_name}_bind_sv_unit -ldflags \"-lws2_32\""
} else {
    puts $fp "vsim -coverage -voptargs=+acc work.${project_name}_top -ldflags \"-lws2_32\""
}
if {$gm_type eq "SB"} {
    puts $fp "coverage save -onexit ${project_name}_CodeCoverage.ucdb\n"
}
puts $fp "if \[file exists wave.do\] { do wave.do } else { add wave -r /* }"
puts $fp "\nrun -all"

puts $fp "\ncoverage save ${project_name}_uvm.ucdb -du ${dut_module}"
puts $fp "vcover report ${project_name}_uvm.ucdb -details -annotate -all -output Code_Coverage_Report.txt"

close $fp
