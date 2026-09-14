# --------- custum_coverage.tcl ---------
if {$gm_type eq "RTL"} {
    # --------- custum_coverage.tcl ---------
    # This script processes the generated environment file to either
    # remove lines containing Case_NO_Coverage (if coverage is false)
    # or clean up the Case_NO_Coverage text (if coverage is true).
    
    if {![info exists project_name] || ![info exists path] || ![info exists coverage]} {
        puts "Error: project_name, path, or coverage not defined."
        exit 1
    }
    
    set environment_file "${path}${project_name}_uvm/verif/environment/${project_name}_environment.sv"
    
    if {![file exists $environment_file]} {
        puts "Error: environment file not found at $environment_file"
        exit 1
    }
    
    set fp [open $environment_file r]
    set data [read $fp]
    close $fp
    
    if {$coverage eq "false" || $coverage eq 0 || $coverage eq "False"} {
        # Remove lines containing Case_NO_Coverage entirely
        set new_data [regsub -all -line {^[ \t]*.*Case_NO_Coverage.*\n} $data ""]
        puts "Coverage disabled: Removed Case_NO_Coverage lines from environment file."
    } else {
        # Clean up the marker // Case_NO_Coverage leaving the lines intact
        set new_data [regsub -all { ?// ?Case_NO_Coverage} $data ""]
        puts "Coverage enabled: Cleaned up Case_NO_Coverage markers from environment file."
    }
    
    set fp [open $environment_file w]
    puts -nonewline $fp $new_data
    close $fp
} else {
    # --------- custum_coverage.tcl ---------
    # This script processes the generated environment file to either
    # remove lines containing Case_NO_Coverage (if coverage is false)
    # or clean up the Case_NO_Coverage text (if coverage is true).
    
    if {![info exists project_name] || ![info exists path] || ![info exists coverage]} {
        puts "Error: project_name, path, or coverage not defined."
        exit 1
    }
    
    set environment_file "${path}${project_name}_uvm/verif/environment/${project_name}_environment.sv"
    
    if {![file exists $environment_file]} {
        puts "Error: environment file not found at $environment_file"
        exit 1
    }
    
    set fp [open $environment_file r]
    set data [read $fp]
    close $fp
    
    if {$coverage eq "false" || $coverage eq 0 || $coverage eq "False"} {
        # Remove lines containing Case_NO_Coverage entirely
        set new_data [regsub -all -line {^[ \t]*.*Case_NO_Coverage.*\n} $data ""]
        puts "Coverage disabled: Removed Case_NO_Coverage lines from environment file."
    } else {
        # Clean up the marker // Case_NO_Coverage leaving the lines intact
        set new_data [regsub -all { ?// ?Case_NO_Coverage} $data ""]
        puts "Coverage enabled: Cleaned up Case_NO_Coverage markers from environment file."
    }
    
    set fp [open $environment_file w]
    puts -nonewline $fp $new_data
    close $fp
}
