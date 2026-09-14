# =====================================================================
# gen_py_protocol_encoder.tcl
# Generates protocol_encoder.sv for Python Golden Model interface
# =====================================================================

proc generate_py_protocol_encoder {project_name ref_dir in_ports u_clk} {
    set proj_upper [string toupper $project_name]
    set sv_dir "${ref_dir}/SV"
    if {![file exists $sv_dir]} {
        file mkdir $sv_dir
    }
    set target_file "${sv_dir}/protocol_encoder.sv"

    # Calculate total payload size in bytes
    set total_payload_bytes 0
    set encode_lines ""
    
    foreach port $in_ports {
        set pname [lindex $port 0]
        if {$pname eq $u_clk} continue
        set width [lindex $port 1]
        set byte_len [expr {int(ceil(double($width) / 8.0))}]
        if {$byte_len < 1} { set byte_len 1 }
        incr total_payload_bytes $byte_len

        append encode_lines "        // ${pname} (${width} bits -> ${byte_len} byte(s))\n"
        if {$byte_len == 1} {
            append encode_lines "        packet\[idx++\] = byte'(tr.${pname});\n"
        } elseif {$byte_len == 2} {
            append encode_lines "        packet\[idx++\] = byte'(tr.${pname}\[15:8\]);\n"
            append encode_lines "        packet\[idx++\] = byte'(tr.${pname}\[7:0\]);\n"
        } elseif {$byte_len == 3} {
            append encode_lines "        packet\[idx++\] = byte'(tr.${pname}\[23:16\]);\n"
            append encode_lines "        packet\[idx++\] = byte'(tr.${pname}\[15:8\]);\n"
            append encode_lines "        packet\[idx++\] = byte'(tr.${pname}\[7:0\]);\n"
        } elseif {$byte_len == 4} {
            append encode_lines "        packet\[idx++\] = byte'(tr.${pname}\[31:24\]);\n"
            append encode_lines "        packet\[idx++\] = byte'(tr.${pname}\[23:16\]);\n"
            append encode_lines "        packet\[idx++\] = byte'(tr.${pname}\[15:8\]);\n"
            append encode_lines "        packet\[idx++\] = byte'(tr.${pname}\[7:0\]);\n"
        } else {
            for {set b [expr {$byte_len - 1}]} {$b >= 0} {incr b -1} {
                set msb [expr {$b * 8 + 7}]
                set lsb [expr {$b * 8}]
                append encode_lines "        packet\[idx++\] = byte'((tr.${pname} >> $lsb) & 8'hFF);\n"
            }
        }
    }

    set content ""
    append content "package protocol_encoder_pkg;\n\n"
    append content "import protocol_pkg::*;\n"
    append content "import ${project_name}_sequence_item_pkg::*;\n\n"
    append content "class protocol_encoder;\n\n"
    append content "    //------------------------------------------------------------\n"
    append content "    // Build Packet Header\n"
    append content "    //------------------------------------------------------------\n"
    append content "    static function int build_header\n"
    append content "    (\n"
    append content "        ref    byte           packet\[\],\n"
    append content "        input  message_type_e msg_type,\n"
    append content "        input  int            payload_size,\n"
    append content "        input  int unsigned   transaction_id\n"
    append content "    );\n"
    append content "        int idx;\n"
    append content "        idx = 0;\n\n"
    append content "        // Protocol Version\n"
    append content "        packet\[idx++\] = PROTOCOL_VERSION;\n\n"
    append content "        // Message Type\n"
    append content "        packet\[idx++\] = msg_type;\n\n"
    append content "        // Payload Length (Big Endian)\n"
    append content "        packet\[idx++\] = payload_size\[15:8\];\n"
    append content "        packet\[idx++\] = payload_size\[7:0\];\n\n"
    append content "        // Transaction ID (Big Endian)\n"
    append content "        packet\[idx++\] = transaction_id\[31:24\];\n"
    append content "        packet\[idx++\] = transaction_id\[23:16\];\n"
    append content "        packet\[idx++\] = transaction_id\[15:8\];\n"
    append content "        packet\[idx++\] = transaction_id\[7:0\];\n\n"
    append content "        return idx;\n"
    append content "    endfunction\n\n\n"
    append content "    //------------------------------------------------------------\n"
    append content "    // Encode Request\n"
    append content "    //------------------------------------------------------------\n"
    append content "    static function void encode_request\n"
    append content "    (\n"
    append content "        input  ${project_name}_sequence_item tr,\n"
    append content "        ref    byte                packet\[\]\n"
    append content "    );\n"
    append content "        int idx;\n"
    append content "        int payload_size;\n\n"
    append content "        payload_size = ${total_payload_bytes};\n\n"
    append content "        // Allocate Packet (Header + Payload)\n"
    append content "        packet = new\[HEADER_SIZE + payload_size\];\n\n"
    append content "        // Build Header\n"
    append content "        idx = build_header(\n"
    append content "                packet,\n"
    append content "                MSG_${proj_upper}_REQUEST,\n"
    append content "                payload_size,\n"
    append content "                1               // Transaction ID\n"
    append content "              );\n\n"
    append content "        // Payload Serialization\n"
    append content $encode_lines
    append content "    endfunction\n\n"
    append content "endclass\n"
    append content "endpackage\n"

    set fp [open $target_file w]
    puts -nonewline $fp $content
    close $fp
    puts "Python Protocol Encoder generated: $target_file"
}
