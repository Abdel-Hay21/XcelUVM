package templete_sequencer_pkg;

  import uvm_pkg::*;
  import templete_sequence_item_pkg::*;

  `include "uvm_macros.svh"

  class templete_sequencer extends uvm_sequencer #(templete_sequence_item);
    `uvm_component_utils(templete_sequencer);

    //------------------------------------------------------------
    // Constructor
    //------------------------------------------------------------
    function new (string name = "templete_sequencer", uvm_component parent = null);
      super.new(name, parent);
    endfunction
  endclass

endpackage