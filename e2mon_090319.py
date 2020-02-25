##########################################################################################
#                                                                                        #
#                          #### e2monitor    version 1.21 010219####                     #
#                                                                                        #
#      # Python3 script for monitoring twin rate electricity meter flashing LED #        #
#          #  use single LDR connected to Broadcom pin 4 and 1 (pin #1 and pin #7) #     #
#                    #  Graphical display using PyQt4  #                                 #
#           # time stamped energy data saved to e2mon.csv file  #                        #
#   # NEW! -  data saved to e2mon.dat in case of loss of power! #                        #
#                                                                                        #
#          copyright July 28 2018 Stuart Guy - free to use for educational purposes      #
#                                                                                        #
##########################################################################################

# USER CONFIGURABLE SECTION ##############################################################

# Set the cost of electricity unit-(for single rate set peak and offpeak cost to same value)

costpeak=.1531
costoffpeak=.0787
costdaily=.2456
      

# define time switch settings for start and end of peak rate(1) in DECIMAL GMT hours

# ***note start must be numerically less than end time otherwise fault will occur***
    
 
startpeak = 6.5

endpeak = 23.5


# set the range of values to be plotted on graph (does not affect the .csv file record)

plotinterval = 60 # plot interval in seconds

xplot= 500 # x axis - time

yplot=4500 # y axis - power


# set the update rate of the .csv file record in seconds

fileupdate=300




# END OF USER CONFIGURABLE SECTION! ######################################################




###################################################################
#                                                                 #
#   Initialising input pin definitions and csv file for monitoring#
#                                                                 #
###################################################################



# External module imports

import RPi.GPIO as GPIO

import time
from time import gmtime, strftime
import datetime


import csv




# Pin Definitons: using a 20M ohm to 5k ohm LDR across pin #1 and pin #7 (GPIO 4) 


GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme

meterLDR = 4 # Broadcom pin 4 



# Pin Setup:


