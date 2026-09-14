`define DUT templete_top.templete_DUT
module templete_assertions;

  // properties
     property property_name;
     endproperty
 
  // assery property
     assert property (property_name);

  // cover property
     cover property (property_name);

endmodule
