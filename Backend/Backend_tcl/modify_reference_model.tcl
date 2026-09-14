# modify_reference_model.tcl
if {$gm_type ne "SB"} return

# =====================================================================
# modify_reference_model.tcl
# Injects unpacked structs, mappings, and execute functions into reference model / proxy.
# Generates C header (.h) and source (.c) files for DPI-C reference models.
# Supports both SV and C (DPI-C) in Single-Agent and Multi-Agent modes.
# Uses memory-safe unpacked structs with C-compatible scalar types.
# =====================================================================

if {![info exists project_name] || ![info exists path]} {
    puts "Error: project_name or path not defined."
    exit 1
}

if {![info exists sb_language] || $sb_language eq ""} { set sb_language "SV" }

set output_dir "${path}${project_name}_uvm/verif"
set ref_dir    "${output_dir}/reference_model"
set c_dir      "${ref_dir}/c"

# Collect all agents
set all_agents {}
for {set i 1} {$i <= $Num_AC_agent} {incr i} {
    lappend all_agents [lindex [lindex $active_agent [expr {$i-1}]] 0]
}
for {set i 1} {$i <= $Num_PA_agent} {incr i} {
    lappend all_agents [lindex [lindex $passive_agent [expr {$i-1}]] 0]
}

# ─── Helper Functions ────────────────────────────────────────────────────────

proc sv_type_for_width {width} {
    if {$width <= 8} {
        return "byte"
    } elseif {$width <= 16} {
        return "shortint unsigned"
    } elseif {$width <= 32} {
        return "int unsigned"
    } elseif {$width <= 64} {
        return "longint unsigned"
    } else {
        return "longint unsigned"
    }
}

proc c_type_for_width {width} {
    if {$width <= 8} {
        return "uint8_t"
    } elseif {$width <= 16} {
        return "uint16_t"
    } elseif {$width <= 32} {
        return "uint32_t"
    } elseif {$width <= 64} {
        return "uint64_t"
    } else {
        return "uint64_t"
    }
}

proc generate_sv_struct_fields {ports u_clk} {
    set max_type_len 0
    set max_pname_len 0
    foreach port $ports {
        set pname [lindex $port 0]
        if {$pname eq $u_clk} continue
        set width [lindex $port 1]
        set svtype [sv_type_for_width $width]
        if {[string length $svtype] > $max_type_len} { set max_type_len [string length $svtype] }
        if {[string length $pname] > $max_pname_len} { set max_pname_len [string length $pname] }
    }
    
    set fields ""
    foreach port $ports {
        set pname [lindex $port 0]
        if {$pname eq $u_clk} continue
        set width [lindex $port 1]
        set svtype [sv_type_for_width $width]
        set t_pad [string repeat " " [expr {$max_type_len - [string length $svtype]}]]
        set p_pad [string repeat " " [expr {$max_pname_len - [string length $pname]}]]
        append fields "    ${svtype}${t_pad}  ${pname}${p_pad};\n"
    }
    return [string trimright $fields "\n"]
}

proc generate_c_struct_fields_list {ports u_clk} {
    set max_type_len 8
    set max_pname_len 0
    foreach port $ports {
        set pname [lindex $port 0]
        if {$pname eq $u_clk} continue
        set width [lindex $port 1]
        set ctype [c_type_for_width $width]
        if {[string length $ctype] > $max_type_len} { set max_type_len [string length $ctype] }
        if {[string length $pname] > $max_pname_len} { set max_pname_len [string length $pname] }
    }
    
    set fields ""
    foreach port $ports {
        set pname [lindex $port 0]
        if {$pname eq $u_clk} continue
        set width [lindex $port 1]
        set ctype [c_type_for_width $width]
        set t_pad [string repeat " " [expr {$max_type_len - [string length $ctype]}]]
        set p_pad [string repeat " " [expr {$max_pname_len - [string length $pname]}]]
        append fields "    ${ctype}${t_pad}  ${pname}${p_pad};\n"
    }
    return [string trimright $fields "\n"]
}

