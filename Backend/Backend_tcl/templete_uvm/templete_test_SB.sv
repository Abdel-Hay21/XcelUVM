package templete_test_pkg;

import uvm_pkg::*;

import templete_environment_pkg::*;
import templete_agent_pkg::*;
import templete_sequencer_pkg::*;
import templete_virtual_sequence_pkg::*;
import templete_config_pkg::*;

`include "uvm_macros.svh"

class templete_test extends uvm_test;
  `uvm_component_utils(templete_test)
  
  // Class ENVIRONMENT
     templete_environment            environment;
          
  // Class CONFIG           
     templete_config                 cfg;

  // Virtual Sequence
     templete_virtual_sequence       virtual_sequence;



  //------------------------------------------------------------
  // Constructor
  //------------------------------------------------------------
  function new(string name = "templete_test", uvm_component parent = null);
    super.new(name, parent);
  endfunction



  //------------------------------------------------------------
  // Build phase
  //------------------------------------------------------------
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    
    // CFG
       cfg         = templete_config::      type_id:: create("cfg"           ,this);
   
    // Environment
       environment = templete_environment:: type_id:: create("environment"   ,this);


    if(!uvm_config_db #(virtual templete_interface)::get(this,"","templete_DUT_interface", cfg.DUT_virtual_interface))
      `uvm_fatal("build_phase", "Test - unable to get the templete DUT virtual interface from config");


    uvm_config_db #(templete_config)::set(this,"*","CFG", cfg);
  endfunction



  //------------------------------------------------------------
  // Run phase
  //------------------------------------------------------------
  task run_phase(uvm_phase phase);
    super.run_phase       ( phase );
    phase.raise_objection ( this  );

    virtual_sequence = templete_virtual_sequence::type_id::create("virtual_sequence");
    virtual_sequence.start(environment.virtual_sequencer);

    phase.drop_objection(this);
  endtask
endclass

endpackage


