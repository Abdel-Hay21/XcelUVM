# ================================================
# lib_rtl_generate.tcl
# RTL Mode generation logic
# ================================================

set template_files [glob -nocomplain -directory $template_dir *]
if {[llength $template_files] == 0} {
    puts "No files found in $template_dir"
    exit 1
}

# Only pick templates with _RTL suffix, or shared ones without a suffix
set filtered_templates {}
foreach file $template_files {
    set filename [file tail $file]
    if {[string match "*_SB.sv" $filename]} { continue }
    
    # Filter predictors and proxies
    if {[string match "*predictor_v.sv"  $filename] ||
        [string match "*predictor_c.sv"  $filename] ||
        [string match "*predictor_ex.sv" $filename] ||
        [string match "reference_model_v.sv"       $filename] ||
        [string match "reference_model_proxy_c.sv" $filename] ||
        [string match "reference_model_proxy_ex.sv" $filename]} { continue }
        
    if {!$a_flag && [string match "*_assertions*" $filename]} { continue }
    if {!$c_flag && [string match "*_coverage*"   $filename]} { continue }
    
    lappend filtered_templates $file
}

foreach file $filtered_templates {
    set filename [file tail $file]
    # Remove _RTL suffix for output filename
    set base_filename [string map {"_RTL.sv" ".sv"} $filename]
    set new_filename [string map [list templete $project_name] $base_filename]

    set fp [open $file r]
    set data [read $fp]
    close $fp
    
    set new_data [string map [list templete $project_name USER_CLK $user_clk] $data]

    if {[string match "*_top*" $filename]} {
        set assertions_str "${project_name}_assertions"
        
        if {$a_flag} {
            set col1_max [expr {
                max([string length $dut_module],
                    [string length $REF_module],
                    [string length $assertions_str])
            }]
        } else {
            set col1_max [expr {
                max([string length $dut_module],
                    [string length $REF_module])
            }]
        }
        
        set port_map_dut "(\n"
        set port_map_REF "(\n"
        set all_ports [concat $input_ports $output_ports]
        set port_count [llength $all_ports]
        
        set max_port_len 0
        foreach port $all_ports {
            set n [string length [lindex $port 0]]
            if {$n > $max_port_len} { set max_port_len $n }
        }
        
        set i 0
        foreach port $all_ports {
            set pname [lindex $port 0]
            incr i
            set pad [string repeat " " [expr {$max_port_len - [string length $pname]}]]
            set dut_if "DUT_interface.${pname}"
            set gld_if "REF_interface.${pname}"

            if {$i < $port_count} {
                append port_map_dut    "       .${pname}${pad} ( ${dut_if}${pad} ) ,\n"
                append port_map_REF "       .${pname}${pad} ( ${gld_if}${pad} ) ,\n"
            } else {
                append port_map_dut    "       .${pname}${pad} ( ${dut_if}${pad} )\n     )"
                append port_map_REF "       .${pname}${pad} ( ${gld_if}${pad} )\n     )"
            }
        }
        
        if {$a_flag} {
            set new_data [string map \
                [list "NODUT_COL1"      [_pad $dut_module    $col1_max] \
                      "DOREF_COL1"   [_pad $REF_module  $col1_max] \
                      "ASSERTIONS_COL1" [_pad $assertions_str $col1_max] \
                      "DUT_PORT_MAP"    $port_map_dut \
                      "REF_PORT_MAP" $port_map_REF] \
                $new_data]
        } else {
            set new_data [string map \
                [list "NODUT_COL1"    [_pad $dut_module   $col1_max] \
                      "DOREF_COL1" [_pad $REF_module $col1_max] \
                      "DUT_PORT_MAP"    $port_map_dut \
                      "REF_PORT_MAP" $port_map_REF] \
                $new_data]
                
            set new_data [regsub -line {^[ \t]*ASSERTIONS_COL1.*\n} $new_data ""]
            set new_data [string map {"// DUT, REF and Assertions" "// DUT, REF"} $new_data]
        }
    }
    
    set subdir [get_template_subdir $filename]
    write_file "${output_dir}/${subdir}/${new_filename}" $new_data
    puts "Generated: ${subdir}/${new_filename}"
}

puts "RTL files generated successfully."
