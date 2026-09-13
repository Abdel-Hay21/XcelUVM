// =====================================================================
// STYLE EXAMPLE A -- Combinational DUT  (e.g. ALU, Adder, Decoder, Mux)
// Use when: output depends ONLY on current inputs (no history needed)
// =====================================================================

package <DUT>_reference_model_pkg;
   import uvm_pkg::*;
   import <DUT>_sequence_item_pkg::*;
   `include "uvm_macros.svh"

   class <DUT>_reference_model extends uvm_object;
       `uvm_object_utils(<DUT>_reference_model)

       function new(string name = "<DUT>_reference_model");
           super.new(name);
       endfunction

       function <DUT>_sequence_item execute(input <DUT>_sequence_item request);
           <DUT>_sequence_item response;
           response = <DUT>_sequence_item::type_id::create("response");

           // Pass-through ALL input/control signals (RULE 3)
           response.rst_n    = request.rst_n;

           // Compute and assign ALL output signals -- never leave any unassigned (RULE 1)
           response.result   = request.operand_a + request.operand_b;
           response.overflow = (request.operand_a[7] == request.operand_b[7]) &&
                               (response.result[7]  != request.operand_a[7]);

           return response;
       endfunction
   endclass
endpackage


// =====================================================================
// STYLE EXAMPLE B -- Sequential DUT WITH CLOCK DIVIDER  (e.g. UART TX)
// Use when: output depends on HISTORY + a sub-counter controls timing.
// KEY PATTERN: baud_counter must reach BAUD_DIV before FSM advances.
// This is the most common sequential DUT pattern -- read RULE 8 carefully.
// =====================================================================

package <DUT>_reference_model_pkg;
   import uvm_pkg::*;
   import <DUT>_sequence_item_pkg::*;
   `include "uvm_macros.svh"

   class <DUT>_reference_model extends uvm_object;
       `uvm_object_utils(<DUT>_reference_model)

       // ---- Clock Divider Register (RULE 8: mandatory for baud-rate DUTs) ----
       localparam int unsigned BAUD_DIV = 16;  // match RTL parameter exactly
       int unsigned baud_counter;              // counts 0..BAUD_DIV-1

       // ---- FSM State Registers (RULE 5: class-level, persist between calls) ----
       typedef enum logic [2:0] {IDLE, START, DATA, PARITY, STOP} fsm_state_t;
       fsm_state_t  current_state;
       int unsigned bit_counter;
       bit [7:0]    shift_reg;
       bit          parity_bit;

       // ---- Output Hold Registers (RULE 8: hold output during baud phase) ----
       bit          last_tx_out;
       bit          last_busy;

       function new(string name = "<DUT>_reference_model");
           super.new(name);
           current_state = IDLE;
           bit_counter   = 0;
           baud_counter  = 0;
           shift_reg     = 8'h00;
           parity_bit    = 1'b0;
           last_tx_out   = 1'b1;
           last_busy     = 1'b0;
       endfunction

       function <DUT>_sequence_item execute(input <DUT>_sequence_item request);
           <DUT>_sequence_item response;
           response = <DUT>_sequence_item::type_id::create("response");

           // Pass-through ALL input/control signals (RULE 3)
           response.rst_n = request.rst_n;

           // Handle reset (RULE 1)
           if (!request.rst_n) begin
               current_state   = IDLE;
               baud_counter    = 0;
               bit_counter     = 0;
               last_tx_out     = 1'b1;
               last_busy       = 1'b0;
               response.tx_out = 1'b1;
               response.busy   = 1'b0;
               return response;
           end

           // ---- RULE 8: Run clock divider FIRST -- before any FSM logic ----
           if (baud_counter < BAUD_DIV - 1) begin
               baud_counter    = baud_counter + 1;
               response.tx_out = last_tx_out;   // hold -- do NOT advance FSM
               response.busy   = last_busy;
               return response;
           end
           baud_counter = 0;   // divider complete -- now advance FSM

           // ---- State Machine (RULE 5, RULE 6) ----
           case (current_state)
               IDLE: begin
                   last_tx_out = 1'b1;
                   last_busy   = 1'b0;
                   if (request.valid_in) begin
                       shift_reg     = request.data_in;
                       parity_bit    = ^request.data_in;
                       current_state = START;
                   end
               end
               START: begin
                   last_tx_out   = 1'b0;
                   last_busy     = 1'b1;
                   bit_counter   = 0;
                   current_state = DATA;
               end
               DATA: begin
                   last_tx_out = shift_reg[bit_counter];
                   last_busy   = 1'b1;
                   if (bit_counter == 7) current_state = PARITY;
                   else                  bit_counter   = bit_counter + 1;
               end
               PARITY: begin
                   last_tx_out   = parity_bit;   // NOT dead code (RULE 2)
                   last_busy     = 1'b1;
                   current_state = STOP;
               end
               STOP: begin
                   last_tx_out   = 1'b1;
                   last_busy     = 1'b0;
                   current_state = IDLE;
               end
               default: begin
                   last_tx_out   = 1'b1;
                   last_busy     = 1'b0;
                   current_state = IDLE;
               end
           endcase

           response.tx_out = last_tx_out;
           response.busy   = last_busy;
           return response;
       endfunction
   endclass
