# =====================================================================
# gen_py_protocol_decoder.tcl
# Generates protocol_decoder.sv for Python Golden Model interface
# =====================================================================

proc generate_py_protocol_decoder {project_name ref_dir out_ports} {
    set sv_dir "${ref_dir}/SV"
    if {![file exists $sv_dir]} {
        file mkdir $sv_dir
    }
    set target_file "${sv_dir}/protocol_decoder.sv"

    set decode_lines ""
    foreach port $out_ports {
        set pname [lindex $port 0]
        set width [lindex $port 1]
        set byte_len [expr {int(ceil(double($width) / 8.0))}]
        if {$byte_len < 1} { set byte_len 1 }

        append decode_lines "        // ${pname} (${width} bits -> ${byte_len} byte(s))\n"
        if {$byte_len == 1} {
            append decode_lines "        tr.${pname} = packet\[idx++\];\n"
        } elseif {$byte_len == 2} {
            append decode_lines "        tr.${pname} = {packet\[idx\], packet\[idx+1\]};\n"
            append decode_lines "        idx += 2;\n"
        } elseif {$byte_len == 3} {
            append decode_lines "        tr.${pname} = {packet\[idx\], packet\[idx+1\], packet\[idx+2\]};\n"
            append decode_lines "        idx += 3;\n"
        } elseif {$byte_len == 4} {
            append decode_lines "        tr.${pname} = {packet\[idx\], packet\[idx+1\], packet\[idx+2\], packet\[idx+3\]};\n"
            append decode_lines "        idx += 4;\n"
        } else {
            set slice_parts {}
            for {set b 0} {$b < $byte_len} {incr b} {
                if {$b == 0} {
                    lappend slice_parts "packet\[idx\]"
                } else {
                    lappend slice_parts "packet\[idx+${b}\]"
                }
            }
            append decode_lines "        tr.${pname} = {[join $slice_parts ", "]};\n"
            append decode_lines "        idx += ${byte_len};\n"
        }
    }

    set content ""
    append content "package protocol_decoder_pkg;\n\n"
    append content "import protocol_pkg::*;\n"
    append content "import ${project_name}_sequence_item_pkg::*;\n\n"
    append content "class protocol_decoder;\n\n"
    append content "    //------------------------------------------------------------\n"
    append content "    // Decode Response\n"
    append content "    //------------------------------------------------------------\n"
    append content "    static function void decode_response\n"
    append content "    (\n"
    append content "        input  byte                 packet\[\],\n"
    append content "        output ${project_name}_sequence_item tr\n"
    append content "    );\n"
    append content "        int idx;\n"
    append content "        int payload_length;\n"
    append content "        int transaction_id;\n\n"
    append content "        // Create Transaction\n"
    append content "        tr = ${project_name}_sequence_item::type_id::create(\"tr\");\n\n"
    append content "        // Start from beginning of packet\n"
    append content "        idx = 0;\n\n"
    append content "        // Version\n"
    append content "        idx++;\n\n"
    append content "        // Message Type\n"
    append content "        idx++;\n\n"
    append content "        // Payload Length\n"
    append content "        payload_length = {packet\[idx\], packet\[idx+1\]};\n"
    append content "        idx += 2;\n\n"
    append content "        // Transaction ID\n"
    append content "        transaction_id = {packet\[idx\], packet\[idx+1\], packet\[idx+2\], packet\[idx+3\]};\n"
    append content "        idx += 4;\n\n"
    append content "        // Decode Response Payload Fields\n"
    append content $decode_lines
    append content "    endfunction\n\n"
    append content "endclass\n"
    append content "endpackage\n"

    set fp [open $target_file w]
    puts -nonewline $fp $content
    close $fp
    puts "Python Protocol Decoder generated: $target_file"
}
