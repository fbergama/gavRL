// Install MD_MAX72XX

#include <MD_MAX72xx.h>

#define HARDWARE_TYPE MD_MAX72XX::FC16_HW

#define MAX_DEVICES 4
#define CLK_PIN 13 // or SCK
#define DATA_PIN 11 // or MOSI
#define CS_PIN 10 // or SS


MD_MAX72XX mx = MD_MAX72XX(HARDWARE_TYPE, CS_PIN, MAX_DEVICES);


void setup() 
{ 
  Serial.begin( 115200 );
  while (!Serial);
  mx.begin();
  mx.clear();
}


void loop() {
  if (Serial.available() >= 32 ) 
  {
    byte buffer[32];
    int bytesRead = Serial.readBytes(buffer, 32);

    mx.clear();

    for (uint8_t col=0; col<32; col++)
    {
      //Serial.print("Column "); Serial.print(col); Serial.print(" -> "); Serial.println(buffer[col], HEX );
      mx.setColumn(col, buffer[col]);
    }
  }
}