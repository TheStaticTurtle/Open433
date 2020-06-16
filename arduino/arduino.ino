#include <RCSwitch.h>

#define BOARD_V01
#include "packets.h"
#include "board_definition.h"

#define BUFFER_SIZE 512

RCSwitch mySwitch = RCSwitch();
received_signal_packet_t packet_received_signal = {"receive_signal",0,0,0,0,0};
ack_packet_t ack_packet = {"ack",0,"hello world"};

uint8_t serial_buffer[BUFFER_SIZE];
uint8_t data_buffer[BUFFER_SIZE];
int bufferCounter = 0;
int dataBufferCounter = 0;
unsigned long last_message = 0;

void setup() {
  Serial.begin(9600);
  mySwitch.enableReceive(digitalPinToInterrupt(PIN_MODULE_RX));  // Receiver on interrupt 0 => that is pin #2
  mySwitch.enableTransmit(PIN_MODULE_TX);
  mySwitch.setRepeatTransmit(3);

  pinMode(PIN_LED_TX,OUTPUT);
  pinMode(PIN_LED_RX,OUTPUT);
  pinMode(PIN_LED_RX,HIGH);
  Serial.println("HELLO");
}

void sendAck() {
    ack_packet.t = millis();
    Serial.println("START"); //Send start marker
    uint8_t payload[sizeof(ack_packet)]; //Create temporary buffer to store the struct
    memcpy(payload,&ack_packet,sizeof(ack_packet)); //copy the struct to the tmp buffer
    for(int i=0;i < sizeof(payload);i++)  Serial.write(payload[i]); //Write the tmp buffer to serial port
    Serial.println("END"); //Send end marker
}

void loop() {
  digitalWrite(PIN_LED_RX,HIGH);
  if (mySwitch.available()) {
    //Assign values to send struct
    packet_received_signal.t        = millis();
    packet_received_signal.decimal  = mySwitch.getReceivedValue();
    packet_received_signal.length   = mySwitch.getReceivedBitlength();
    packet_received_signal.delay    = mySwitch.getReceivedDelay();
    packet_received_signal.protocol = mySwitch.getReceivedProtocol();
    
    Serial.println("START"); //Send start marker
    uint8_t payload[sizeof(packet_received_signal)]; //Create temporary buffer to store the struct
    memcpy(payload,&packet_received_signal,sizeof(packet_received_signal)); //copy the struct to the tmp buffer
    for(int i=0;i < sizeof(payload);i++)  Serial.write(payload[i]); //Write the tmp buffer to serial port
    Serial.println("END"); //Send end marker
    
    mySwitch.resetAvailable();
  }
  
  if(Serial.available()){
    last_message = millis();
    serial_buffer[bufferCounter] = Serial.read();
    
    char* search_start_pointer;
    search_start_pointer = strstr(serial_buffer, "START\r\n"); //Search for the "START\r\n" string in the serial receive buffer
    if (search_start_pointer != NULL) {
      data_buffer[dataBufferCounter] = serial_buffer[bufferCounter]; //Start copying incoming data to the data buffer but offseted so that it can be cast as a struc later
      if(data_buffer[dataBufferCounter-2] == 'E' && data_buffer[dataBufferCounter-1] == 'N' && data_buffer[dataBufferCounter] == 'D') { //Last 3 chars were END -> end of data
        char type[17];  //Create a tmp buffer to store the type of packet received
        memcpy (&type, &data_buffer, 17); //Copy only the first 17bytes to the tmp buffer (See ptype in each struct in packet.h)

        if(strstr(type,"send_decimal")!=NULL) { //SendDecimal packet found
          send_decimal_packet_t *test = (send_decimal_packet_t*) data_buffer; //Cast the data buffer to the struct representing the packet

          digitalWrite(PIN_LED_RX,LOW); //Led blinking
          digitalWrite(PIN_LED_TX,HIGH); 
          mySwitch.setProtocol(test->protocol); //Set the correct protocol according to the received packet
          mySwitch.send(test->decimal, test->length); //Send the value over the air
          digitalWrite(PIN_LED_TX,LOW); //Led blinking
  
          memset(data_buffer  , '\0', sizeof(char)*BUFFER_SIZE ); //Reset both buffers
          memset(serial_buffer, '\0', sizeof(char)*BUFFER_SIZE );
          sendAck();
        }
        if(strstr(type,"rcswitch_conf")!=NULL) { //SendDecimal packet found
          rcswitch_config_t *test = (rcswitch_config_t*) data_buffer; //Cast the data buffer to the struct representing the packet

          mySwitch.setRepeatTransmit(test->repeat);
          #if not defined( RCSwitchDisableReceiving )
          mySwitch.setReceiveTolerance(test->receiveTolerance);
          #endif
          
          memset(data_buffer  , '\0', sizeof(char)*BUFFER_SIZE ); //Reset both buffers
          memset(serial_buffer, '\0', sizeof(char)*BUFFER_SIZE );
          sendAck();
        }
        
        dataBufferCounter = -1; //Reset both buffers counters (-1 needed because of the ++ at the end of the loop)
        bufferCounter = -1;
      }
      dataBufferCounter++;
    }
    bufferCounter++;


    //Security measure. Ensure that the buffer will not overflow if the message. It also reset the buffers if the last message eceived was more than 30sec ago
    if((bufferCounter >= BUFFER_SIZE && dataBufferCounter >= BUFFER_SIZE) || last_message+30000 < millis()) {
      memset(data_buffer  , '\0', sizeof(char)*BUFFER_SIZE );
      memset(serial_buffer, '\0', sizeof(char)*BUFFER_SIZE );
      dataBufferCounter = 0;
      bufferCounter = 0;
    }
  }
}
