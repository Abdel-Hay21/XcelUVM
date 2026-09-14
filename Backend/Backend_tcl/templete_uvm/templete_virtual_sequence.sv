package templete_virtual_sequence_pkg;

import uvm_pkg::*;

import templete_virtual_sequencer_pkg::*;
import templete_sequence_pkg::*;

`include "uvm_macros.svh"

class templete_virtual_sequence extends uvm_sequence #(uvm_sequence_item);
  `uvm_object_utils(templete_virtual_sequence)
  `uvm_declare_p_sequencer(templete_virtual_sequencer)

  // Class All Sequences
templete_my_sequence        my_seq;



  //------------------------------------------------------------
  // Constructor
  //------------------------------------------------------------
  function new(string name = "templete_virtual_sequence");
    super.new(name);
  endfunction



  //------------------------------------------------------------
  // Body
  //------------------------------------------------------------
  virtual task body();

    if (p_sequencer == null)
      `uvm_fatal("body", "Virtual Sequence - p_sequencer is not set")

    // All Sequences
my_seq           =    templete_my_sequence::      type_id:: create("my_seq");

    // Adapt Repeation of each sequence
       my_seq.repeat_number = TAKE_NUM_FROM_USER ;
    


// my sequence
       `uvm_info("run_phase", "my Asserted"                      , UVM_LOW)
        my_seq.start(p_sequencer.sequencer);         
       `uvm_info("run_phase", "my Deasserted"                    , UVM_LOW)

  endtask
endclass

endpackage


