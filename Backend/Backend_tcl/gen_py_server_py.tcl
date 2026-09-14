# =====================================================================
# gen_py_server_py.tcl
# Generates server.py for Python Reference Model socket bridge
# =====================================================================

proc generate_py_server_py {project_name ref_dir in_ports out_ports u_clk} {
    set proj_upper [string toupper $project_name]
    set py_dir "${ref_dir}/python"
    if {![file exists $py_dir]} {
        file mkdir $py_dir
    }
    set target_file "${py_dir}/server.py"

    set in_decode_lines ""
    set in_arg_list {}
    foreach port $in_ports {
        set pname [lindex $port 0]
        if {$pname eq $u_clk} continue
        set width [lindex $port 1]
        set byte_len [expr {int(ceil(double($width) / 8.0))}]
        if {$byte_len < 1} { set byte_len 1 }
        lappend in_arg_list $pname

        if {$byte_len == 1} {
            append in_decode_lines "            ${pname} = payload\[idx\]\n"
            append in_decode_lines "            idx += 1\n"
        } else {
            append in_decode_lines "            ${pname} = int.from_bytes(payload\[idx : idx + ${byte_len}\], byteorder='big')\n"
            append in_decode_lines "            idx += ${byte_len}\n"
        }
    }

    set out_arg_list {}
    set out_encode_lines ""
    foreach port $out_ports {
        set pname [lindex $port 0]
        set width [lindex $port 1]
        set byte_len [expr {int(ceil(double($width) / 8.0))}]
        if {$byte_len < 1} { set byte_len 1 }
        lappend out_arg_list $pname

        append out_encode_lines "            response_payload.extend(int(${pname} & ((1 << ${width}) - 1)).to_bytes(${byte_len}, byteorder='big'))\n"
    }

    set in_args_str [join $in_arg_list ", "]
    set out_unpack_str [join $out_arg_list ", "]
    set exec_call_line "            ${out_unpack_str} = execute(${in_args_str})"

    set content ""
    append content "import socket\n\n"
    append content "from protocol import *\n"
    append content "from ${project_name}_reference_model import *\n\n\n"
    append content "############################################################\n"
    append content "# Socket Configuration\n"
    append content "############################################################\n\n"
    append content "HOST = \"127.0.0.1\"\n"
    append content "PORT = 5000\n\n\n"
    append content "############################################################\n"
    append content "# Create and Bind Socket\n"
    append content "############################################################\n\n"
    append content "server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
    append content "server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)\n"
    append content "server_socket.bind((HOST, PORT))\n"
    append content "server_socket.listen(1)\n\n"
    append content "print(f\"\[${project_name} Server\] Waiting for connection on {HOST}:{PORT} ...\")\n"
    append content "client_socket, client_address = server_socket.accept()\n"
    append content "print(f\"\[${project_name} Server\] Connected to UVM Testbench from : {client_address}\")\n\n\n"
    append content "############################################################\n"
    append content "# Main Request Processing Loop\n"
    append content "############################################################\n\n"
    append content "try:\n"
    append content "    while True:\n"
    append content "        # 1. Receive Header\n"
    append content "        header = client_socket.recv(HEADER_SIZE)\n"
    append content "        if not header or len(header) < HEADER_SIZE:\n"
    append content "            break\n\n"
    append content "        version, msg_type, payload_length, transaction_id = decode_header(header)\n\n"
    append content "        # 2. Receive Complete Payload\n"
    append content "        payload = b\"\"\n"
    append content "        while len(payload) < payload_length:\n"
    append content "            chunk = client_socket.recv(payload_length - len(payload))\n"
    append content "            if not chunk:\n"
    append content "                break\n"
    append content "            payload += chunk\n\n"
    append content "        # 3. Handle Request\n"
    append content "        if msg_type == MSG_${proj_upper}_REQUEST:\n"
    append content "            idx = 0\n"
    append content $in_decode_lines
    append content "\n"
    append content $exec_call_line
    append content "\n\n"
    append content "            # Encode Response Payload\n"
    append content "            response_payload = bytearray()\n"
    append content $out_encode_lines
    append content "            response_payload = bytes(response_payload)\n\n"
    append content "            # Build Response Header and Send\n"
    append content "            response_header = encode_header(\n"
    append content "                MSG_${proj_upper}_RESPONSE,\n"
    append content "                len(response_payload),\n"
    append content "                transaction_id\n"
    append content "            )\n\n"
    append content "            client_socket.sendall(response_header + response_payload)\n\n"
    append content "        # 4. Handle Shutdown\n"
    append content "        elif msg_type == MSG_SHUTDOWN:\n"
    append content "            print(f\"\[${project_name} Server\] Received SHUTDOWN signal\")\n"
    append content "            break\n\n"
    append content "finally:\n"
    append content "    client_socket.close()\n"
    append content "    server_socket.close()\n"
    append content "    print(f\"\[${project_name} Server\] Socket Server Closed gracefully.\")\n"

    set fp [open $target_file w]
    puts -nonewline $fp $content
    close $fp
    puts "Python Server generated: $target_file"
}
