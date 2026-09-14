# =====================================================================
# generate_wave.tcl
# =====================================================================


if {![info exists project_name] || ![info exists path] || ![info exists dut_module]} { exit 1 }

set output_dir  "${path}${project_name}_uvm/test"
set wave_file   "${output_dir}/wave.do"

if {![file exists $output_dir]} { file mkdir $output_dir }

set fp [open $wave_file w]
puts $fp "onerror {resume}\nquietly WaveActivateNextPane {} 0\n"

foreach port $input_ports {
    lassign $port name width type
    puts $fp "add wave -noupdate -expand -group ${dut_module} /${project_name}_top/DUT_interface/$name"
}
foreach port $output_ports {
    lassign $port name width type
    puts $fp "add wave -noupdate -expand -group ${dut_module} /${project_name}_top/DUT_interface/$name"
}

if {$gm_type eq "RTL"} {
    puts $fp ""
    foreach port $input_ports {
        lassign $port name width type
        puts $fp "add wave -noupdate -expand -group ${REF_module} /${project_name}_top/REF_interface/$name"
    }
    foreach port $output_ports {
        lassign $port name width type
        puts $fp "add wave -noupdate -expand -group ${REF_module} /${project_name}_top/REF_interface/$name"
    }
}
puts $fp "\nTreeUpdate \[SetDefaultTree\]"
puts $fp "WaveRestoreCursors {{Cursor 1} {0 ps} 0}"
puts $fp "quietly wave cursor active 1"
puts $fp "configure wave -namecolwidth 150\nconfigure wave -valuecolwidth 100\nconfigure wave -justifyvalue left"
puts $fp "configure wave -signalnamewidth 1\nconfigure wave -snapdistance 10\nconfigure wave -datasetprefix 0"
puts $fp "configure wave -rowmargin 4\nconfigure wave -childrowmargin 2\nconfigure wave -gridoffset 0"
puts $fp "configure wave -gridperiod 1\nconfigure wave -griddelta 40\nconfigure wave -timeline 0"
puts $fp "configure wave -timelineunits ps\nupdate\nWaveRestoreZoom {0 ps} {0 ps}"

close $fp