proc generate_first_mapping {in_ports u_clk req_struct_name req_obj_name} {
    set max_pname_len 0
    foreach port $in_ports {
        set pname [lindex $port 0]
        if {$pname eq $u_clk} continue
        if {[string length $pname] > $max_pname_len} { set max_pname_len [string length $pname] }
    }
    set mapping ""
    foreach port $in_ports {
        set pname [lindex $port 0]
        if {$pname eq $u_clk} continue
        set p_pad [string repeat " " [expr {$max_pname_len - [string length $pname]}]]
        append mapping "        ${req_struct_name}.${pname}${p_pad} = ${req_obj_name}.${pname}${p_pad} ;\n"
    }
    return [string trimright $mapping "\n"]
}

proc generate_second_mapping {out_ports resp_obj_name resp_struct_name} {
    set max_pname_len 0
    foreach port $out_ports {
        set pname [lindex $port 0]
        if {[string length $pname] > $max_pname_len} { set max_pname_len [string length $pname] }
    }
    set mapping ""
    foreach port $out_ports {
        set pname [lindex $port 0]
        set p_pad [string repeat " " [expr {$max_pname_len - [string length $pname]}]]
        append mapping "        ${resp_obj_name}.${pname}${p_pad} = ${resp_struct_name}.${pname}${p_pad} ;\n"
    }
    return [string trimright $mapping "\n"]
}

# ─── CASE 1: C Mode (DPI-C) ──────────────────────────────────────────────────

if {[string match "py*" $lang_lower] || [string match "ex*" $lang_lower]} {
    # ─── CASE: Python Mode (Socket + DPI-C) ──────────────────────────────────
    set script_dir [file dirname [info script]]
    source [file join $script_dir "gen_py_protocol_pkg.tcl"]
    source [file join $script_dir "gen_py_protocol_encoder.tcl"]
    source [file join $script_dir "gen_py_protocol_decoder.tcl"]
    source [file join $script_dir "gen_py_reference_model_proxy.tcl"]
    source [file join $script_dir "gen_py_dpi_files.tcl"]
    source [file join $script_dir "gen_py_protocol_py.tcl"]
    source [file join $script_dir "gen_py_reference_model_py.tcl"]
    source [file join $script_dir "gen_py_server_py.tcl"]

    if {$single_agent} {
        set in_ports  [expr {[info exists input_ports_A1] && [llength $input_ports_A1] > 0 ? $input_ports_A1 : ( [info exists input_ports] ? $input_ports : {} )}]
        set out_ports [expr {[info exists output_ports_A1] && [llength $output_ports_A1] > 0 ? $output_ports_A1 : ( [info exists output_ports] ? $output_ports : {} )}]
        set clk_name  [expr {[llength $in_ports] > 0 ? [lindex [lindex $in_ports 0] 0] : "clk"}]
    } else {
        set in_ports {}
        set out_ports {}
        for {set i 1} {$i <= $Num_AC_agent} {incr i} {
            if {[info exists input_ports_A${i}]} {
                foreach p [set input_ports_A${i}] { lappend in_ports $p }
            }
            if {[info exists output_ports_A${i}]} {
                foreach p [set output_ports_A${i}] { lappend out_ports $p }
            }
        }
        for {set i 1} {$i <= $Num_PA_agent} {incr i} {
            if {[info exists input_ports_P${i}]} {
                foreach p [set input_ports_P${i}] { lappend in_ports $p }
            }
            if {[info exists output_ports_P${i}]} {
                foreach p [set output_ports_P${i}] { lappend out_ports $p }
            }
        }
        set clk_name  [expr {[llength $in_ports] > 0 ? [lindex [lindex $in_ports 0] 0] : "clk"}]
    }

    generate_py_protocol_pkg $project_name $ref_dir
    generate_py_protocol_encoder $project_name $ref_dir $in_ports $clk_name
    generate_py_protocol_decoder $project_name $ref_dir $out_ports
    generate_py_reference_model_proxy $project_name $ref_dir $single_agent $all_agents
    generate_py_dpi_files $project_name $ref_dir
    generate_py_protocol_py $project_name $ref_dir
    generate_py_reference_model_py $project_name $ref_dir $in_ports $out_ports $clk_name
    generate_py_server_py $project_name $ref_dir $in_ports $out_ports $clk_name
    return
}

