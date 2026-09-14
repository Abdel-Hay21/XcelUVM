# =====================================================================
# gen_py_reference_model_py.tcl
# Generates <project_name>_reference_model.py template for Python Golden Model
# =====================================================================

proc generate_py_reference_model_py {project_name ref_dir in_ports out_ports u_clk} {
    set py_dir "${ref_dir}/python"
    if {![file exists $py_dir]} {
        file mkdir $py_dir
    }
    set target_file "${py_dir}/${project_name}_reference_model.py"

    set in_arg_list {}
    set in_doc_lines ""
    foreach port $in_ports {
        set pname [lindex $port 0]
        if {$pname eq $u_clk} continue
        set width [lindex $port 1]
        lappend in_arg_list $pname
        append in_doc_lines "        ${pname}: int (${width}-bit)\n"
    }

    set out_arg_list {}
    set out_doc_lines ""
    set default_assigns ""
    foreach port $out_ports {
        set pname [lindex $port 0]
        set width [lindex $port 1]
        lappend out_arg_list $pname
        append out_doc_lines "        ${pname}: int (${width}-bit)\n"
        append default_assigns "    ${pname} = 0\n"
    }

    set in_args_str [join $in_arg_list ", "]
    set out_return_str [join $out_arg_list ", "]

    set content ""
    append content "############################################################\n"
    append content "# Reference Model for ${project_name}\n"
    append content "############################################################\n\n"
    append content "# Global or class state can be defined here\n"
    append content "# Example: state_register = 0\n\n"
    append content "def execute(${in_args_str}):\n"
    append content "    \"\"\"\n"
    append content "    Algorithmic Reference Model Execution Function.\n\n"
    append content "    Inputs:\n"
    append content $in_doc_lines
    append content "\n    Outputs:\n"
    append content $out_doc_lines
    append content "    \"\"\"\n\n"
    append content "    # =========================================================\n"
    append content "    # TODO: Implement your algorithmic reference logic here\n"
    append content "    # =========================================================\n"
    append content $default_assigns
    append content "\n"
    append content "    return ${out_return_str}\n"

    set fp [open $target_file w]
    puts -nonewline $fp $content
    close $fp
    puts "Python Reference Model template generated: $target_file"
}
