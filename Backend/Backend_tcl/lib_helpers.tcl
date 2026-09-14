# ================================================
# lib_helpers.tcl
# Small, reusable helper procs used by every generator stage.
# ================================================

# Reads a template file for a given "stem" (e.g. driver, monitor, seq_item)
# and substitutes the project name + clock name placeholders.
proc read_template {template_dir file_stem project_name user_clk {suffix ""}} {
    set fpath "${template_dir}/templete_${file_stem}${suffix}.sv"
    if {![file exists $fpath]} {
        set fpath "${template_dir}/templete_${file_stem}.sv"
    }
    set fh [open $fpath r]; set data [read $fh]; close $fh
    return [string map [list templete $project_name USER_CLK $user_clk] $data]
}

# Writes data to path, automatically creating parent directories if needed, overwriting any existing file.
proc write_file {path data} {
    set dir [file dirname $path]
    if {![file exists $dir]} {
        file mkdir $dir
    }
    set fh [open $path w]; puts -nonewline $fh $data; close $fh
}

# Right-pads string $s with spaces so it is $w characters wide.
# Used to align columns in generated port maps / module names.
proc _pad {s w} {
    return "${s}[string repeat { } [expr {$w - [string length $s]}]]"
}

# Determines target subdirectory for a template file based on its component stem
proc get_template_subdir {filename} {
    global dir_map
    set comp $filename
    regsub {^templete_} $comp "" comp
    regsub {_SB\.sv$} $comp "" comp
    regsub {_RTL\.sv$} $comp "" comp
    regsub {\.sv$} $comp "" comp
    
    if {[info exists dir_map($comp)]} {
        return $dir_map($comp)
    }
    return "."
}
