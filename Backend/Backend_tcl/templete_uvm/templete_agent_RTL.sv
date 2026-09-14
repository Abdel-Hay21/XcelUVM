package templete_agent_pkg;

import uvm_pkg::*;
import templete_sequence_item_pkg::*;
import templete_config_pkg::*;
import templete_sequencer_pkg::*;
import templete_driver_pkg::*;
import templete_monitor_pkg::*;

`include "uvm_macros.svh"

class templete_agent extends uvm_agent;
  `uvm_component_utils(templete_agent)
  
  // Active or Passive agent
     uvm_active_passive_enum is_active = UVM_ACTIVE;
  
  // Create Object
     templete_sequencer    sequencer ;
     templete_driver       driver    ;
     templete_monitor      monitor   ;
     templete_config       cfg       ;

  // Analysis_port 
     uvm_analysis_port #(templete_sequence_item) DUT_analysis_port ;
     uvm_analysis_port #(templete_sequence_item) REF_analysis_port ;






  //------------------------------------------------------------
  // Constructor
  //------------------------------------------------------------
  function new (string name = "templete_agent", uvm_component parent = null);
    super.new(name, parent);
  endfunction




  //------------------------------------------------------------
  // Build phase
  //------------------------------------------------------------
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    
    if( !uvm_config_db #(templete_config):: get(this,"","CFG", cfg) )
      `uvm_fatal("build_phase", "Agent - Unable to get the virtual interface");
    
    if( is_active == UVM_ACTIVE ) begin
      sequencer  = templete_sequencer:: type_id:: create("sequencer",this) ;
      driver     = templete_driver::    type_id:: create("driver"   ,this) ;
    end 
      monitor    = templete_monitor::   type_id:: create("monitor"  ,this) ;
    
    DUT_analysis_port = new("DUT_analysis_port",this);
    REF_analysis_port = new("REF_analysis_port",this);
  endfunction





  //------------------------------------------------------------
  // Connect phase
  //------------------------------------------------------------
  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
      // Monitor Connection
       // Interface
          monitor.DUT_virtual_interface = cfg.DUT_virtual_interface   ;
          monitor.REF_virtual_interface = cfg.REF_virtual_interface   ;
       // Transaction  
          monitor.DUT_analysis_port.connect(DUT_analysis_port)        ;
          monitor.REF_analysis_port.connect(REF_analysis_port)        ;
       // Driver and Sequencer Connection
        if(is_active == UVM_ACTIVE) begin
          // Interface
             driver.DUT_virtual_interface = cfg.DUT_virtual_interface ;
             driver.REF_virtual_interface = cfg.REF_virtual_interface ;
          // Transaction   
             driver.seq_item_port.connect(sequencer.seq_item_export)  ;
        end
  endfunction
  
endclass
endpackage