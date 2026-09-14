package templete_environment_pkg;

  import uvm_pkg::*;
  import templete_virtual_sequencer_pkg::*;
  import templete_agent_pkg::*;
  import templete_scoreboard_pkg::*;
  import templete_coverage_pkg::*;    // Case_NO_Coverage
  
  `include "uvm_macros.svh"

  class templete_environment extends uvm_env;
     `uvm_component_utils(templete_environment)
   
     // Create Objects
        templete_agent              agent             ;
        templete_virtual_sequencer  virtual_sequencer ;
        templete_scoreboard         scoreboard        ;
        templete_coverage           coverage          ;  // Case_NO_Coverage


     //------------------------------------------------------------
     // Constructor
     //------------------------------------------------------------
     function new(string name = "templete_environment", uvm_component parent = null);
      super.new(name,parent);    
     endfunction



     //------------------------------------------------------------
     // Build phase
     //------------------------------------------------------------
     function void build_phase(uvm_phase phase);
       super.build_phase(phase);
       agent             =  templete_agent::               type_id:: create("agent"              , this);
       virtual_sequencer =  templete_virtual_sequencer::   type_id:: create("virtual_sequencer"  , this);
       scoreboard        =  templete_scoreboard::          type_id:: create("scoreboard"         , this);
       coverage          =  templete_coverage::            type_id:: create("coverage"           , this); // Case_NO_Coverage
     endfunction



     //------------------------------------------------------------
     // Connect phase
     //------------------------------------------------------------
     function void connect_phase(uvm_phase phase);
      super.connect_phase(phase);
       
      // connect virtual sequencer to each agent sequencer
         virtual_sequencer.sequencer = agent.sequencer;

      // Scoreboard
         agent.DUT_analysis_port.connect(scoreboard.DUT_export);
         agent.REF_analysis_port.connect(scoreboard.REF_export);
         
      // Coverage // Case_NO_Coverage
         agent.DUT_analysis_port.connect(coverage.Seq_export  ); // Case_NO_Coverage
     endfunction
  endclass

endpackage

