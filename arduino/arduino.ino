#include <RCSwitch.h>

#define ARDUINOJSON_USE_LONG_LONG 1
#include "ArduinoJson.h"

#define BOARD_V01
//#include "packets.h"
#include "board_definition.h"

//#define BUFFER_SIZE 512

RCSwitch mySwitch = RCSwitch();

//ack_packet_t ack_packet = {"ack",0,"hello world"};

//uint8_t serial_buffer[BUFFER_SIZE];
//uint8_t data_buffer[BUFFER_SIZE];
//int bufferCounter = 0;
//int dataBufferCounter = 0;
//unsigned long last_message = 0;

void setup() {
  Serial.begin(9600);
  mySwitch.enableReceive(digitalPinToInterrupt(PIN_MODULE_RX));  // Receiver on interrupt 0 => that is pin #2
  mySwitch.enableTransmit(PIN_MODULE_TX);
  mySwitch.setRepeatTransmit(3);

  pinMode(PIN_LED_TX,OUTPUT);
  pinMode(PIN_LED_RX,OUTPUT);
  pinMode(PIN_LED_RX,HIGH);
  sendAck(0);
}

void sendAck(int for_id) {
    StaticJsonDocument<100> doc;

    if(for_id!=0)  doc["type"]  = "acknowledgement";
    if(for_id==0)  doc["type"]  = "hello_world";
    if(for_id==-1) doc["type"]  = "error";

    doc["time"]                 = millis();
    doc["for_id"]               = for_id;

    serializeJson(doc, Serial);
}

void sendReceivedPacket() {
    StaticJsonDocument<150> doc;
    doc["type"]            = "recived_signal";
    doc["time"]            = millis();
    doc["signal_code"]     = mySwitch.getReceivedValue();;
    doc["signal_lenght"]   = mySwitch.getReceivedBitlength();
    doc["signal_delay"]    = mySwitch.getReceivedDelay();
    doc["signal_protocol"] = mySwitch.getReceivedProtocol();
    serializeJson(doc, Serial);
}

void loop() {
  digitalWrite(PIN_LED_RX,HIGH);
  if (mySwitch.available()) {
    sendReceivedPacket();
    mySwitch.resetAvailable();
  }

  if(Serial.available()){
    StaticJsonDocument<320> doc;
    if( deserializeJson(doc, Serial) == DeserializationError::Ok) {
        if(strstr(doc["type"] , "send_decimal")) {
          digitalWrite(PIN_LED_RX,LOW);
          digitalWrite(PIN_LED_TX,HIGH);

          mySwitch.setProtocol(doc["signal_lenght"].as<int>());
          mySwitch.send(doc["signal_code"].as<unsigned long>(), doc["signal_lenght"].as<int>());

          digitalWrite(PIN_LED_TX,LOW);

          sendAck(doc["id"]);
        }
    } else {
        sendAck(-1);
    }
  }



  /*
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
  */
}
