import serial
import time



ser = serial.Serial('/dev/ttyACM0')  # open serial port
print(ser.name)         # check which port was really used


while(True):
    cmd = input("Enter command or 'exit':")
        	# for Python 3
    if cmd != 'exit':
         ser.write(cmd.encode('ascii'))
         out = ser.readline()
         print(out)
         time.sleep(2)
    elif cmd == 'exit':
         ser.close()
         exit()
