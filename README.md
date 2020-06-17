# Open433

This project is an opensource usb 433Mhz rf transmitter / receiver based on an atmega328p the board uses a serial communication with a "packet" based systems (simples structs that are sent over the serial port).
The project has a basic but working implementation of a custom component for homeassistant  which is similar to the rpi_rf configuration)

#Building the project
If you just got your own barebone pcbs you just need to flash the arduino bootloader to do that you can use any iscp programmer (or even "arduino as isp") for the bootloader I use the arduino uno bootloader the hardware is using an atmega328p running at 16MHz at 5V.
After that you just have to compile compile and upload the scketch in the arduino folder

#Using the project
## Using the library
If you don't use homeassistant you can see an example in the software folder.


## From homeassistant
If you want to use the board with homeassistant you need to create a `custom_components` folder in the homeassistant configuration directory (same one as the configuration.yaml) then you need to rename the `homeassistant_open433` to `open433` and put it in the `custom_components`.
Then after restarting the server you can add switches like this:
```
switch:
  - platform: open433
    port: COM3
    switches:
      KitchenLamp:
        code_on: 2523794944
        code_off: 2658012672
        protocol: 2
        length: 32
        signal_repetitions: 5
```