package templete_virtual_sequencer_pkg;

  import uvm_pkg::*;
  import templete_sequencer_pkg::*;

  `include "uvm_macros.svh"

  class templete_virtual_sequencer extends uvm_sequencer;
    `uvm_component_utils(templete_virtual_sequencer)
  
    templete_sequencer sequencer;

    //------------------------------------------------------------
    // Constructor
    //------------------------------------------------------------
    function new(string name = "templete_virtual_sequencer", uvm_component parent = null);
        super.new(name, parent);
    endfunction
  
  endclass

endpackage