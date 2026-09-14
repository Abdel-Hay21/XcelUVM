`timescale 1ns/1ps

import uvm_pkg::*;
import templete_test_pkg::*;

`include "uvm_macros.svh"

module templete_top;
  localparam time CLK_PERIOD = 2ns;

  // Prepare SYSTEM CLOCK
     bit USER_CLK;
     initial USER_CLK = 0;
     always #(CLK_PERIOD/2) USER_CLK = ~USER_CLK;
  
  // Interfaces
     templete_interface     DUT_interface    (      USER_CLK      ) ;   // create templete interface of DUT

  // DUT and Assertions 
     NODUT_COL1  templete_DUT          DUT_PORT_MAP ;   // connect templete interface to DUT


  initial begin
    uvm_config_db#(virtual templete_interface)::set(null, "*", "templete_DUT_interface", DUT_interface);

    run_test("templete_test");
  end
endmodule