if {[string match "c*" $lang_lower]} {
    file mkdir $c_dir
    set proj_upper [string toupper $project_name]
    set proxy_file "${ref_dir}/${project_name}_reference_model_proxy.sv"
    set c_hdr_file "${c_dir}/${project_name}_reference_model.h"
    set c_src_file "${c_dir}/${project_name}_reference_model.c"
    
    if {$single_agent} {
        set in_ports  [expr {[info exists input_ports_A1] && [llength $input_ports_A1] > 0 ? $input_ports_A1 : ( [info exists input_ports] ? $input_ports : {} )}]
        set out_ports [expr {[info exists output_ports_A1] && [llength $output_ports_A1] > 0 ? $output_ports_A1 : ( [info exists output_ports] ? $output_ports : {} )}]
        set clk_name  [expr {[llength $in_ports] > 0 ? [lindex [lindex $in_ports 0] 0] : "clk"}]
        
        # 1. Update SV Proxy
        if {[file exists $proxy_file]} {
            set fp [open $proxy_file r]; set data [read $fp]; close $fp
            
            set req_fields  [generate_sv_struct_fields $in_ports $clk_name]
            set resp_fields [generate_sv_struct_fields $out_ports $clk_name]
            set m1          [generate_first_mapping $in_ports $clk_name "request_struct" "request"]
            set m2          [generate_second_mapping $out_ports "response" "response_struct"]
            
            set data [string map [list \
                "// Here is Request Struct" $req_fields \
                "// Here is Response Struct" $resp_fields \
                "// Here is First mapping" $m1 \
                "// Here is second mapping" $m2 \
            ] $data]
            
            set fp [open $proxy_file w]; puts -nonewline $fp $data; close $fp
            puts "C Reference Model Proxy updated: $proxy_file"
        }
        
        # 2. Generate C Header (.h)
        set c_req_fields  [generate_c_struct_fields_list $in_ports $clk_name]
        set c_resp_fields [generate_c_struct_fields_list $out_ports $clk_name]
        set h_content ""
        append h_content "#ifndef ${proj_upper}_REFERENCE_MODEL_H\n"
        append h_content "#define ${proj_upper}_REFERENCE_MODEL_H\n\n"
        append h_content "#include <stdint.h>\n"
        append h_content "#include <stdbool.h>\n"
        append h_content "#include <stdio.h>\n"
        append h_content "#include <string.h>\n"
        append h_content "#include \"svdpi.h\"\n\n"
        append h_content "#ifdef __cplusplus\n"
        append h_content "extern \"C\" {\n"
        append h_content "#endif\n\n"
        append h_content "// =====================================================================\n"
        append h_content "// Transaction Struct Definitions (Unpacked & C-Compatible)\n"
        append h_content "// =====================================================================\n"
        append h_content "typedef struct {\n"
        append h_content "${c_req_fields}\n"
        append h_content "} dpi_request_struct;\n\n"
        append h_content "typedef struct {\n"
        append h_content "${c_resp_fields}\n"
        append h_content "} dpi_response_struct;\n\n"
        append h_content "// =====================================================================\n"
        append h_content "// DPI Function Prototypes\n"
        append h_content "// =====================================================================\n"
        append h_content "/**\n"
        append h_content " * @brief Executes one step/transaction of the Reference Model.\n"
        append h_content " * @param request   Pointer to input transaction struct (read-only)\n"
        append h_content " * @param response  Pointer to output transaction struct (written by model)\n"
        append h_content " * @return 0 on SUCCESS, non-zero on ERROR (triggers uvm_error in SV)\n"
        append h_content " */\n"
        append h_content "int REF_execute(const dpi_request_struct* request, dpi_response_struct* response);\n\n"
        append h_content "// Helper function to reset internal model state\n"
        append h_content "void REF_model_reset(void);\n\n"
        append h_content "#ifdef __cplusplus\n"
        append h_content "}\n"
        append h_content "#endif\n\n"
        append h_content "#endif // ${proj_upper}_REFERENCE_MODEL_H\n"
        
        set fp [open $c_hdr_file w]; puts -nonewline $fp $h_content; close $fp
        puts "C Reference Model Header generated: $c_hdr_file"
        
        # 3. Generate C Source (.c)
        set c_content ""
        append c_content "#include \"${project_name}_reference_model.h\"\n\n"
        append c_content "// =====================================================================\n"
        append c_content "// Internal State of the Reference Model\n"
        append c_content "// =====================================================================\n"
        append c_content "typedef struct {\n\n\n"
        append c_content "    // =================================================================================== //\n"
        append c_content "    // =================================================================================== //\n"
        append c_content "    // Write here all signals that should be remembered throughout the function execution. //\n"
        append c_content "    // =================================================================================== //\n"
        append c_content "    // =================================================================================== //\n\n\n"
        append c_content "    uint32_t state_var;\n"
        append c_content "} ref_model_state_t;\n\n"
        append c_content "static ref_model_state_t ref_state = {0};\n\n"
        append c_content "void REF_model_reset(void) {\n"
        append c_content "    memset(&ref_state, 0, sizeof(ref_model_state_t));\n"
        append c_content "}\n\n"
        append c_content "// =====================================================================\n"
        append c_content "// Main DPI Execution Function\n"
        append c_content "// =====================================================================\n"
        append c_content "int REF_execute(const dpi_request_struct* request, dpi_response_struct* response) {\n"
        append c_content "    if (!request || !response) {\n"
        append c_content "        return -1; // Error: Null pointer passed\n"
        append c_content "    }\n\n"
        append c_content "    // 1. Initialize output response struct to 0\n"
        append c_content "    memset(response, 0, sizeof(dpi_response_struct));\n\n\n"
        append c_content "    // ================================== //\n"
        append c_content "    // ================================== //\n"
        append c_content "    // Write here All your Reference Code //\n"
        append c_content "    // ================================== //\n"
        append c_content "    // ================================== //\n\n\n"

        append c_content "    return 0; // Return 0 for SUCCESS\n"
        append c_content "}\n"
        
        set fp [open $c_src_file w]; puts -nonewline $fp $c_content; close $fp
        puts "C Reference Model Source generated: $c_src_file"
        
    } else {
        # Multi-agent C proxy & C files
        
        # 1. Update SV Proxy
        set proxy_data "package ${project_name}_reference_model_proxy_pkg;\nimport uvm_pkg::*;\n`include \"uvm_macros.svh\"\n"
        foreach ag_name $all_agents {
            append proxy_data "import ${project_name}_${ag_name}_sequence_item_pkg::*;\n"
        }
        
        append proxy_data "\n//------------------------------------------------------------\n// Struct Definitions (Unpacked & C-Compatible) & DPI-C Functions\n//------------------------------------------------------------\n"
        
        for {set i 1} {$i <= $Num_AC_agent} {incr i} {
            set aname       [lindex [lindex $active_agent [expr {$i-1}]] 0]
            set in_ports    [expr {[info exists input_ports_A${i}] ? [set input_ports_A${i}] : {}}]
            set out_ports   [expr {[info exists output_ports_A${i}] ? [set output_ports_A${i}] : {}}]
            set clk_name    [expr {[llength $in_ports] > 0 ? [lindex [lindex $in_ports 0] 0] : "clk"}]
            set req_fields  [generate_sv_struct_fields $in_ports $clk_name]
            set resp_fields [generate_sv_struct_fields $out_ports $clk_name]
            
            append proxy_data "typedef struct {\n${req_fields}\n} dpi_${aname}_request_struct;\n\n"
            append proxy_data "typedef struct {\n${resp_fields}\n} dpi_${aname}_response_struct;\n\n"
            append proxy_data "import \"DPI-C\" function int REF_execute_${aname}(\n    input  dpi_${aname}_request_struct  request,\n    output dpi_${aname}_response_struct response\n);\n\n"
        }
        for {set i 1} {$i <= $Num_PA_agent} {incr i} {
            set pname       [lindex [lindex $passive_agent [expr {$i-1}]] 0]
            set in_ports    [expr {[info exists input_ports_P${i}] ? [set input_ports_P${i}] : {}}]
            set out_ports   [expr {[info exists output_ports_P${i}] ? [set output_ports_P${i}] : {}}]
            set clk_name    [expr {[llength $in_ports] > 0 ? [lindex [lindex $in_ports 0] 0] : "clk"}]
            set req_fields  [generate_sv_struct_fields $in_ports $clk_name]
            set resp_fields [generate_sv_struct_fields $out_ports $clk_name]
            
            append proxy_data "typedef struct {\n${req_fields}\n} dpi_${pname}_request_struct;\n\n"
            append proxy_data "typedef struct {\n${resp_fields}\n} dpi_${pname}_response_struct;\n\n"
            append proxy_data "import \"DPI-C\" function int REF_execute_${pname}(\n    input  dpi_${pname}_request_struct  request,\n    output dpi_${pname}_response_struct response\n);\n\n"
        }
        
        append proxy_data "class ${project_name}_reference_model_proxy extends uvm_object;\n\n    `uvm_object_utils(${project_name}_reference_model_proxy)\n\n    function new(string name = \"${project_name}_reference_model_proxy\");\n        super.new(name);\n    endfunction\n\n"
        
        for {set i 1} {$i <= $Num_AC_agent} {incr i} {
            set aname     [lindex [lindex $active_agent [expr {$i-1}]] 0]
            set in_ports  [expr {[info exists input_ports_A${i}] ? [set input_ports_A${i}] : {}}]
            set out_ports [expr {[info exists output_ports_A${i}] ? [set output_ports_A${i}] : {}}]
            set clk_name  [expr {[llength $in_ports] > 0 ? [lindex [lindex $in_ports 0] 0] : "clk"}]
            set item_type "${project_name}_${aname}_sequence_item"
            set m1        [generate_first_mapping $in_ports $clk_name "request_struct" "request"]
            set m2        [generate_second_mapping $out_ports "response" "response_struct"]
            
            append proxy_data "    //------------------------------------------------------------\n"
            append proxy_data "    // Execute for ${aname}\n"
            append proxy_data "    //------------------------------------------------------------\n"
            append proxy_data "    function ${item_type} execute_${aname}(input ${item_type} request);\n\n"
            append proxy_data "        ${item_type}                    response        ;\n"
            append proxy_data "        dpi_${aname}_request_struct     request_struct  ;\n"
            append proxy_data "        dpi_${aname}_response_struct    response_struct ;\n"
            append proxy_data "        int                             status          ;\n\n"
            append proxy_data "        // Map sequence_item --> Request Struct\n${m1}\n\n"
            append proxy_data "        // Call C function\n"
            append proxy_data "           status = REF_execute_${aname}(request_struct, response_struct);\n\n"
            append proxy_data "           if (status != 0) begin\n"
            append proxy_data "               `uvm_error(\"REF_MODEL\", \$sformatf(\"REF_execute_${aname} failed with status %0d\", status));\n"
            append proxy_data "           end\n\n"
            append proxy_data "        // create response\n"
            append proxy_data "           response = ${item_type}::type_id::create(\"response\");\n\n"
            append proxy_data "        // Map Response Struct --> sequence_item\n${m2}\n\n"
            append proxy_data "        return response;\n\n"
            append proxy_data "    endfunction\n\n"
        }
        
        for {set i 1} {$i <= $Num_PA_agent} {incr i} {
            set pname     [lindex [lindex $passive_agent [expr {$i-1}]] 0]
            set in_ports  [expr {[info exists input_ports_P${i}] ? [set input_ports_P${i}] : {}}]
            set out_ports [expr {[info exists output_ports_P${i}] ? [set output_ports_P${i}] : {}}]
            set clk_name  [expr {[llength $in_ports] > 0 ? [lindex [lindex $in_ports 0] 0] : "clk"}]
            set item_type "${project_name}_${pname}_sequence_item"
            set m1        [generate_first_mapping $in_ports $clk_name "request_struct" "request"]
            set m2        [generate_second_mapping $out_ports "response" "response_struct"]
            
            append proxy_data "    //------------------------------------------------------------\n"
            append proxy_data "    // Execute for ${pname}\n"
            append proxy_data "    //------------------------------------------------------------\n"
            append proxy_data "    function ${item_type} execute_${pname}(input ${item_type} request);\n\n"
            append proxy_data "        ${item_type}                    response        ;\n"
            append proxy_data "        dpi_${pname}_request_struct     request_struct  ;\n"
            append proxy_data "        dpi_${pname}_response_struct    response_struct ;\n"
            append proxy_data "        int                             status          ;\n\n"
            append proxy_data "        // Map sequence_item --> Request Struct\n${m1}\n\n"
            append proxy_data "        // Call C function\n"
            append proxy_data "           status = REF_execute_${pname}(request_struct, response_struct);\n\n"
            append proxy_data "           if (status != 0) begin\n"
            append proxy_data "               `uvm_error(\"REF_MODEL\", \$sformatf(\"REF_execute_${pname} failed with status %0d\", status));\n"
            append proxy_data "           end\n\n"
            append proxy_data "        // create response\n"
            append proxy_data "           response = ${item_type}::type_id::create(\"response\");\n\n"
            append proxy_data "        // Map Response Struct --> sequence_item\n${m2}\n\n"
            append proxy_data "        return response;\n\n"
            append proxy_data "    endfunction\n\n"
        }
        
        append proxy_data "endclass\nendpackage\n"
        
        set fp [open $proxy_file w]; puts -nonewline $fp $proxy_data; close $fp
        puts "Multi-Agent C Reference Model Proxy updated: $proxy_file"
        
        # 2. Generate Multi-Agent C Header (.h)
        set h_content ""
        append h_content "#ifndef ${proj_upper}_REFERENCE_MODEL_H\n"
        append h_content "#define ${proj_upper}_REFERENCE_MODEL_H\n\n"
        append h_content "#include <stdint.h>\n"
        append h_content "#include <stdbool.h>\n"
        append h_content "#include <stdio.h>\n"
        append h_content "#include <string.h>\n"
        append h_content "#include \"svdpi.h\"\n\n"
        append h_content "#ifdef __cplusplus\n"
        append h_content "extern \"C\" {\n"
        append h_content "#endif\n\n"
        append h_content "// =====================================================================\n"
        append h_content "// Transaction Struct Definitions (Unpacked & C-Compatible)\n"
        append h_content "// =====================================================================\n"
        
        for {set i 1} {$i <= $Num_AC_agent} {incr i} {
            set aname         [lindex [lindex $active_agent [expr {$i-1}]] 0]
            set in_ports      [expr {[info exists input_ports_A${i}] ? [set input_ports_A${i}] : {}}]
            set out_ports     [expr {[info exists output_ports_A${i}] ? [set output_ports_A${i}] : {}}]
            set clk_name      [expr {[llength $in_ports] > 0 ? [lindex [lindex $in_ports 0] 0] : "clk"}]
            set c_req_fields  [generate_c_struct_fields_list $in_ports $clk_name]
            set c_resp_fields [generate_c_struct_fields_list $out_ports $clk_name]
            
            append h_content "// --- Agent: ${aname} (Active) ---\n"
            append h_content "typedef struct {\n${c_req_fields}\n} dpi_${aname}_request_struct;\n\n"
            append h_content "typedef struct {\n${c_resp_fields}\n} dpi_${aname}_response_struct;\n\n"
        }
        for {set i 1} {$i <= $Num_PA_agent} {incr i} {
            set pname         [lindex [lindex $passive_agent [expr {$i-1}]] 0]
            set in_ports      [expr {[info exists input_ports_P${i}] ? [set input_ports_P${i}] : {}}]
            set out_ports     [expr {[info exists output_ports_P${i}] ? [set output_ports_P${i}] : {}}]
            set clk_name      [expr {[llength $in_ports] > 0 ? [lindex [lindex $in_ports 0] 0] : "clk"}]
            set c_req_fields  [generate_c_struct_fields_list $in_ports $clk_name]
            set c_resp_fields [generate_c_struct_fields_list $out_ports $clk_name]
            
            append h_content "// --- Agent: ${pname} (Passive) ---\n"
            append h_content "typedef struct {\n${c_req_fields}\n} dpi_${pname}_request_struct;\n\n"
            append h_content "typedef struct {\n${c_resp_fields}\n} dpi_${pname}_response_struct;\n\n"
        }
        
        append h_content "// =====================================================================\n"
        append h_content "// DPI Function Prototypes\n"
        append h_content "// =====================================================================\n"
        for {set i 1} {$i <= $Num_AC_agent} {incr i} {
            set aname [lindex [lindex $active_agent [expr {$i-1}]] 0]
            append h_content "int REF_execute_${aname}(const dpi_${aname}_request_struct* request, dpi_${aname}_response_struct* response);\n"
        }
        for {set i 1} {$i <= $Num_PA_agent} {incr i} {
            set pname [lindex [lindex $passive_agent [expr {$i-1}]] 0]
            append h_content "int REF_execute_${pname}(const dpi_${pname}_request_struct* request, dpi_${pname}_response_struct* response);\n"
        }
        
        append h_content "\n// Helper function to reset internal model state\n"
        append h_content "void REF_model_reset(void);\n\n"
        append h_content "#ifdef __cplusplus\n"
        append h_content "}\n"
        append h_content "#endif\n\n"
        append h_content "#endif // ${proj_upper}_REFERENCE_MODEL_H\n"
        
        set fp [open $c_hdr_file w]; puts -nonewline $fp $h_content; close $fp
        puts "Multi-Agent C Reference Model Header generated: $c_hdr_file"
        
        # 3. Generate Multi-Agent C Source (.c)
        set c_content ""
        append c_content "#include \"${project_name}_reference_model.h\"\n\n"
        append c_content "// =====================================================================\n"
        append c_content "// Shared Internal State of the Reference Model\n"
        append c_content "// =====================================================================\n"
        append c_content "typedef struct {\n"
        append c_content "    // Define shared memory, FIFOs, registers across agents\n"
        append c_content "    uint32_t state_var;\n"
        append c_content "} ref_model_state_t;\n\n"
        append c_content "static ref_model_state_t ref_state = {0};\n\n"
        append c_content "void REF_model_reset(void) {\n"
        append c_content "    memset(&ref_state, 0, sizeof(ref_model_state_t));\n"
        append c_content "}\n\n"
        append c_content "// =====================================================================\n"
        append c_content "// DPI Execution Functions\n"
        append c_content "// =====================================================================\n\n"
        
        for {set i 1} {$i <= $Num_AC_agent} {incr i} {
            set aname [lindex [lindex $active_agent [expr {$i-1}]] 0]
            append c_content "// --- Execution for ${aname} (Active) ---\n"
            append c_content "int REF_execute_${aname}(const dpi_${aname}_request_struct* request, dpi_${aname}_response_struct* response) {\n"
            append c_content "    if (!request || !response) {\n"
            append c_content "        return -1;\n"
            append c_content "    }\n\n"
            append c_content "    memset(response, 0, sizeof(dpi_${aname}_response_struct));\n\n"
            append c_content "    // =================================================================\n"
            append c_content "    // >>> USER REFERENCE LOGIC FOR ${aname} STARTS HERE <<<\n"
            append c_content "    // =================================================================\n\n"
            append c_content "    // Read inputs: request-><field>\n"
            append c_content "    // Write outputs: response-><field>\n\n"
            append c_content "    // =================================================================\n"
            append c_content "    // >>> USER REFERENCE LOGIC FOR ${aname} ENDS HERE <<<\n"
            append c_content "    // =================================================================\n\n"
            append c_content "    return 0;\n"
            append c_content "}\n\n"
        }
        for {set i 1} {$i <= $Num_PA_agent} {incr i} {
            set pname [lindex [lindex $passive_agent [expr {$i-1}]] 0]
            append c_content "// --- Execution for ${pname} (Passive) ---\n"
            append c_content "int REF_execute_${pname}(const dpi_${pname}_request_struct* request, dpi_${pname}_response_struct* response) {\n"
            append c_content "    if (!request || !response) {\n"
            append c_content "        return -1;\n"
            append c_content "    }\n\n"
            append c_content "    memset(response, 0, sizeof(dpi_${pname}_response_struct));\n\n"
            append c_content "    // =================================================================\n"
            append c_content "    // >>> USER REFERENCE LOGIC FOR ${pname} STARTS HERE <<<\n"
            append c_content "    // =================================================================\n\n"
            append c_content "    // Read inputs: request-><field>\n"
            append c_content "    // Write outputs: response-><field>\n\n"
            append c_content "    // =================================================================\n"
            append c_content "    // >>> USER REFERENCE LOGIC FOR ${pname} ENDS HERE <<<\n"
            append c_content "    // =================================================================\n\n"
            append c_content "    return 0;\n"
            append c_content "}\n\n"
        }
        
        set fp [open $c_src_file w]; puts -nonewline $fp $c_content; close $fp
        puts "Multi-Agent C Reference Model Source generated: $c_src_file"
    }
    return
}

