# =====================================================================
# gen_py_reference_model_proxy.tcl
# Generates SV Reference Model Proxy for Python Golden Model interface
# =====================================================================

proc generate_py_reference_model_proxy {project_name ref_dir single_agent {all_agents {}}} {
    set sv_dir "${ref_dir}/SV"
    if {![file exists $sv_dir]} {
        file mkdir $sv_dir
    }
    set target_file "${sv_dir}/${project_name}_reference_model_proxy.sv"

    set content ""
    append content "package ${project_name}_reference_model_proxy_pkg;\n\n"
    append content "import uvm_pkg::*;\n"
    if {$single_agent} {
        append content "import ${project_name}_sequence_item_pkg::*;\n"
    } else {
        foreach ag_name $all_agents {
            append content "import ${project_name}_${ag_name}_sequence_item_pkg::*;\n"
        }
    }
    append content "import protocol_pkg::*;\n"
    append content "import protocol_encoder_pkg::*;\n"
    append content "import protocol_decoder_pkg::*;\n"
    append content "`include \"uvm_macros.svh\"\n\n"

    append content "//------------------------------------------------------------\n"
    append content "// DPI Functions (Package Scope)\n"
    append content "//------------------------------------------------------------\n"
    append content "import \"DPI-C\" function int rm_connect();\n"
    append content "import \"DPI-C\" function int rm_disconnect();\n"
    append content "import \"DPI-C\" function int rm_send(input byte packet\[1024\], input int size);\n"
    append content "import \"DPI-C\" function int rm_receive(output byte packet\[1024\]);\n\n"

    append content "class ${project_name}_reference_model_proxy extends uvm_object;\n\n"
    append content "    `uvm_object_utils(${project_name}_reference_model_proxy)\n\n"
    append content "    //------------------------------------------------------------\n"
    append content "    // Constructor\n"
    append content "    //------------------------------------------------------------\n"
    append content "    function new(string name = \"${project_name}_reference_model_proxy\");\n"
    append content "        super.new(name);\n"
    append content "    endfunction\n\n"

    append content "    //------------------------------------------------------------\n"
    append content "    // Connect\n"
    append content "    //------------------------------------------------------------\n"
    append content "    function void connect();\n"
    append content "        if(rm_connect() != 0)\n"
    append content "            `uvm_fatal(\"REF_MODEL\", \"Cannot connect to Python Server\")\n"
    append content "    endfunction\n\n"

    append content "    //------------------------------------------------------------\n"
    append content "    // Disconnect\n"
    append content "    //------------------------------------------------------------\n"
    append content "    function void disconnect();\n"
    append content "        void'(rm_disconnect());\n"
    append content "    endfunction\n\n"

    append content "    //------------------------------------------------------------\n"
    append content "    // Execute\n"
    append content "    //------------------------------------------------------------\n"
    append content "    function ${project_name}_sequence_item execute\n"
    append content "    (\n"
    append content "        input ${project_name}_sequence_item request\n"
    append content "    );\n"
    append content "        byte packet\[1024\];\n"
    append content "        byte response_packet\[1024\];\n"
    append content "        int  packet_size;\n"
    append content "        ${project_name}_sequence_item response;\n"
    append content "        byte dyn_packet\[\];\n"
    append content "        byte dyn_response\[\];\n\n"

    append content "        // 1. Encode Request\n"
    append content "        protocol_encoder::encode_request(\n"
    append content "            request,\n"
    append content "            dyn_packet\n"
    append content "        );\n\n"

    append content "        packet_size = dyn_packet.size();\n"
    append content "        for(int i = 0; i < packet_size; i++) begin\n"
    append content "            packet\[i\] = dyn_packet\[i\];\n"
    append content "        end\n\n"

    append content "        // 2. Send over DPI socket\n"
    append content "        void'(rm_send(packet, packet_size));\n\n"

    append content "        // 3. Receive response over DPI socket\n"
    append content "        void'(rm_receive(response_packet));\n\n"

    append content "        // 4. Decode Response\n"
    append content "        dyn_response = new\[HEADER_SIZE + {response_packet\[2], response_packet\[3\]}\];\n"
    append content "        for(int i = 0; i < dyn_response.size(); i++) begin\n"
    append content "            dyn_response\[i\] = response_packet\[i\];\n"
    append content "        end\n\n"

    append content "        protocol_decoder::decode_response(\n"
    append content "            dyn_response,\n"
    append content "            response\n"
    append content "        );\n\n"

    append content "        return response;\n"
    append content "    endfunction\n\n"
    append content "endclass\n"
    append content "endpackage\n"

    set fp [open $target_file w]
    puts -nonewline $fp $content
    close $fp
    puts "Python Reference Model Proxy generated: $target_file"
}
