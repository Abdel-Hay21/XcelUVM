package templete_predictor_pkg;

   import uvm_pkg::*;
   import templete_reference_model_proxy_pkg::*;
   import templete_sequence_item_pkg::*;

   `include "uvm_macros.svh"

   class templete_predictor extends uvm_subscriber #(templete_sequence_item);
      `uvm_component_utils(templete_predictor)

      // Analysis Port for Expected Transaction
         uvm_analysis_port #(templete_sequence_item) expected_port;

      // Reference Model proxy
         templete_reference_model_proxy REF_proxy;

      //------------------------------------------------------------
      // Constructor
      //------------------------------------------------------------
      function new(string name = "templete_predictor", uvm_component parent = null);
         super.new(name, parent);
      endfunction

      //------------------------------------------------------------
      // Build phase
      //------------------------------------------------------------
      function void build_phase(uvm_phase phase);
         super.build_phase(phase);
         expected_port = new("expected_port", this);
           
         // Create the proxy object
            REF_proxy = templete_reference_model_proxy::type_id::create("REF_proxy");
      endfunction

      //------------------------------------------------------------
      // Write
      //------------------------------------------------------------
      // This is called automatically when the Monitor writes a transaction to its analysis port.
      function void write(templete_sequence_item t);
         templete_sequence_item expected_transaction;
      
         `uvm_info("PREDICTOR", {"Received Actual Transaction from Monitor:\n", t.convert2string()}, UVM_HIGH)
              
         // 1. Send Actual Transaction to Reference Model
         // 2. Wait for it to be processed
         // 3. Receive the Expected Transaction
            expected_transaction = REF_proxy.execute(t);
       
         // Send the Expected Transaction to the Scoreboard
            `uvm_info("PREDICTOR", {"Sending Expected Transaction to Scoreboard:\n", expected_transaction.convert2string()}, UVM_HIGH)
            expected_port.write(expected_transaction);
      endfunction

   endclass
endpackage
