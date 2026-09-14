package templete_sequence_item_pkg;

  import uvm_pkg::*;
  `include "uvm_macros.svh"


  class templete_sequence_item extends uvm_sequence_item;

// Here write your signals

// Here write your field macros


     function string convert2string();
        return $sformatf("%s", super.convert2string());
     endfunction


     // Here write your Global constraints 
     // Global_Constraint means the constraints that you want to apply to all the sequences
        constraint Global_Constraint{
           // Here write your Global Constraints
        }

// Here write your User constraints
     // USER_Constraint means the constraints that you want to apply to this sequence only
        constraint USER_Constraint{
           // Here write your User Constraints
        }

     //------------------------------------------------------------
     // Constructor
     //------------------------------------------------------------
     function new(string name = "templete_sequence_item");
        super.new(name);
     endfunction

  endclass
endpackage