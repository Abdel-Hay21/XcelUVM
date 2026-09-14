package templete_monitor_pkg;

  import uvm_pkg::*;
  import templete_sequence_item_pkg::*;

  `include "uvm_macros.svh"

  class templete_monitor extends uvm_monitor;
    `uvm_component_utils(templete_monitor)
     // virtual interface to DUT & REF
        virtual templete_interface DUT_virtual_interface ;
        virtual templete_interface REF_virtual_interface ;


     // sequence item to DUT & REF
        templete_sequence_item DUT_sequence_item ;
        templete_sequence_item REF_sequence_item ; 


     // analysis_port to DUT & REF
        uvm_analysis_port #(templete_sequence_item) DUT_analysis_port ;
        uvm_analysis_port #(templete_sequence_item) REF_analysis_port ;





     //------------------------------------------------------------
     // Constructor
     //------------------------------------------------------------
     function new(string name = "templete_monitor", uvm_component parent = null);
      super.new(name, parent);
     endfunction


     //------------------------------------------------------------
     // Build phase
     //------------------------------------------------------------
     function void build_phase(uvm_phase phase);
       super.build_phase(phase);
       DUT_analysis_port = new("DUT_analysis_port" , this);
       REF_analysis_port = new("REF_analysis_port" , this);
     endfunction


     //------------------------------------------------------------
     // Run phase
     //------------------------------------------------------------
     task run_phase(uvm_phase phase);
       super.run_phase(phase);
       forever begin
         // create sequence_item to DUT & REF
            DUT_sequence_item = templete_sequence_item:: type_id:: create ("DUT_sequence_item");
            REF_sequence_item = templete_sequence_item:: type_id:: create ("REF_sequence_item");

         // Connect sequence item with virtual interface
            @(negedge DUT_virtual_interface.USER_CLK);
// DUT_sequence_item_equal_virtual_interface

// REF_sequence_item_equal_virtual_interface

         // write analysis port to DUT & REF
            DUT_analysis_port.write( DUT_sequence_item );
            REF_analysis_port.write( REF_sequence_item );
       end
     endtask
   
  endclass
endpackage
