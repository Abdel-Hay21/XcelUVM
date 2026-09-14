package templete_coverage_pkg;

  import uvm_pkg::*;
  import templete_sequence_item_pkg::*;

  `include "uvm_macros.svh"


  class templete_coverage extends uvm_component;
    `uvm_component_utils(templete_coverage)

    // Define analysis export & tlm_fifo
       uvm_analysis_export   #(templete_sequence_item) Seq_export ;
       uvm_tlm_analysis_fifo #(templete_sequence_item) fifo       ;

    // sequence_item
       templete_sequence_item sequence_item;
    
    // coverage group
       covergroup cover_group;
        //////////////////////////////// 
        //                            //
        //                            //
        // Here write your covergroup //
        //                            //
        //                            //
        //////////////////////////////// 
       endgroup







    //------------------------------------------------------------
    // Constructor
    //------------------------------------------------------------
    function new(string name = "templete_coverage", uvm_component parent = null);
     super.new(name, parent);
     cover_group = new;
    endfunction
    


    //------------------------------------------------------------
    // Build phase
    //------------------------------------------------------------
    function void build_phase(uvm_phase phase);
     super.build_phase(phase);
     Seq_export = new("Seq_export", this);
     fifo       = new("fifo"      , this);
    endfunction
     


    //------------------------------------------------------------
    // Connect phase
    //------------------------------------------------------------
    function void connect_phase(uvm_phase phase);
     super.connect_phase(phase);
     Seq_export.connect(fifo.analysis_export);
    endfunction



    //------------------------------------------------------------
    // Run phase
    //------------------------------------------------------------
    task run_phase(uvm_phase phase);
      super.run_phase(phase);
      forever begin
       fifo.get(sequence_item);
       cover_group.sample();
      end
    endtask
  endclass
endpackage