endpackage


// =====================================================================
// STYLE EXAMPLE C -- Memory/Buffer DUT  (e.g. FIFO, RAM, Register File)
// Use when: DUT stores data; outputs depend on STORED HISTORY.
// KEY PATTERN: class-level array + read/write pointers + depth counter.
// =====================================================================

package <DUT>_reference_model_pkg;
   import uvm_pkg::*;
   import <DUT>_sequence_item_pkg::*;
   `include "uvm_macros.svh"

   class <DUT>_reference_model extends uvm_object;
       `uvm_object_utils(<DUT>_reference_model)

       // ---- Memory Storage (RULE 5: class-level storage) ----
       localparam int unsigned DEPTH  = 8;
       localparam int unsigned DATA_W = 8;
       bit [DATA_W-1:0] memory [0:DEPTH-1];
       int unsigned     wr_ptr;
       int unsigned     rd_ptr;
       int unsigned     depth_count;

       function new(string name = "<DUT>_reference_model");
           super.new(name);
           wr_ptr      = 0;
           rd_ptr      = 0;
           depth_count = 0;
           foreach (memory[i]) memory[i] = '0;
       endfunction

       function <DUT>_sequence_item execute(input <DUT>_sequence_item request);
           <DUT>_sequence_item response;
           response = <DUT>_sequence_item::type_id::create("response");

           // Pass-through ALL input/control signals (RULE 3)
           response.rst_n   = request.rst_n;
           response.push    = request.push;
           response.pop     = request.pop;
           response.data_in = request.data_in;

           // Handle reset (RULE 1)
           if (!request.rst_n) begin
               wr_ptr      = 0;
               rd_ptr      = 0;
               depth_count = 0;
               foreach (memory[i]) memory[i] = '0;
               response.data_out = '0;
               response.full     = 1'b0;
               response.empty    = 1'b1;
               response.count    = '0;
               return response;
           end

           // ---- RULE 10: Combinational flags -- compute from current state ----
           response.full  = (depth_count == DEPTH);
           response.empty = (depth_count == 0);
           response.count = depth_count[DATA_W-1:0];

           // ---- RULE 10: Registered data_out -- value at rd_ptr BEFORE pop ----
           response.data_out = memory[rd_ptr];

           // Push: write to wr_ptr, advance pointer
           if (request.push && !response.full) begin
               memory[wr_ptr] = request.data_in;
               wr_ptr         = (wr_ptr + 1) % DEPTH;
               depth_count    = depth_count + 1;
           end

           // Pop: advance rd_ptr
           if (request.pop && !response.empty) begin
               rd_ptr      = (rd_ptr + 1) % DEPTH;
               depth_count = depth_count - 1;
           end

           return response;
       endfunction
   endclass
endpackage
