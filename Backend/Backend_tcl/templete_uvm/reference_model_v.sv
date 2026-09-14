package templete_reference_model_pkg;
   import uvm_pkg::*;
   import templete_sequence_item_pkg::*;
   `include "uvm_macros.svh"

   class templete_reference_model extends uvm_object;
   
       `uvm_object_utils(templete_reference_model)
    
       //------------------------------------------------------------
       // Constructor
       //------------------------------------------------------------
       function new(string name = "templete_reference_model");
           super.new(name);
       endfunction
   
   
       //------------------------------------------------------------
       // Execute
       //------------------------------------------------------------
       function templete_sequence_item execute
       (
           input templete_sequence_item request
       );
           templete_sequence_item response;
           
           // ================================== //
           // ================================== //
           // Write here All your declarations   //
           // ================================== //
           // ================================== //   



           // Create Item
              response = templete_sequence_item::type_id::create("response");



           // ================================== //
           // ================================== //
           // Write here All your Reference Code //
           // ================================== //
           // ================================== //   
   
           return response;
   
       endfunction
   
   endclass
endpackage