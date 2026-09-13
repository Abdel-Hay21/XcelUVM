############################################################
# STYLE EXAMPLE A -- Combinational DUT  (e.g. ALU, Adder, Decoder)
# Use when: output depends ONLY on current inputs (no history needed)
############################################################

def execute(rst_n, operand_a, operand_b):
    """
    Combinational reference model. Called once per clock cycle.
    Inputs:  rst_n, operand_a, operand_b
    Outputs: result, overflow
    """
    result   = (operand_a + operand_b) & 0xFF
    overflow = int(((operand_a >> 7) == (operand_b >> 7)) and
                   ((result >> 7)    != (operand_a >> 7)))
    return result, overflow


############################################################
# STYLE EXAMPLE B -- Sequential DUT WITH CLOCK DIVIDER (e.g. UART TX)
# Use when: output depends on HISTORY + sub-counter controls timing.
# KEY PATTERN: baud_counter reaches BAUD_DIV before FSM advances.
############################################################

# ---- Clock Divider Register (RULE 8) ----
BAUD_DIV     = 16       # match RTL parameter exactly
_baud_counter = 0

# ---- FSM State Registers (RULE 5: module-level, persist between calls) ----
_state        = "IDLE"
_bit_counter  = 0
_shift_reg    = 0
_parity_bit   = 0

# ---- Output Hold Registers (RULE 8: hold output during baud phase) ----
_last_tx_out  = 1       # idle line = high
_last_busy    = 0


def reset_model():
    """Call when rst_n goes low."""
    global _baud_counter, _state, _bit_counter, _shift_reg
    global _parity_bit, _last_tx_out, _last_busy
    _baud_counter = 0
    _state        = "IDLE"
    _bit_counter  = 0
    _shift_reg    = 0
    _parity_bit   = 0
    _last_tx_out  = 1
    _last_busy    = 0


def execute(rst_n, data_in, valid_in):
    """
    Sequential (cycle-accurate) reference model. Called once per clock cycle.
    Inputs:  rst_n, data_in (8-bit), valid_in
    Outputs: tx_out (1-bit), busy (1-bit)
    """
    global _baud_counter, _state, _bit_counter, _shift_reg
    global _parity_bit, _last_tx_out, _last_busy

    # Handle reset (RULE 1)
    if not rst_n:
        reset_model()
        return 1, 0   # tx_out=1 (idle high), busy=0

    # ---- RULE 8: Run clock divider FIRST ----
    if _baud_counter < BAUD_DIV - 1:
        _baud_counter += 1
        return _last_tx_out, _last_busy   # hold -- do NOT advance FSM

    _baud_counter = 0   # divider complete -- now advance FSM

    # ---- State Machine (RULE 5, RULE 6) ----
    if _state == "IDLE":
        _last_tx_out = 1
        _last_busy   = 0
        if valid_in:
            _shift_reg  = data_in
            _parity_bit = bin(data_in).count('1') % 2
            _state      = "START"

    elif _state == "START":
        _last_tx_out  = 0       # START bit
        _last_busy    = 1
        _bit_counter  = 0
        _state        = "DATA"

    elif _state == "DATA":
        _last_tx_out = (_shift_reg >> _bit_counter) & 1   # LSB-first
        _last_busy   = 1
        if _bit_counter == 7:
            _state = "PARITY"
        else:
            _bit_counter += 1

    elif _state == "PARITY":
        _last_tx_out = _parity_bit   # NOT dead code (RULE 2)
        _last_busy   = 1
        _state       = "STOP"

    elif _state == "STOP":
        _last_tx_out = 1
        _last_busy   = 0
        _state       = "IDLE"

    else:
        _last_tx_out = 1
        _last_busy   = 0
        _state       = "IDLE"

    return _last_tx_out, _last_busy


############################################################
# STYLE EXAMPLE C -- Memory/Buffer DUT  (e.g. FIFO, RAM, Register File)
# Use when: DUT stores data; outputs depend on STORED HISTORY.
# KEY PATTERN: module-level list as storage + rd/wr pointer management.
############################################################

DEPTH   = 8
DATA_W  = 8

# ---- Memory Storage (RULE 5: module-level) ----
_memory      = [0] * DEPTH
_wr_ptr      = 0
_rd_ptr      = 0
_depth_count = 0


def fifo_reset():
    global _memory, _wr_ptr, _rd_ptr, _depth_count
    _memory      = [0] * DEPTH
    _wr_ptr      = 0
    _rd_ptr      = 0
    _depth_count = 0


def execute_fifo(rst_n, push, pop, data_in):
    """
    FIFO reference model. Called once per clock cycle.
    Inputs:  rst_n, push, pop, data_in
    Outputs: data_out, full, empty, count
    """
    global _memory, _wr_ptr, _rd_ptr, _depth_count

    # Handle reset (RULE 1)
    if not rst_n:
        fifo_reset()
        return 0, 0, 1, 0   # data_out=0, full=0, empty=1, count=0

    # ---- RULE 10: Combinational flags -- compute from current state ----
    full  = int(_depth_count == DEPTH)
    empty = int(_depth_count == 0)
    count = _depth_count

    # ---- RULE 10: Registered data_out -- value at rd_ptr BEFORE pop ----
    data_out = _memory[_rd_ptr]

    # Push: write data_in at wr_ptr, advance pointer
    if push and not full:
        _memory[_wr_ptr] = data_in & ((1 << DATA_W) - 1)
        _wr_ptr          = (_wr_ptr + 1) % DEPTH
        _depth_count    += 1

    # Pop: advance rd_ptr
    if pop and not empty:
        _rd_ptr      = (_rd_ptr + 1) % DEPTH
        _depth_count -= 1

    return data_out, full, empty, count
