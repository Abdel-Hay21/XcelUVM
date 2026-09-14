# =====================================================
# generate_interface.tcl
# =====================================================

set output_dir "${path}${project_name}_uvm/verif"
set interface_dir "${output_dir}/interface"
if {![file exists $interface_dir]} { file mkdir $interface_dir }

proc padded_decl {type width name max_len max_width_len} {
    set name_pad [string repeat " " [expr {$max_len - [string length $name]}]]
    if {$width == 1} { set w_str "" } else { set w_str "\[[expr {$width - 1}]:0\]" }
    set w_len [string length $w_str]
    set width_pad [string repeat " " [expr {$max_width_len - $w_len}]]
    if {$max_width_len == 0} {
        return "  ${type}       ${name}${name_pad} ;"
    } else {
        if {$w_str == ""} { return "  ${type}  ${width_pad}${name}${name_pad} ;" } else { return "  ${type} ${w_str}${width_pad} ${name}${name_pad} ;" }
    }
}

proc format_ports {direction port_list max_len add_trailing_comma} {
    set formatted ""
    set count [llength $port_list]
    set i 0
    foreach port $port_list {
        set name [lindex $port 0]
        set pad [string repeat " " [expr {$max_len - [string length $name]}]]
        incr i
        if {$i < $count || $add_trailing_comma} {
            append formatted "    ${direction} ${name}${pad}   ,\n"
        } else {
            append formatted "    ${direction} ${name}${pad}\n"
        }
    }
    return $formatted
}

proc generate_interface_file {if_name has_clk in_ports out_ports u_clk interface_dir} {
    set if_file "${interface_dir}/${if_name}.sv"
    set fp [open $if_file w]
    
    if {$has_clk && $u_clk ne ""} {
        puts $fp "interface ${if_name}(${u_clk});\n"
        puts $fp "  input bit ${u_clk};\n"
    } else {
        puts $fp "interface ${if_name}();\n"
    }

    set max_name_len 0
    set max_width_len 0
    foreach port [concat $in_ports $out_ports] {
        set n [string length [lindex $port 0]]
        if {$n > $max_name_len} { set max_name_len $n }
        set width [lindex $port 1]
        if {$width > 1} {
            set w_str "\[[expr {$width - 1}]:0\]"
            set wlen [string length $w_str]
            if {$wlen > $max_width_len} { set max_width_len $wlen }
        }
    }

    foreach port $in_ports {
        lassign $port name width type
        if {$has_clk && $name eq $u_clk} continue
        puts $fp [padded_decl $type $width $name $max_name_len $max_width_len]
    }
    foreach port $out_ports {
        lassign $port name width type
        puts $fp [padded_decl $type $width $name $max_name_len $max_width_len]
    }
    puts $fp "\n"

    puts $fp "  modport DUT("
    set dut_inputs  [format_ports "input " $in_ports  $max_name_len 1]
    set dut_outputs [format_ports "output" $out_ports $max_name_len 0]
    puts -nonewline $fp "${dut_inputs}${dut_outputs}"
    puts $fp "  );\n"

    puts $fp "  modport TEST("
    set test_outputs [format_ports "output" $in_ports  $max_name_len 1]
    set test_inputs  [format_ports "input " $out_ports $max_name_len 0]
    puts -nonewline $fp "${test_outputs}${test_inputs}"
    puts $fp "  );\n"

    puts $fp "endinterface\n"
    close $fp
    puts "Interface generated: ${if_name}.sv"
}

if {$gm_type eq "RTL" || ($gm_type eq "SB" && $single_agent)} {
    set if_name "${project_name}_interface"
    set in_p  [expr {[info exists input_ports]  ? $input_ports  : ( [info exists input_ports_A1]  ? $input_ports_A1  : {} )}]
    set out_p [expr {[info exists output_ports] ? $output_ports : ( [info exists output_ports_A1] ? $output_ports_A1 : {} )}]
    set u_clk [expr {[llength $in_p] > 0 ? [lindex [lindex $in_p 0] 0] : "clk"}]
    generate_interface_file $if_name 1 $in_p $out_p $u_clk $interface_dir
} else {
    for {set i 1} {$i <= $Num_AC_agent} {incr i} {
        set agent_info [lindex $active_agent [expr {$i - 1}]]
        if {$agent_info eq ""} { continue }
        set agent_name [lindex $agent_info 0]
        set agent_clk  [lindex $agent_info 1]
        set in_var  "input_ports_A${i}"; set out_var "output_ports_A${i}"
        if {![info exists $in_var] || ![info exists $out_var]} { continue }
        set a_user_clk [expr {$agent_clk ? [lindex [lindex [set $in_var] 0] 0] : ""}]
        generate_interface_file "${project_name}_${agent_name}_interface" $agent_clk [set $in_var] [set $out_var] $a_user_clk $interface_dir
    }
    for {set i 1} {$i <= $Num_PA_agent} {incr i} {
        set agent_info [lindex $passive_agent [expr {$i - 1}]]
        if {$agent_info eq ""} { continue }
        set agent_name [lindex $agent_info 0]
        set agent_clk  [lindex $agent_info 1]
        set in_var  "input_ports_P${i}"; set out_var "output_ports_P${i}"
        if {![info exists $in_var] || ![info exists $out_var]} { continue }
        set p_user_clk [expr {$agent_clk ? [lindex [lindex [set $in_var] 0] 0] : ""}]
        generate_interface_file "${project_name}_${agent_name}_interface" $agent_clk [set $in_var] [set $out_var] $p_user_clk $interface_dir
    }
}
