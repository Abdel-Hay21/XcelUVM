# =====================================================================
# generate_src_files.tcl
# =====================================================================

if {$gm_type ne "RTL"} { return }

if {![info exists project_name] || ![info exists path] || ![info exists dut_module]} { exit 1 }
set is_rtl_gm [expr {([info exists REF_module] && $REF_module ne "") ? 1 : 0}]

set output_dir  "${path}${project_name}_uvm/test"
set src_file    "${output_dir}/src_files.list"
if {![file exists $output_dir]} { file mkdir $output_dir }

set fp [open $src_file w]
puts $fp "# 1. Compile Interface\nvlog -work work ../verif/interface/${project_name}_interface.sv\n"

puts $fp "# 2. Compile RTL"
puts $fp "set dut_v_files \[glob -nocomplain ../rtl/*.v\]"
puts $fp "if {\[llength \$dut_v_files\] > 0} { vlog -work work {*}\$dut_v_files }"
puts $fp "set dut_sv_files \[glob -nocomplain ../rtl/*.sv\]"
puts $fp "if {\[llength \$dut_sv_files\] > 0} { vlog -work work {*}\$dut_sv_files }"

if {$is_rtl_gm} {
    puts $fp "set gm_v_files \[glob -nocomplain ../verif/reference_model/*.v\]"
    puts $fp "if {\[llength \$gm_v_files\] > 0} { vlog -work work {*}\$gm_v_files }"
    puts $fp "set gm_sv_files \[glob -nocomplain ../verif/reference_model/*.sv\]"
    puts $fp "if {\[llength \$gm_sv_files\] > 0} { vlog -work work {*}\$gm_sv_files }"
}

puts $fp "\n# 3. Compile UVM Components"
puts $fp "vlog -work work ../verif/config/${project_name}_config_obj.sv"
puts $fp "vlog -work work ../verif/agent/${project_name}_seq_item.sv"
puts $fp "vlog -work work ../verif/agent/${project_name}_driver.sv"
puts $fp "vlog -work work ../verif/agent/${project_name}_monitor.sv"
puts $fp "vlog -work work ../verif/agent/${project_name}_sequencer.sv"
puts $fp "vlog -work work ../verif/agent/${project_name}_agent.sv"

if {$coverage eq "true" || $coverage eq 1 || $coverage eq "True"} {
    puts $fp "vlog -work work ../verif/environment/${project_name}_coverage.sv"
}
puts $fp "vlog -work work ../verif/environment/${project_name}_scoreboard.sv"
puts $fp "vlog -work work ../verif/environment/${project_name}_environment.sv"
puts $fp "vlog -work work ../verif/sequences/*.sv"
puts $fp "vlog -work work ../verif/test/${project_name}_test.sv"
if {$assertions eq "true" || $assertions eq 1 || $assertions eq "True"} {
    puts $fp "vlog -work work ../verif/assertions/${project_name}_assertions.sv"
}

puts $fp "\n# 4. Compile Top Module\nvlog -work work ../verif/top/${project_name}_top.sv\n"
puts $fp "# 5. Run Simulation\nvsim -voptargs=+acc work.${project_name}_top\n"
puts $fp "if \[file exists wave.do\] { do wave.do } else { add wave -r /* }\nrun -all"

close $fp
