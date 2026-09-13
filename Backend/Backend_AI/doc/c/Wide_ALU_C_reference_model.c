#include "<DUT>_reference_model.h"

// =====================================================================
// STYLE EXAMPLE A -- Combinational DUT  (e.g. ALU, Adder, Decoder)
// Use when: output depends ONLY on current inputs (no history needed)
// =====================================================================

int REF_execute(const dpi_request_struct* request, dpi_response_struct* response) {
    if (!request || !response) return -1;

    // 1. Initialize ALL output fields to 0 first (RULE 1 baseline)
    memset(response, 0, sizeof(dpi_response_struct));

    // 2. Pass-through control signals (RULE 3)
    response->rst_n = request->rst_n;

    // 3. Compute and assign ALL outputs (RULE 1)
    response->result   = request->operand_a + request->operand_b;
    response->overflow = ((request->operand_a >> 7) == (request->operand_b >> 7)) &&
                         ((response->result   >> 7) != (request->operand_a >> 7));

    return 0;
}


// =====================================================================
// STYLE EXAMPLE B -- Sequential DUT WITH CLOCK DIVIDER  (e.g. UART TX)
// Use when: output depends on HISTORY + sub-counter controls timing.
// KEY PATTERN: baud_counter reaches BAUD_DIV before FSM advances.
// =====================================================================

// ---- Clock Divider (RULE 8) ----
#define BAUD_DIV 16

// ---- FSM State Registers (RULE 5: static, persist between calls) ----
typedef enum { IDLE, START, DATA, PARITY, STOP } fsm_state_t;

typedef struct {
    fsm_state_t  current_state;
    unsigned int baud_counter;   /* RULE 8: clock divider counter */
    unsigned int bit_counter;
    uint8_t      shift_reg;
    uint8_t      parity_bit;
    uint8_t      last_tx_out;   /* RULE 8: hold register */
    uint8_t      last_busy;     /* RULE 8: hold register */
} ref_model_state_t;

static ref_model_state_t ref_state = { IDLE, 0, 0, 0, 0, 1, 0 };

void REF_model_reset(void) {
    ref_state.current_state = IDLE;
    ref_state.baud_counter  = 0;
    ref_state.bit_counter   = 0;
    ref_state.shift_reg     = 0;
    ref_state.parity_bit    = 0;
    ref_state.last_tx_out   = 1;   /* idle line high */
    ref_state.last_busy     = 0;
}

int REF_execute(const dpi_request_struct* request, dpi_response_struct* response) {
    if (!request || !response) return -1;
    memset(response, 0, sizeof(dpi_response_struct));

    // Pass-through (RULE 3)
    response->rst_n = request->rst_n;

    // Handle reset (RULE 1)
    if (!request->rst_n) {
        REF_model_reset();
        response->tx_out = 1;
        response->busy   = 0;
        return 0;
    }

    // ---- RULE 8: Run clock divider FIRST ----
    if (ref_state.baud_counter < BAUD_DIV - 1) {
        ref_state.baud_counter++;
        response->tx_out = ref_state.last_tx_out;   /* hold output */
        response->busy   = ref_state.last_busy;
        return 0;
    }
    ref_state.baud_counter = 0;   /* divider complete -- advance FSM */

    // ---- State Machine (RULE 5, RULE 6) ----
    switch (ref_state.current_state) {

        case IDLE:
            ref_state.last_tx_out = 1;
            ref_state.last_busy   = 0;
            if (request->valid_in) {
                ref_state.shift_reg     = request->data_in;
                ref_state.parity_bit    = __builtin_parity(request->data_in);
                ref_state.current_state = START;
            }
            break;

        case START:
            ref_state.last_tx_out      = 0;
            ref_state.last_busy        = 1;
            ref_state.bit_counter      = 0;
            ref_state.current_state    = DATA;
            break;

        case DATA:
            ref_state.last_tx_out = (ref_state.shift_reg >> ref_state.bit_counter) & 1;
            ref_state.last_busy   = 1;
            if (ref_state.bit_counter == 7) ref_state.current_state = PARITY;
            else                            ref_state.bit_counter++;
            break;

        case PARITY:
            ref_state.last_tx_out      = ref_state.parity_bit;   /* NOT dead code (RULE 2) */
            ref_state.last_busy        = 1;
            ref_state.current_state    = STOP;
            break;

        case STOP:
            ref_state.last_tx_out      = 1;
            ref_state.last_busy        = 0;
            ref_state.current_state    = IDLE;
            break;

        default:
            ref_state.last_tx_out      = 1;
            ref_state.last_busy        = 0;
            ref_state.current_state    = IDLE;
            break;
    }

    response->tx_out = ref_state.last_tx_out;
    response->busy   = ref_state.last_busy;
    return 0;
}


// =====================================================================
// STYLE EXAMPLE C -- Memory/Buffer DUT  (e.g. FIFO, RAM, Register File)
// Use when: DUT stores data; outputs depend on STORED HISTORY.
// KEY PATTERN: static array + rd/wr pointer + depth counter.
// =====================================================================

#define FIFO_DEPTH  8
#define FIFO_DATA_W 8

typedef struct {
    uint8_t      memory[FIFO_DEPTH];
    unsigned int wr_ptr;
    unsigned int rd_ptr;
    unsigned int depth_count;
} fifo_state_t;

static fifo_state_t fifo_state = { {0}, 0, 0, 0 };

void FIFO_reset(void) {
    memset(&fifo_state, 0, sizeof(fifo_state_t));
}

int FIFO_execute(const dpi_request_struct* request, dpi_response_struct* response) {
    if (!request || !response) return -1;
    memset(response, 0, sizeof(dpi_response_struct));

    response->rst_n   = request->rst_n;
    response->push    = request->push;
    response->pop     = request->pop;
    response->data_in = request->data_in;

    if (!request->rst_n) {
        FIFO_reset();
        response->empty = 1;
        return 0;
    }

    /* RULE 10: Combinational flags -- compute from current state */
    response->full  = (fifo_state.depth_count == FIFO_DEPTH);
    response->empty = (fifo_state.depth_count == 0);
    response->count = fifo_state.depth_count;

    /* RULE 10: Registered data_out -- value at rd_ptr BEFORE pop */
    response->data_out = fifo_state.memory[fifo_state.rd_ptr];

    /* Push */
    if (request->push && !response->full) {
        fifo_state.memory[fifo_state.wr_ptr] = request->data_in;
        fifo_state.wr_ptr   = (fifo_state.wr_ptr + 1) % FIFO_DEPTH;
        fifo_state.depth_count++;
    }

    /* Pop */
    if (request->pop && !response->empty) {
        fifo_state.rd_ptr = (fifo_state.rd_ptr + 1) % FIFO_DEPTH;
        fifo_state.depth_count--;
    }

    return 0;
}
