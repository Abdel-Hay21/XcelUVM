package templete_reference_model_proxy_pkg;
import uvm_pkg::*;
import templete_sequence_item_pkg::*;
`include "uvm_macros.svh"

//------------------------------------------------------------
// DPI Functions (Must be in package scope, not class scope)
//------------------------------------------------------------
import "DPI-C" function int rm_connect();
import "DPI-C" function int rm_disconnect();
import "DPI-C" function int rm_send(input byte packet[1024], input int size);
import "DPI-C" function int rm_receive(output byte packet[1024]);

class templete_reference_model_proxy extends uvm_object;

    `uvm_object_utils(templete_reference_model_proxy)

    //------------------------------------------------------------
    // Constructor
    //------------------------------------------------------------
    function new(string name = "templete_reference_model_proxy");
        super.new(name);
    endfunction


    //------------------------------------------------------------
    // Connect
    //------------------------------------------------------------
    function void connect();

        if(rm_connect() != 0)
            `uvm_fatal("REF_MODEL", "Cannot connect to Python Server")

    endfunction


    //------------------------------------------------------------
    // Disconnect
    //------------------------------------------------------------
    function void disconnect();

        void'(rm_disconnect());

    endfunction


    //------------------------------------------------------------
    // Execute
    //------------------------------------------------------------
    function templete_sequence_item execute
    (
        input templete_sequence_item request
    );

        // Use fixed size arrays for DPI to guarantee contiguous memory layout
        // dynamic arrays can cause svGetArrayPtr to return NULL
           byte packet[1024]           ;
           byte response_packet[1024]  ;
           int  packet_size            ;
        
        // Sequence item response
           templete_sequence_item response;

        // We need a dynamic array for the encoder/decoder, then copy to fixed array
           byte dyn_packet[]   ;
           byte dyn_response[] ;

        //----------------------------------------------------
        // Encode
        //----------------------------------------------------
        protocol_encoder::encode_request(
            request,
            dyn_packet
        );

        packet_size = dyn_packet.size();
        for(int i = 0; i < packet_size; i++) begin
            packet[i] = dyn_packet[i];
        end

        //----------------------------------------------------
        // Send
        //----------------------------------------------------
        void'(rm_send(packet, packet_size));

        //----------------------------------------------------
        // Receive
        //----------------------------------------------------
        void'(rm_receive(response_packet));

        //----------------------------------------------------
        // Decode
        //----------------------------------------------------
        // Find payload size from header to copy back
        // Header: Byte 2 and 3 are payload size
        dyn_response = new[HEADER_SIZE + {response_packet[2], response_packet[3]}];
        for(int i = 0; i < dyn_response.size(); i++) begin
            dyn_response[i] = response_packet[i];
        end

        protocol_decoder::decode_response(
            dyn_response,
            response
        );

        return response;

    endfunction

endclass
endpackage