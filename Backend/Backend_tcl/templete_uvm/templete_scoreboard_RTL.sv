package templete_scoreboard_pkg;

   import uvm_pkg::*;
   import templete_sequence_item_pkg::*;
   
   `include "uvm_macros.svh"

   class templete_scoreboard extends uvm_scoreboard;
      `uvm_component_utils(templete_scoreboard)

      // Define analysis Port & tlm_fifo for DUT
         uvm_analysis_export   #(templete_sequence_item) DUT_export  ;
         uvm_tlm_analysis_fifo #(templete_sequence_item) DUT_fifo    ;
 
      // Define analysis Port & tlm_fifo for REF 
         uvm_analysis_export   #(templete_sequence_item) REF_export  ;
         uvm_tlm_analysis_fifo #(templete_sequence_item) REF_fifo    ;

      // sequence_item for DUT & REF
         templete_sequence_item DUT_sequence_item ;
         templete_sequence_item REF_sequence_item ;

      // counters for correct & error
         int error_count   = 0 ;
         int correct_count = 0 ;






      //------------------------------------------------------------
      // Constructor
      //------------------------------------------------------------
      function new(string name = "templete_scoreboard", uvm_component parent = null);
        super.new(name, parent);
      endfunction



      //------------------------------------------------------------
      // Build phase
      //------------------------------------------------------------
      function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        DUT_export = new("DUT_export" , this);
        REF_export = new("REF_export" , this);
        DUT_fifo   = new("DUT_fifo"   , this);
        REF_fifo   = new("REF_fifo"   , this);
      endfunction



      //------------------------------------------------------------
      // Connect phase
      //------------------------------------------------------------
      function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        DUT_export .connect(DUT_fifo.analysis_export);
        REF_export .connect(REF_fifo.analysis_export);
      endfunction



      //------------------------------------------------------------
      // Run phase
      //------------------------------------------------------------
      task run_phase(uvm_phase phase);
        super.run_phase(phase);
             
        forever begin
         DUT_fifo.get(DUT_sequence_item);
         REF_fifo.get(REF_sequence_item);
                  
         if(/* Output_REF == Output_DUT*/)
         begin
             correct_count++;       
         end
         else begin
              error_count++;
              `uvm_error("run_phase",
               $sformatf(
                 "Time: %0t\n\n================= DUT (Actual) ==================%s================= REF (Expected) ================%s\n",
                 $time,
                 DUT_sequence_item.convert2string(),
                 REF_sequence_item.convert2string()
               )
             );
         end
        end
      endtask



      //------------------------------------------------------------
      // Report phase
      //------------------------------------------------------------
      function void report_phase(uvm_phase phase);
        super.report_phase(phase);
        `uvm_info("report_phase", $sformatf("Total Successful Transactions: %0d", correct_count), UVM_MEDIUM);
        `uvm_info("report_phase", $sformatf("Total Failed Transactions:     %0d", error_count  ), UVM_MEDIUM);
      endfunction


   endclass
endpackage