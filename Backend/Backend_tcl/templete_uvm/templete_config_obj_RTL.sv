package templete_config_pkg;

  import uvm_pkg::*;
  
  `include "uvm_macros.svh"

  class templete_config extends uvm_object;
    `uvm_object_utils(templete_config)

    // virtual interface to DUT & REF
       virtual templete_interface DUT_virtual_interface ;
       virtual templete_interface REF_virtual_interface ;



    //------------------------------------------------------------
    // Constructor
    //------------------------------------------------------------
    function new(string name = "templete_config");
      super.new(name);
    endfunction
  endclass

endpackage