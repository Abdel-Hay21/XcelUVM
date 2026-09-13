import re
import os

def parse_sv_ports(filepath):
    """
    Parses a SystemVerilog file to extract top-level module ports.
    Returns a list of dictionaries: [{"name": str, "direction": str, "width": str}]
    """
    if not os.path.exists(filepath):
        return []
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception:
        return []
        
    # Strip comments (line and block)
    text = re.sub(r'//.*', '', text)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    
    # Extract custom type widths from parameter types BEFORE stripping the #(...) block
    # e.g. parameter type dtype = logic [DATA_WIDTH-1:0]  ->  dtype maps to [DATA_WIDTH-1:0]
    custom_types = {}
    type_matches = re.finditer(r'\bparameter\s+type\s+(\w+)\s*=\s*(?:wire|reg|logic|bit)?\s*(\[[^\]]*\])?', text)
    for m in type_matches:
        t_name = m.group(1)
        t_width = m.group(2).strip() if m.group(2) else ""
        # Also resolve known numeric params: DATA_WIDTH -> 32 default
        # If the bracket still has non-numeric content, mark it as parameterized
        custom_types[t_name] = t_width
    
    # Strip parameter blocks like #(parameter N=8, M=4) which might contain commas
    text = re.sub(r'#\s*\(.*?\)', '', text, flags=re.DOTALL)
    
    # Tokenize: grab [...] blocks as single tokens, words, and structural delimiters
    tokens = re.findall(r'\[.*?\]|\b\w+\b|[,;()]', text)
    
    keywords = {'input', 'output', 'inout', 'ref', 'wire', 'reg', 'logic', 'bit', 'signed', 'unsigned', 'module', 'endmodule'}
    skip_words = {'parameter', 'localparam', 'import', 'export', 'typedef', 'class', 'struct', 'enum'}
    
    ports = []
    current_dir = None
    current_width = ""
    skip_mode = False
    current_identifiers = []
    
    i = 0
    while i < len(tokens):
        t = tokens[i]
        
        if t in skip_words:
            skip_mode = True
        elif skip_mode:
            # End skip mode on statement or port list boundaries
            if t == ';' or t == ')':
                skip_mode = False
        else:
            if t in ['input', 'output', 'inout', 'ref']:
                current_dir = t
                current_width = ""
                current_identifiers = []
            elif t.startswith('['):
                current_width = t
            elif t in [',', ';', '(', ')']:
                if current_identifiers and current_dir:
                    ports.append({
                        "name": current_identifiers[-1],
                        "direction": current_dir,
                        "width": current_width
                    })
                current_identifiers = []
                if t in [';', '(', ')']:
                    current_dir = None
            elif t not in keywords:
                # Potential identifier
                if i > 0 and tokens[i-1] == 'module':
                    pass # It's the module name
                elif current_dir:
                    current_identifiers.append(t)
                    # If this identifier is a custom type, grab its width
                    if t in custom_types and custom_types[t]:
                        current_width = custom_types[t]
        i += 1
        
    # Deduplicate while preserving order (to handle non-ANSI redundant declarations)
    seen = set()
    unique_ports = []
    for p in ports:
        if p['name'] not in seen:
            seen.add(p['name'])
            unique_ports.append(p)
            
    return unique_ports

if __name__ == "__main__":
    # For standalone testing
    test_sv = """
    module top #(parameter WIDTH=32) (
        input logic clk,
        input logic rst_n,
        input logic [WIDTH-1:0] data_in,
        output wire [WIDTH-1:0] data_out,
        inout wire sda
    );
        logic internal_sig;
    endmodule
    """
    with open("test_dummy.sv", "w") as f:
        f.write(test_sv)
    
    res = parse_sv_ports("test_dummy.sv")
    for p in res:
        print(p)
    os.remove("test_dummy.sv")
