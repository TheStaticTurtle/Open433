#include <RCSwitch.h>

RCSwitch mySwitch = RCSwitch();

// Constants
#define version "0.0.1"

const char _CMD_HELLO             = 'H';
const char _CMD_CHANGE_MODE       = 'M';
const char _CMD_CHANGE_CONFIG     = 'C';

const char _CMD_CONFIG_RETRYS     = 'R';

const char _CMD_TX_START          = 'T';
const char _CMD_COMMAND_END       = '\n';

const char _RESPONSE_SUCESS       = 'S';
const char _RESPONSE_FAIL         = 'F';
const char _RESPONSE_ACK          = 'A';

const char _MODE_IDLE             = '0';
const char _MODE_MONITOR_SIMPLE   = '1';
const char _MODE_MONITOR_ADVANCED = '2';
const char _MODE_TRANSMITTER      = '3';

int current_mode = '0';

#define serial_buffer_size 60
char serial_buffer[serial_buffer_size];
int serial_buffer_i = 0;

void process_serial() {
  if(serial_buffer[0] == _CMD_HELLO) {
    Serial.print("hello ");
    Serial.print(version);
    Serial.write(_CMD_COMMAND_END);
    return;
  }
  if(serial_buffer[0] == _CMD_CHANGE_MODE) {
    current_mode = serial_buffer[1];
    Serial.write(_RESPONSE_ACK);
    Serial.write(_CMD_COMMAND_END);
  }
  if(serial_buffer[0] == _CMD_TX_START && current_mode == _MODE_TRANSMITTER) {
    digitalWrite(PB0, false );
    digitalWrite(PB1, true );
    int packetType = serial_buffer[1];
    if(packetType = _MODE_MONITOR_SIMPLE)  {
      unsigned long value;
      int  bitlenght;
      int  protocol;
      sscanf (serial_buffer,"%*c%*c_%ld_%d_%d",&value,&bitlenght,&protocol);
      mySwitch.setProtocol(protocol);
      mySwitch.send(value, bitlenght);
      
      Serial.write(_RESPONSE_SUCESS);
      Serial.write(_RESPONSE_ACK);
      Serial.write(_CMD_COMMAND_END);
    } else {
      Serial.write(_RESPONSE_FAIL);
      Serial.write(_RESPONSE_ACK);
      Serial.write(_CMD_COMMAND_END);
    }
    digitalWrite(PB0, true  );
    digitalWrite(PB1, false );
  }
  if(serial_buffer[0] == _CMD_CHANGE_CONFIG) {
    if(serial_buffer[1] == _CMD_CONFIG_RETRYS) {
      int  retry_count;
      sscanf (serial_buffer,"%*c%*c%d",&retry_count);
      mySwitch.setRepeatTransmit(retry_count);
      Serial.write(_RESPONSE_ACK);
      Serial.write(_CMD_COMMAND_END);
    }
  }
  
}

void read_serial() {
  if(Serial.available()) {
    char current_char = Serial.read();
    if(current_char == '\n') {
      process_serial();
      memset(serial_buffer,'\0',serial_buffer_size);
      serial_buffer_i = 0;
    } else {
      serial_buffer[serial_buffer_i] = current_char;
      serial_buffer_i = (serial_buffer_i+1) % serial_buffer_size; //Avoid overflowing
    }
  }
}

void read_rf_simple() {
  int value = mySwitch.getReceivedValue();
  if (value == 0) {
      Serial.print("0x0x-1");
      Serial.write(_CMD_COMMAND_END);
  } else {
      Serial.print( mySwitch.getReceivedValue() );
      Serial.print("x");
      Serial.print( mySwitch.getReceivedBitlength() );
      Serial.print("x");
      Serial.print( mySwitch.getReceivedProtocol() );
      Serial.write(_CMD_COMMAND_END);
    }
}


void setup() {
  Serial.begin(9600);
  Serial.println("begin");
  mySwitch.enableReceive(0);
  mySwitch.enableTransmit(10);
  mySwitch.setRepeatTransmit(2);
  pinMode(PB0, OUTPUT);
  pinMode(PB1, OUTPUT);
  digitalWrite(PB0, true );
}

void loop() {
  read_serial();
  
  if (mySwitch.available()) {
    if(current_mode == _MODE_MONITOR_SIMPLE) {
      read_rf_simple();
    }
    mySwitch.resetAvailable();
  }
}
