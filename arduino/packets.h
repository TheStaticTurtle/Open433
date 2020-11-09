typedef struct {
  char ptype[17];
  unsigned long t;
  char msg[32];
} ack_packet_t;

typedef struct {
  char ptype[17];
  unsigned long decimal;
  unsigned int  length;
  unsigned int  delay;
  unsigned int  protocol;
  char end[3];
} send_decimal_packet_t;

typedef struct {
  char ptype[17];
  unsigned int  repeat;
  unsigned int  receiveTolerance;
  char end[3];
} rcswitch_config_t;
