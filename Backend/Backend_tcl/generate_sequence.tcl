# ==============================================================
# Script Name: generate_sequence.tcl
# Description: Generate multiple sequence files from the main sequence file
# ==============================================================

if {![info exists project_name]} { exit 1 }
if {![info exists sequence_list]} { exit 1 }

set base_dir          "${path}${project_name}_uvm/verif"
set seq_dir           "${base_dir}/sequences/sequences"
set base_sequence_file "${base_dir}/environment/${project_name}_sequence.sv"

if {![file exists $base_sequence_file]} { exit 1 }

set fid [open $base_sequence_file r]
set file_data [read $fid]
close $fid

if {![file exists $seq_dir]} { file mkdir $seq_dir }

if {$single_agent || $gm_type eq "RTL"} {
    foreach seq_info $sequence_list {
        set seq_name [lindex $seq_info 0]
        set new_file "${seq_dir}/${project_name}_${seq_name}_sequence.sv"
        set new_data [string map [list "mysequence" "${seq_name}_sequence" \
                                       "templete_sequence_item" "${project_name}_sequence_item"] $file_data]
        set fout [open $new_file w]; puts $fout $new_data; close $fout
    }
} else {
    for {set i 1} {$i <= $Num_AC_agent} {incr i} {
        set aname [lindex [lindex $active_agent [expr {$i-1}]] 0]
        foreach seq_info $sequence_list {
            set seq_name [lindex $seq_info 0]
            set new_file "${seq_dir}/${project_name}_${aname}_${seq_name}_sequence.sv"
            set new_data [string map [list "mysequence" "${aname}_${seq_name}_sequence" \
                                           "${project_name}_sequence_item" "${project_name}_${aname}_sequence_item" \
                                           "${project_name}_sequence_pkg" "${project_name}_${aname}_sequence_pkg"] $file_data]
            set fout [open $new_file w]; puts $fout $new_data; close $fout
        }
    }
}
file delete $base_sequence_file