# ─── CASE 2: SystemVerilog Mode ──────────────────────────────────────────────

set ref_file "${ref_dir}/${project_name}_reference_model.sv"
if {![file exists $ref_file]} {
    puts "Warning: Reference model file not found at $ref_file"
    return
}

if {$single_agent} {
    # Single-agent SV mode is handled by templates
    return
}

# Multi-Agent SV Mode
set fp [open $ref_file r]; set ref_data [read $fp]; close $fp

# Build per-agent execute functions
set ref_funcs ""
foreach ag_name $all_agents {
    set item_type "${project_name}_${ag_name}_sequence_item"
    append ref_funcs "\n\n\n\n"
    append ref_funcs "       //------------------------------------------------------------\n"
    append ref_funcs "       // Execute for ${ag_name}\n"
    append ref_funcs "       //------------------------------------------------------------\n"
    append ref_funcs "       function ${item_type} execute_${ag_name}\n"
    append ref_funcs "       (\n"
    append ref_funcs "           input ${item_type} request\n"
    append ref_funcs "       );\n"
    append ref_funcs "           ${item_type} response;\n\n"
    append ref_funcs "           // ===================================================== //\n"
    append ref_funcs "           // ===================================================== //\n"
    append ref_funcs "           // Write here All your Reference Code for ${ag_name}\n"
    append ref_funcs "           // ===================================================== //\n"
    append ref_funcs "           // ===================================================== //\n"
    append ref_funcs "\n           return response;\n"
    append ref_funcs "       endfunction\n\n"
}

# Remove old single execute block if present
set ref_data [regsub -all {\n[ \t]*//-+\n[ \t]*// Execute\n[ \t]*//-+\n[ \t]*function.*?endfunction} $ref_data ""]

# Inject per-agent execute functions before endclass
set ref_data [regsub {endclass} $ref_data "${ref_funcs}   endclass"]

# Rename generic class name → project-prefixed name
set ref_data [string map [list "reference_model" "${project_name}_reference_model"] $ref_data]

# Build sequence item imports block
set imports "\n"
foreach ag_name $all_agents {
    append imports "   import ${project_name}_${ag_name}_sequence_item_pkg::*;\n"
}

set lines [split $ref_data "\n"]
set index -1
for {set i 0} {$i < [llength $lines]} {incr i} {
    if {[string match "*package ${project_name}_reference_model_pkg;*" [lindex $lines $i]]} {
        set index $i
        break
    }
}
if {$index != -1} {
    set lines [linsert $lines [expr {$index + 1}] $imports]
}
set ref_data [join $lines "\n"]

set fp [open $ref_file w]; puts -nonewline $fp $ref_data; close $fp
puts "Multi-Agent SV Reference model updated: $ref_file"
