package templete_mysequence_pkg;

  import uvm_pkg::*;
  import templete_sequence_item_pkg::*;

  `include "uvm_macros.svh"
  
  class templete_mysequence extends uvm_sequence #(templete_sequence_item);
    `uvm_object_utils(templete_mysequence)
     templete_sequence_item sequence_item;

    // Num of Repeation
       int repeat_number = 1;

    //------------------------------------------------------------
    // Constructor
    //------------------------------------------------------------
    function new (string name = "templete_mysequence");
      super.new(name);
    endfunction

    //------------------------------------------------------------
    // Body
    //------------------------------------------------------------
    task body;
     repeat(repeat_number) begin
       // Create a new sequence_item
          sequence_item = templete_sequence_item::type_id::create("sequence_item");
           
       // Set the constraint mode
          sequence_item.Global_Constraint.constraint_mode(1);
          sequence_item.USER_Constraint.constraint_mode(1_OR_0);
                  
       // Start, Randomize and Finish the sequence_item
          start_item  ( sequence_item             );
          assert      ( sequence_item.randomize() );
          finish_item ( sequence_item             );
     end
    endtask
  endclass

endpackage
