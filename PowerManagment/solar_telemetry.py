import serial
import matplotlib.pyplot as plt
import numpy as np
from collections import deque
import logging

#------- interactive plot must be run inside the terminal to be updated  -------
# realised by cd (change directory inside current folder) and run via python3 filename


#logger configuration
DEBUG = True
logging.basicConfig(
    level=logging.INFO,
	format= '%(filename)s, %(lineno)d - %(message)s'
)

#creatae instance
logger = logging.getLogger("telemetry")

#switch between logger levels
if DEBUG:
    logger.setLevel(logging.DEBUG)

# ----Constants----
PORT = "/dev/ttyUSB0" #serial device on Ubuntu
BAUD = 115200 #serial speed
MAX_POINTS = 200
v_max = 5.0 #max deliverd voltage of the solar-panel

#create object through which python reads incoming data
ser = serial.Serial(PORT, BAUD, timeout=1)
'''
pyserial is used to read data from teh USB serial port

Here:
ESP32 sends text via USB
the PC reads that text through /dev/ttyUSB0
'''
times = deque(range(0, MAX_POINTS), maxlen=MAX_POINTS)
values_adc = deque((k*3.3/2**12 for k in range(0, MAX_POINTS)), maxlen=MAX_POINTS)
#values_dac = deque((k*3.3/2**8 for k in range(0, MAX_POINTS)), maxlen=MAX_POINTS)

# ----Create a live plot ----
plt.ion()
fig, (ax1) = plt.subplots(1, 1)

#Herausnehmen des Linienelementes das geupdatet wird.
line = ax1.plot([], [])
line1 = line[0]

ax1.set_title("DAC produced tension.")
ax1.set_ylabel("Tension [V]")
ax1.set_xlabel("Time [s]")
ax1.set_ylim(0, v_max)
ax1.set_xlim(0, MAX_POINTS-1)
plt.show(block=False)

while True:
    raw = ser.readline().decode(errors='ignore').strip()

    if not raw:
        continue
    try:
        time_str, adc_str = raw.split(',')
        time = int(time_str) # in [s]
        tension = int(adc_str) #bereits in range [0, 3.3V] umgewandelt

    except ValueError as e:
        print(f"Error: {type(e)} occurred while converting the serial data into useful information!")
        continue

    #update the deque containers to update the plot.
    times.append(time)
    values_adc.append(tension)
    #values_dac.append(dac_value * 3.3/2**8)

    #Set values in the plot.
    #line1.set_xdata(list(times)) currently the same time deque will be inserted so we
    # need to change this so the x-axis shows a time interval but shows also the increasing time.
    #logger.debug(times[-1])
    line1.set_ydata(list(values_adc))
    #logger.debug(values_dac[-1])
    #ax1.relim()
    #ax1.autoscale_view(scalex=True, scaley=False)
    fig.canvas.draw()
    fig.canvas.flush_events()
    plt.pause(0.01)



"""
while True:
    #read the information contained in ser
    raw = ser.readline().decode(errors="ignore").strip()
    #print(f"Material contained inside ser: {raw}.")
    #print(f"{repr(raw)}")
    #print(f"{len(raw.split(","))}")

    if not raw:
        continue
    try:
        #print("Entered try block.")
        raw_values = raw.split(",")
        t = int(float(raw_values[0]))
        #dac_value = int(float(raw_values[1])) #8-bits
        #logger.debug(f"dac: {dac_value}")
        adc_value = int(float(raw_values[-1])) #bereits in range [0, 3.3V] umgewandelt
        #logger.debug(f"adc: {adc_value}")
    except ValueError:
        print('Value Error occurred.')
        continue

    #update the deque containers to update the plot.
    times.append(t)
    values_adc.append(adc_value * 3.3/2**12)
    values_dac.append(dac_value * 3.3/2**8)

    #set values inside the plot
    line1.set_xdata(list(range(len(values_dac))))
    #logger.debug(times[-1])
    line1.set_ydata(list(values_dac))
    #logger.debug(values_dac[-1])
    #ax1.relim()
    #ax1.autoscale_view(scalex=True, scaley=False)
    fig.canvas.draw()
    fig.canvas.flush_events()
    print(
         np.array(list(values_dac)[-5:], dtype=float)
          - np.array(line1.get_ydata()[-5:], dtype=float)
        )
    #print(line1.get_ydata()[-5:])
    plt.pause(0.01)"""
