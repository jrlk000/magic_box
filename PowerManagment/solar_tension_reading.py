import urandom
import time
from machine import Pin, DAC, ADC


#create analog signal from digit
#dac_pin = Pin(25, Pin.OUT) Is substituted by the solarpanel as real power source.
#measure analog signal and translate it into a digit
adc_pin = Pin(34, Pin.IN)

#create ADC and DAC objects
#dac = DAC(dac_pin)
adc = ADC(adc_pin)


adc.block().init(bits=12) #map the analog  signal to the set {1, ..., 2¹²}
adc.init(atten=ADC.ATTN_11DB) #allows an interval from [0, 3.3] [V]

while True:
    #dac_value = urandom.getrandbits(8)
    #dac.write(dac_value)
    #time.sleep_ms(5)

    #Write to the REPL USB-serial connection
    #This information gets received by ser.readline()
    print(f"{time.ticks_ms()*1e3},{adc.read_u16()/2**16 * 3.3}")
    time.sleep_ms(5)






