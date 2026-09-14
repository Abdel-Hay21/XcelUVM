package templete_driver_pkg;

  import uvm_pkg::*;
  import templete_sequence_item_pkg::*;

  `include "uvm_macros.svh"

  class templete_driver extends uvm_driver #(templete_sequence_item);
   `uvm_component_utils(templete_driver)

    // virtual interface to DUT & REF
       virtual templete_interface DUT_virtual_interface ;
       virtual templete_interface REF_virtual_interface ;

    // sequence item 
       templete_sequence_item sequence_item;
  


  


  
    //------------------------------------------------------------
    // Constructor
    //------------------------------------------------------------
       function new(string name = "templete_driver", uvm_component parent = null);
         super.new(name,parent);    
       endfunction



    //------------------------------------------------------------
    // Run phase
    //------------------------------------------------------------
    task run_phase(uvm_phase phase);
      super.run_phase(phase);
      forever begin
        sequence_item = templete_sequence_item::type_id::create("sequence_item"); 
        seq_item_port.get_next_item(sequence_item);
        
// virtual_interface_DUT_equal_sequence_item

// virtual_interface_REF_equal_sequence_item

        @(negedge DUT_virtual_interface.USER_CLK);
        seq_item_port.item_done();
      end
    endtask

  endclass
endpackage