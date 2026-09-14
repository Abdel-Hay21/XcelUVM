package templete_reference_model_proxy_pkg;
import uvm_pkg::*;
import templete_sequence_item_pkg::*;
`include "uvm_macros.svh"

//------------------------------------------------------------
// Struct Definitions (Unpacked & C-Compatible)
//------------------------------------------------------------
typedef struct {
// Here is Request Struct
} dpi_request_struct;

typedef struct {
// Here is Response Struct
} dpi_response_struct;

//------------------------------------------------------------
// DPI Functions
//------------------------------------------------------------
import "DPI-C" function int REF_execute(
    input  dpi_request_struct  request,
    output dpi_response_struct response
);

class templete_reference_model_proxy extends uvm_object;

    `uvm_object_utils(templete_reference_model_proxy)

    //------------------------------------------------------------
    // Constructor
    //------------------------------------------------------------
    function new(string name = "templete_reference_model_proxy");
        super.new(name);
    endfunction



    //------------------------------------------------------------
    // Execute
    //------------------------------------------------------------
    function templete_sequence_item execute(input templete_sequence_item request);

        templete_sequence_item    response        ;
        dpi_request_struct        request_struct  ;
        dpi_response_struct       response_struct ;
        int                       status          ;

        // Map sequence_item --> Request Struct
// Here is First mapping

        // Call C function
           status = REF_execute(request_struct, response_struct);

           if (status != 0) begin
               `uvm_error("REF_MODEL", $sformatf("REF_execute failed with status %0d", status));
           end

        // create response
           response = templete_sequence_item::type_id::create("response");

        // Map Response Struct --> sequence_item
// Here is second mapping

        return response;

    endfunction

endclass
endpackage