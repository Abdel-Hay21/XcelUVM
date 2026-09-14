# =====================================================================
# gen_py_protocol_pkg.tcl
# Generates protocol_pkg.sv for Python Golden Model interface
# =====================================================================

proc generate_py_protocol_pkg {project_name ref_dir} {
    set proj_upper [string toupper $project_name]
    set sv_dir "${ref_dir}/SV"
    if {![file exists $sv_dir]} {
        file mkdir $sv_dir
    }
    set target_file "${sv_dir}/protocol_pkg.sv"
    
    set content ""
    append content "package protocol_pkg;\n\n"
    append content "    //----------------------------------------------------------\n"
    append content "    // Protocol Version\n"
    append content "    //----------------------------------------------------------\n"
    append content "    localparam byte PROTOCOL_VERSION = 8'd1;\n\n"
    append content "    //----------------------------------------------------------\n"
    append content "    // Message Types\n"
    append content "    //----------------------------------------------------------\n"
    append content "    typedef enum byte\n"
    append content "    {\n"
    append content "        MSG_${proj_upper}_REQUEST  = 8'd1,\n"
    append content "        MSG_${proj_upper}_RESPONSE = 8'd2,\n\n"
    append content "        MSG_PING         = 8'd3,\n"
    append content "        MSG_PONG         = 8'd4,\n\n"
    append content "        MSG_SHUTDOWN     = 8'd5\n\n"
    append content "    } message_type_e;\n\n"
    append content "    //----------------------------------------------------------\n"
    append content "    // Packet Constants\n"
    append content "    //----------------------------------------------------------\n"
    append content "    localparam int HEADER_SIZE      = 8;\n"
    append content "    localparam int MAX_PAYLOAD_SIZE = 1024;\n\n"
    append content "endpackage\n"

    set fp [open $target_file w]
    puts -nonewline $fp $content
    close $fp
    puts "Python Protocol Package generated: $target_file"
}
