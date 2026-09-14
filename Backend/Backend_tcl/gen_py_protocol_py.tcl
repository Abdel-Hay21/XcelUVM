# =====================================================================
# gen_py_protocol_py.tcl
# Generates protocol.py for Python Reference Model
# =====================================================================

proc generate_py_protocol_py {project_name ref_dir} {
    set proj_upper [string toupper $project_name]
    set py_dir "${ref_dir}/python"
    if {![file exists $py_dir]} {
        file mkdir $py_dir
    }
    set target_file "${py_dir}/protocol.py"

    set content ""
    append content "import struct\n\n"
    append content "############################################################\n"
    append content "# Protocol Information\n"
    append content "############################################################\n\n"
    append content "PROTOCOL_VERSION = 1\n\n"
    append content "############################################################\n"
    append content "# Message Types\n"
    append content "############################################################\n\n"
    append content "MSG_${proj_upper}_REQUEST  = 1\n"
    append content "MSG_${proj_upper}_RESPONSE = 2\n\n"
    append content "MSG_PING         = 3\n"
    append content "MSG_PONG         = 4\n\n"
    append content "MSG_SHUTDOWN     = 5\n\n"
    append content "############################################################\n"
    append content "# Header Constants\n"
    append content "############################################################\n\n"
    append content "HEADER_SIZE = 8\n\n\n"
    append content "############################################################\n"
    append content "# Decode Header\n"
    append content "############################################################\n\n"
    append content "def decode_header(packet):\n"
    append content "    version = packet\[0\]\n"
    append content "    msg_type = packet\[1\]\n"
    append content "    payload_length = struct.unpack(\">H\", packet\[2:4\])\[0\]\n"
    append content "    transaction_id = struct.unpack(\">I\", packet\[4:8\])\[0\]\n"
    append content "    return version, msg_type, payload_length, transaction_id\n\n\n"
    append content "############################################################\n"
    append content "# Encode Header\n"
    append content "############################################################\n\n"
    append content "def encode_header(msg_type, payload_length, transaction_id):\n"
    append content "    return struct.pack(\n"
    append content "        \">BBHI\",\n"
    append content "        PROTOCOL_VERSION,\n"
    append content "        msg_type,\n"
    append content "        payload_length,\n"
    append content "        transaction_id\n"
    append content "    )\n"

    set fp [open $target_file w]
    puts -nonewline $fp $content
    close $fp
    puts "Python Protocol Module generated: $target_file"
}