GPIO.setup(meterLDR, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # meter LDR set as input w/ pull-down



# initialise csv file for electricity monitoring 'a' for append to existing or 'w' to delete and start a new file

with open('e2mon.csv', 'a', newline='') as csvfile:
                
    
            fieldnames = ['time', 'power', 'total peak', 'total offpeak', 'rate now']

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writerow({'time': 'TIME', 'power': '  POWER','total peak':' DAY UNITS','total offpeak':' NIGHT UNITS', 'rate now' : ' RATE'})






print("Monitor started initialise graphics")







###################################################################
#                                                                 #
#   Initialising the ouptut of a live graph in PyQt4              #
#                                                                 #
###################################################################


import sys
import os
from PyQt4 import QtGui
from PyQt4 import QtCore
import functools
import numpy as np
import random as rd
import matplotlib
matplotlib.use("Qt4Agg")
from matplotlib.figure import Figure
from matplotlib.animation import TimedAnimation
from matplotlib.lines import Line2D
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import threading
import time



def setCustomSize(x, width, height):
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(x.sizePolicy().hasHeightForWidth())
    x.setSizePolicy(sizePolicy)
    x.setMinimumSize(QtCore.QSize(width, height))
    x.setMaximumSize(QtCore.QSize(width, height))

''''''

class CustomMainWindow(QtGui.QMainWindow):

    def __init__(self):

        super(CustomMainWindow, self).__init__()

        # Define the geometry of the main window
        self.setGeometry(0, 0, 800, 470)
        self.setWindowTitle("e2mon- GRID POWER EVERY MINUTE in Watts")

        # Create FRAME_A
        self.FRAME_A = QtGui.QFrame(self)
        self.FRAME_A.setStyleSheet("QWidget { background-color: %s }" % QtGui.QColor(210,210,235,255).name())
        self.LAYOUT_A = QtGui.QGridLayout()
        self.FRAME_A.setLayout(self.LAYOUT_A)
        self.setCentralWidget(self.FRAME_A)

        
        # Place the matplotlib figure
        self.myFig = CustomFigCanvas()
        self.LAYOUT_A.addWidget(self.myFig, *(0,1))

        # Add the callbackfunc to ..
        myDataLoop = threading.Thread(name = 'myDataLoop', target = dataSendLoop, daemon = True, args = (self.addData_callbackFunc,))
        myDataLoop.start()

        self.show()

        
    ''''''


    
    def addData_callbackFunc(self, value):
        
        self.myFig.addData(value)



''' End Class '''


class CustomFigCanvas(FigureCanvas, TimedAnimation):

    def __init__(self):

        self.addedData = []


        # The data
        self.xlim = xplot  # adjust the graph x axis 
        self.n = np.linspace(0, self.xlim - 1, self.xlim)
        a = []
        b = []
        a.append(2.0)
        a.append(4.0)
        a.append(2.0)
        b.append(4.0)
        b.append(3.0)
        b.append(4.0)
        self.y = (self.n * 0.0) + 50

        # The window
        self.fig = Figure(figsize=(5,5), dpi=100) #adjust the graph size and resolution
        self.ax1 = self.fig.add_subplot(111)


        # self.ax1 settings
        #self.ax1.set_xlabel('Time (minutes)') # axis labels not used
        #self.ax1.set_ylabel('Power (watts)')
        self.line1 = Line2D([], [], color='blue')
        self.line1_tail = Line2D([], [], color='red', linewidth=2)
        self.line1_head = Line2D([], [], color='red', marker='o', markeredgecolor='r')
        self.ax1.add_line(self.line1)
        self.ax1.add_line(self.line1_tail)
        self.ax1.add_line(self.line1_head)
        self.ax1.set_xlim(0, self.xlim - 1)
        self.ax1.set_ylim(0, yplot) # adjust the  graph  y axis


        FigureCanvas.__init__(self, self.fig)
        TimedAnimation.__init__(self, self.fig, interval = 50, blit = True)

    def new_frame_seq(self):
        return iter(range(self.n.size))

    def _init_draw(self):
        lines = [self.line1, self.line1_tail, self.line1_head]
        for l in lines:
            l.set_data([], [])

    def addData(self, value):
        self.addedData.append(value)

    
    def _step(self, *args):
        # Extends the _step() method for the TimedAnimation class.
        try:
            TimedAnimation._step(self, *args)
        except Exception as e:
            self.abc += 1
            print(str(self.abc))
            TimedAnimation._stop(self)
            pass

    def _draw_frame(self, framedata):
        margin = 2
        while(len(self.addedData) > 0):
            self.y = np.roll(self.y, -1)
            self.y[-1] = self.addedData[0]
            del(self.addedData[0])


        self.line1.set_data(self.n[ 0 : self.n.size - margin ], self.y[ 0 : self.n.size - margin ])
        self.line1_tail.set_data(np.append(self.n[-10:-1 - margin], self.n[-1 - margin]), np.append(self.y[-10:-1 - margin], self.y[-1 - margin]))
        self.line1_head.set_data(self.n[-1 - margin], self.y[-1 - margin])
        self._drawn_artists = [self.line1, self.line1_tail, self.line1_head]



''' End Class '''


# important - this sends data to  GUI in a thread-safe way.

class Communicate(QtCore.QObject):
    data_signal = QtCore.pyqtSignal(float)

def dataSendLoop(addData_callbackFunc):
    # Setup the signal-slot mechanism.
    mySrc = Communicate()
    mySrc.data_signal.connect(addData_callbackFunc)
    

###################################################################
#                                                                 #
# Initialising variables and output file                          #
#                                                                 #
###################################################################



    lastTime = time.time()
    lastintervaltime = time.time()
    lastintervaltime2 = time.time()
    lastintervaltime3 = time.time()
    lastintervaltime4 = time.time()
    day=datetime.datetime.today().weekday()
    date=int(datetime.date.today().strftime("%d"))
    
    
    power = 0

    poweravg = 0
    today = 0
    week=0
    weekcost=0
    daycost=0
    
    
    lastweek=0
    yesterdaycost=0
    lastweekcost=0
    month=0
    monthcost=0
    lastmonth=0
    lastmonthcost=0
    monthestimate=0
    
   
    
    lastday=day
    lastdate=date
   

    
    difference = 0

    lastTime = 0

    
    signal = False
            
    lastsignal = False

    rate=0

    date=0


    

    # number of pulses per watt hour

    meter_constant = 1

    seconds_in_an_hour = 3600
    
    
# read saved power and cost variables and convert to str to float before starting monitor

    col1=0
    col2=0
    col3=0
    col4=0
    col5=0    
    col6=0
    col7=0
    col8=0
    col9=0
    col10=0
    col11=0    
    col12=0
    col13=0
    col14=0
    col15=0
    col16=0
    
   
    with open('e2mon.dat', newline='') as f:
        reader = csv.reader(f)
        for column in reader:
            col1,col2,col3,col4,col5,col6,col7,col8,col9,col10,col11,col12,col13,col14,col15,col16,=(column)
            
    total1=float(col1)
    total2=float(col2)
    today1=float(col3)
    today2=float(col4)
    yesterday=float(col5)
    week1=float(col6)
    week2=float(col7)
    lastweek=float(col8)
    month=float(col9)
    lastmonth=float(col10)
    weekcost=float(col11)
    lastweekcost=float(col12)
    monthcost=float(col13)
    lastmonthcost=float(col14)
    daycost=float(col15)
    yesterdaycost=float(col16)
        


    
# set the totals to sum of peak and offpeak totals

    total = total1 + total2

    lasttotal= total

###############################################################################
#                                                                             #
#      polling LDR for a flash and calculate power and  rate                  #
#                                                                             #
###############################################################################




    print (" ")
    print (" ")
    print (" ")
    print (" ")
    print (" ")
    print (" ")
    print (" ")
    print (" ")
    print (" ")
    print (" ")
    print (" ")
    print (" ")
    
    print("scanning for meter FLASH")      
        


    while True:
        
       
       
       #  detect LDR change of state time interval to calculate power consumed

                
        if (GPIO.input(meterLDR) ==0): # LDR input no flash
    
            signal = False
            
            lastsignal = False
            
        if (GPIO.input(meterLDR) ==1): # LDR input flash
    
            signal = True    
    
        if lastsignal == False and signal == True: # new flash-calculate power

                   
            
            #get gmt hour as a decimal
            
            hour = strftime("%H", gmtime())
            minute = strftime("%M", gmtime())
            gmthour = float(hour)+float(minute)/60
        
            #calculate current rate

            rate = 2
            

            if (gmthour>=startpeak and gmthour<endpeak):
            
                rate = 1

                   
            #get time difference calculate energy
                 
            
            newTime = time.time()

            difference = newTime - lastTime

            if (difference>.2): # only calculate power if real to avoid integer overflow
	    
                power = seconds_in_an_hour / (difference * meter_constant)

                lastTime = newTime
                

            #increment energy totals and cost since last flash (costdaily added at new day )    

                if (rate==1):
                    total1= total1 + .001
                    
                    today1=today1+0.001
                    week1=week1+0.001

                    weekcost= weekcost+(costpeak/1000)

                    daycost= daycost+(costpeak/1000)

                    monthcost= monthcost+(costpeak/1000)
                                          

                if (rate==2):
                    total2= total2 + .001

                    today2=today2+0.001
                    week2=week2+0.001

                    weekcost=weekcost+(costoffpeak/1000)

                    daycost= daycost+(costoffpeak/1000)

                    monthcost= monthcost+(costoffpeak/1000)

                    
                    
                    
                total=total1 + total2

                today=today1+today2

                week=week1+week2

                month=month + .001

                
                                
                
            # display the power and data
            # note-to avoid a high power reading persisting when no flash received for long time  
            # update the display every 20 secs (but without incrementing totals) 
            
       
        if ((time.time()-lastintervaltime2) > 20) or (lastsignal == False and signal == True):

            lastintervaltime2 = time.time()
               
           
            if lastsignal == False and signal == False: # no new flash detected recalculate power to ramp display down

                               
                newTime = time.time()

                difference = newTime - lastTime
                
                powerupdate = seconds_in_an_hour / (difference * meter_constant)

                if (powerupdate < power): #only update power if the result decreases the displayed power!
                    
                    power=powerupdate
                
                
            # print the power and data - arranged for some data to be behind graph 800x600 resolution
            # LXterminal settings are display 40x17 and text size 25 monospace bold,all hide buttons ticked
                    
            
            print (" ")
            print ("  -e2mon----GRID POWER EVERY MINUTE-")
            print (" ")
            
            print   ("RATE NOW:",rate)
            print   ("METER TOTAL={0:.0f}".format(total))
            print   ("       DAY1={0:.0f}".format(total1),"NIGHT2={0:.0f}".format(total2))

            print (" ")                    
            
 
                              
            print ("LAST MONTH {0:.1f}kWh".format(lastmonth)," COST £{0:.2f}".format(lastmonthcost))
            print ("THIS MONTH {0:.1f}kWh".format(month)," COST £{0:.2f}".format(monthcost))
            print ("LAST WEEK  {0:.1f}kWh".format(lastweek)," COST £{0:.2f}".format(lastweekcost))
            print (" ")
            print ("TODAY £{0:.2f}".format(daycost)," YESTERDAY £{0:.2f}".format(yesterdaycost))  

            print ("PROJECTED MONTHLY COST £{0:.2f}".format(monthestimate))
            
            print (" ")                  

            print  (int(power),"Watts TODAY={0:.1f}kWh".format(today),"Y'DAY={0:.1f}kWh".format(yesterday))
  
            print  ("DAY={0:.1f}kWh".format(today1),"NIGHT={0:.1f}kWh".format(today2)," WEEK £{0:.2f}".format(weekcost),)
            print (" ")
            
            

                    
            lastsignal = True
           

         

        time.sleep(.005)  # pause to reduce cpu time - adjust as necessary to ensure no flash is missed
        

        
#  Append power and totals to .csv file at interval to avoid excess of data typically every 5 minutes
#     - note this records average power over interval rather than instantaneous values and as a result
#        the resolution of the values decreases with the interval - meter values are still correct

        interval = fileupdate
            
        if ((time.time()-lastintervaltime3) > interval):

            lastintervaltime3 = time.time()

            poweravg = ((total-lasttotal)*3600/interval)*1000
            
            
            lasttotal = total

                      
            with open('e2mon.csv', 'a', newline='') as csvfile:
                    
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                    
                writer.writerow({'time': time.asctime(), 'power': int(poweravg), 'total peak':int(total1), 'total offpeak':int(total2), 'rate now' : rate})
                        
         
               
                
                
        #  Update costs, power totals and graph display at set interval
        

        interval=plotinterval
        

        if ((time.time()-lastintervaltime4) > interval):
            
            lastintervaltime4 = time.time()


            
            #this section calculates the monthly cost estimate
            
            
            
            monthestimate = (yesterdaycost)*356/12 # use yesterdays cost as default until there is more data for month


 
            if (date > 1) and (lastmonthcost > 0): # if a new month indicated by lastmonth's data saved then
                                                    # update this month's estimate based on monthly costs so far

                monthestimate = (monthcost-daycost)*(356/12)/(date-1)


 


            #reset totals if end of period


            
            day=datetime.datetime.today().weekday() 
            
                  

            if (lastday != day): # it's a newday! reset the days data and add daily standing charge
                
                yesterday=today

                today=0

                today1=0

                today2=0

                    
                yesterdaycost=daycost

                daycost=costdaily

                weekcost=weekcost + costdaily

                monthcost=monthcost + costdaily

                    

                

   
            if ((lastday == 6) and (day == 0)): # it's Monday! reset weeks data

                  
                    lastweek=week
                        
                    week=0

                    week1=0

                    week2=0

 
           
                    lastweekcost=weekcost
                    
                    weekcost=costdaily

            lastday=day
                    
                    
            date=int(datetime.date.today().strftime("%d"))

            

            if ((lastdate >1) and (date == 1)): # it's a new month! reset months data

                               
                lastmonth=month
                    
                month=0

                lastmonthcost=monthcost

                monthcost=0

            lastdate = date
                                
               
                    

 #  save power and cost variables to register file in case of loss of power!
            

            with open('e2mon.dat', 'w', newline='') as csvfile:
                                
                    
                    fieldnames2 = ['total1','total2',
                                   'today1','today2',
                                   'yesterday','week1',
                                   'week2','lastweek',
                                   'month','lastmonth',                                   
                                   'cost','lastweekcost',
                                   'monthcost','lastmonthcost',
                                   'daycost','yesterdaycost',]

                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames2)

                    writer.writerow({'total1':' METER1','total2':'  METER2',
                                    'today1':' DAY1','today2':' DAY2',
                                    'yesterday':' YDAY','week1':'  WK1',
                                    'week2':'  WK2','lastweek':' LASTWK',
                                    'month':' MONTH','lastmonth':' LASTMTH',                                   
                                    'cost':' WKCOST','lastweekcost':' LASTWKCOST',
                                    'monthcost':' MTHCOST','lastmonthcost':' LASTMTHCOST',                                     
                                    'daycost':' DAYCOST','yesterdaycost':' YESTERDAYCOST' })

                    writer.writerow({'total1': '{:0.1f}'.format(total1),'total2': ' {:0.1f}'.format(total2),
                                     'today1': '   {:0.1f}'.format(today1),'today2': '  {:0.1f}'.format(today2),
                                     'yesterday': '   {:0.1f}'.format(yesterday),'week1': '  {:0.1f}'.format(week1),
                                     'week2': '  {:0.1f}'.format(week2),'lastweek': '  {:0.1f}'.format(lastweek),
                                     'month': '  {:0.1f}'.format(month),'lastmonth': '  {:0.1f}'.format(lastmonth),
                                     'cost': '  {:0.2f}'.format(weekcost),'lastweekcost': '   {:0.2f}'.format(lastweekcost),
                                     'monthcost': '   {:0.2f}'.format(monthcost),'lastmonthcost': '   {:0.2f}'.format(lastmonthcost),
                                     'daycost': '   {:0.2f}'.format(daycost),'yesterdaycost': '   {:0.2f}'.format(yesterdaycost)})



                        

 #  and finally update the graph!!!                   

            mySrc.data_signal.emit(power)
            

                           




if __name__== '__main__':
    app = QtGui.QApplication(sys.argv)
    QtGui.QApplication.setStyle(QtGui.QStyleFactory.create('Plastique'))
    myGUI = CustomMainWindow()


    sys.exit(app.exec_())

''''''






























































#          copyright July 28 2018 Stuart Guy - free to use for educational purposes      #
