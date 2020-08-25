from PyQt4.QtGui import *
from PyQt4.QtCore import *
from sys import *
import sip
import serial
import serial.tools.list_ports
import time
from QLed import QLed
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
from pygame import mixer
from csvReader import *
from scipy.interpolate import CubicSpline
import numpy as np
import traceback

mixer.init()
alert=mixer.Sound('Mario_Jumping.wav')

record = CSVReader()
record.setPath ("newcsv1.csv")

ser = None
	
class Serial_Check (QThread):						#This thread continuously check the availability of comports and also revise the list of comport in main widget.
	def __init__(self):
		super(Serial_Check, self).__init__()
		self.count = 0
	
	def __del__(self):
		self.wait()
	
	def listComportSer (self):				#for retrieving the list of comports from window port file 
		global alert
		#print "Rachit!"
		widget = QWidget ()
		try:
			ports = serial.tools.list_ports.comports()
			comports = list()
			#print "Patel", comports
			numConnection = len(ports)
			#print numConnection
			if numConnection != 0:
				#print "Should not be here!"
				for port in ports:
					#print port
					comports.append ((str(port).split (' '))[0])
					self.count += 1		
				return comports
			elif self.count == 0:
				self.count = 1
				self.emit(SIGNAL('E'), "No port is found!")
				return comports
			else:
				self.count = 1
				return comports
		except BaseException as e:
			if self.count == 0:
				self.emit(SIGNAL('E'), "No Comport is found!")
				count = 1
				return comports
	
	def run (self):
		global error
		global alert
		old = list()
		old_error_csv = error
		time.sleep(2)
		while True:
			new = self.listComportSer()
			#print "Here is a theif!", new
			new_error_csv = error
			if new_error_csv != old_error_csv:
				self.emit(SIGNAL('E'), "Error in CSV File!")
			old_error_csv = new_error_csv
			if new != old:
				#print "Parth "
				self.emit(SIGNAL("5"), new)
			old = new
			time.sleep(1)
		
		
class My_Panel (QMainWindow):							#The main window class
	def __init__(self, parent = None):
		super(My_Panel, self).__init__(parent)
		self.widget = Main_Widget(self)
		self.setCentralWidget (self.widget)
		self.setWindowTitle ("CO2 control Panel")
		self.setGeometry (100, 30, 650, 680)	
	def __del__ (self):
		global ser
		#print "Close!"
		try:
			ser.close()
		except:
			pass

		
class Pulse_Mode (QWidget):						#The class of pulse mode
	def __init__(self, parent):
		self.Count = 0
		self.on = 0
		self.on_clock = 0
		self.time_period = 1000			# 1 millisecond .. 
		self.freq = 1000
		self.power = 1
		self.dutycycle = 1000
		self.power_max = 30				#30 Watt which is maximum power of GEM-30 LASER
		
		global record
		self.duty, self.pwr = record.getData(int(self.freq / 1000))
		x = np.array(self.duty)
		y = np.array(self.pwr)
		self.min_duty = float(8.0 * 100 / self.time_period)
		self.max_duty = 72 				# Dial Maximum Limit
		self.min_power = CubicSpline(x, y)(self.min_duty)
		self.max_power = CubicSpline(x, y)(self.max_duty)
		self.power = self.min_power
		self.dutycycle = self.min_duty
		self.on = self.dutycycle * self.time_period / 100					#self.on is on time of pulse in Micro Seconds
		self.on_clock = int((self.on - 7.67) * 1000 / 62.5) - 1									#on_clock is appropriate number of clock used to generate same time in arduino.
		
		
		super(Pulse_Mode, self).__init__(parent)		
		label = QLabel ("<font color=maroon size=7><b>Pulse Mode</b></font>")
		self.Power_Label = QLabel ("<font size=5><b>POWER (Watt)</b></font>")
		self.Power_Spin = QDoubleSpinBox(self)
		self.Power_Spin.setStyleSheet ("color : red; font : bold 20px; font-family: MS Sans Serif")
		self.Power_Spin.setRange(self.min_power, self.max_power)
		self.Power_Spin.setValue(0)
		self.Power_Dial = QDial(self)			#Virtual Power Nobe of Power value
		self.Power_Dial.setRange((self.min_power*10), (self.max_power*10))
		self.Power_Dial.setNotchesVisible (True)
		
		self.Frequency_Label =QLabel ("<font size=5><b>FREQUENCY (kHz)</b></font>")
		self.Frequency_Spin = QDoubleSpinBox(self)
		self.Frequency_Spin.setStyleSheet ("color : blue; font : bold 20px; font-family: MS Sans Serif")
		self.Frequency_Spin.setRange(1, 25)
		self.Frequency_Spin.setValue (1)
		self.Frequency_Dial = QDial(self)			#virtual Frequency nobe for Frequency value
		self.Frequency_Dial.setRange(1,25)
		self.Frequency_Dial.setNotchesVisible (True)
		self.Frequency_Dial.setValue (1)
		
		#self.Load = QPushButton ("LOAD")
		#self.Load.setStyleSheet ("color : Black; background-color: #6FF31F; font : bold 16px; font-family: Lucida Console; height: 20px")
		#self.Reset = QPushButton ("RESET")
		#self.Reset.setStyleSheet ("color : Black; background-color: #00FBFF; font : bold 16px; font-family: Lucida Console; height: 20px")
		self.Run = QPushButton ("Run")
		self.Run.setStyleSheet ("color : Black; background-color: #FF00DC; font : bold 16px; font-family: Lucida Console; height: 20px")
				
		control_struct = QGridLayout()
		control_struct.addWidget (self.Power_Label, 0, 2, 1, 4)
		control_struct.addWidget (self.Power_Dial, 1, 0, 8, 8)
		control_struct.addWidget (self.Power_Spin, 9, 2, 1, 4)
		control_struct.addWidget (self.Frequency_Label, 0, 11, 1, 8)
		control_struct.addWidget (self.Frequency_Dial, 1, 9, 8, 8)
		control_struct.addWidget (self.Frequency_Spin, 9, 11, 1, 4)
		
		Layout = QGridLayout()
		Layout.addWidget (label, 0, 0, 1, 17)
		Layout.addLayout (control_struct, 1, 0, 10, 17)
		#Layout.addWidget (self.Load, 12, 7)
		#Layout.addWidget (self.Reset, 12, 8)
		Layout.addWidget (self.Run, 12, 9)
		
		self.setLayout(Layout)
		
		self.connect (self.Power_Dial, SIGNAL("valueChanged(int)"), self.UpdatePulse1_1)
		self.connect (self.Power_Spin, SIGNAL("valueChanged(double)"), self.UpdatePulse1_2)
		self.connect (self.Frequency_Dial, SIGNAL("valueChanged(int)"), self.UpdatePulse2)
		self.connect (self.Frequency_Spin, SIGNAL("valueChanged(double)"), self.UpdatePulse2)
		self.connect (self.Run, SIGNAL("clicked()"), self.LaserStart)
		
	def UpdatePulse1_1 (self, val):
		global record
		self.Power_Spin.setValue(float(val)/10)
		self.power = val/10
				
	def UpdatePulse1_2 (self, val):
		global record
		self.Power_Dial.setValue(float(val*10))
		self.power = val
		
	def UpdatePulse2 (self, val):
		global record
		self.duty, self.pwr = record.getData(int(val))
		self.Frequency_Dial.setValue (val)
		self.Frequency_Spin.setValue (float(val))
		self.freq = val * 1000
		self.time_period = 1000000 / self.freq				#here the time period is in microsecond
		
		self.duty, self.pwr = record.getData(int(self.freq/1000))
		x = np.array(self.duty)
		y = np.array(self.pwr)
		self.min_duty = float(8.0 * 100 / self.time_period)
		self.max_duty = float((self.time_period - 12) * 100 / self.time_period)
		self.min_power = CubicSpline(x, y)(self.min_duty)
		self.max_power = CubicSpline(x, y)(self.max_duty)
		self.Power_Spin.setRange(self.min_power, self.max_power)
		self.Power_Dial.setRange((self.min_power*10), (self.max_power*10))				
	
	def	ResetData (self):
		global ser
		self.Power_Dial.setValue (0)
		self.Power_Spin.setValue (0)
		self.Frequency_Dial.setValue (1)
		self.Frequency_Spin.setValue (1)
		self.power = 1
		self.freq = 1000
		self.on = 0
		self.on_clock = 0
		self.time_period = 1000
		self.Count = 0
		
	
	def LaserStart (self):
		global ser
		self.duty, self.pwr = record.getData(int(self.freq/1000))
		
		x = np.array (self.pwr)
		y = np.array (self.duty)
		self.dutycycle = CubicSpline(x, y)(self.power)
		self.on = self.dutycycle * self.time_period / 100						#self.on is on time of pulse in Micro Seconds
		self.on_clock = int((self.on - 7.67) * 1000 / 62.5) - 1							#on_clock is appropriate number of clock used to generate same time in arduino.
		if self.Count == 0:
			s = "M1;O"+str(int(self.on_clock))+";"+"\nS"
			try:
				if ser.isOpen() == False:
					ser.open()
				ser.write (s.encode("utf-8"))
				self.Count +=1
			except BaseException as e:
				self.emit(SIGNAL('E'), str(e))
		else:
			s = "R\n"+"M1;O"+str(int(self.on_clock))+";"+"\nS"
			try:
				if ser.isOpen() == False:
					ser.open()
				ser.write (s.encode("utf-8"))
				self.Count +=1
			except BaseException as e:
				self.emit(SIGNAL('E'), str(e))
		
		
class Continuous_Mode (QWidget):
	def __init__(self, parent):
		self.on_clock = 0
		self.off_clock = 0
		self.time_period = 1000				#1 millisecond
		self.freq = 1000
		self.power = 1
		self.power_max = 30				#30 Watt which is maximum power of GEM-30 LASER  
		global record
		self.duty, self.pwr = record.getData(int(self.freq / 1000))
		x = np.array(self.duty)
		y = np.array(self.pwr)
		self.min_duty = float(8.0 * 100 / self.time_period)
		self.max_duty = 72
		self.min_power = CubicSpline(x, y)(self.min_duty)
		self.max_power = CubicSpline(x, y)(self.max_duty)
		self.power = self.min_power
		self.dutycycle = self.min_duty
		self.on = self.dutycycle * self.time_period / 100					#self.on is on time of pulse in Micro Seconds
		self.on_clock = int((self.on - 7.67) * 1000 / 62.5) - 1									#on_clock is appropriate number of clock used to generate same time in arduino.
		self.off = self.time_period - self.on
		self.off_clock = int((self.off - 11)*1000 / 62.5) -1
				
		super(Continuous_Mode, self).__init__(parent)
		
		label = QLabel ("<font color=maroon size=10><b>Continuous Mode</b></font>")
		self.Power_Label = QLabel ("<font size=5><b>POWER (Watt)</b></font>")
		self.Power_Spin = QDoubleSpinBox(self)
		self.Power_Spin.setStyleSheet ("color : red; font : bold 20px; font-family: MS Sans Serif")
		self.Power_Spin.setRange(self.min_power, self.max_power)
		self.Power_Spin.setValue(0)
		self.Power_Dial = QDial(self)			#Virtual Power Nobe of Power value
		self.Power_Dial.setRange((self.min_power*10), (self.max_power*10))
		
 		self.Power_Dial.setNotchesVisible (True)
		
		self.Frequency_Label =QLabel ("<font size=5><b>FREQUENCY (kHz)</b></font>")
		self.Frequency_Spin = QDoubleSpinBox(self)
		self.Frequency_Spin.setStyleSheet ("color : blue; font : bold 20px; font-family: MS Sans Serif")
		self.Frequency_Spin.setRange(1, 25)
		self.Frequency_Spin.setValue (1)
		self.Frequency_Dial = QDial(self)			#virtual Frequency nobe for Frequency value
		self.Frequency_Dial.setRange(1, 25)
		self.Frequency_Dial.setNotchesVisible (True)
		
		self.Start = QPushButton ("START")
		self.Start.setStyleSheet ("color : Black; background-color: #FF00DC; font : bold 16px; font-family: Lucida Console; height: 20px")
		self.Stop = QPushButton ("STOP")
		self.Stop.setStyleSheet ("color : Black; background-color: #FF1700; font : bold 16px; font-family: Lucida Console; height: 20px")
		
		control_struct = QGridLayout()
		control_struct.addWidget (self.Power_Label, 0, 2, 1, 4)
		control_struct.addWidget (self.Power_Dial, 1, 0, 8, 8)
		control_struct.addWidget (self.Power_Spin, 9, 2, 1, 4)
		control_struct.addWidget (self.Frequency_Label, 0, 11, 1, 8)
		control_struct.addWidget (self.Frequency_Dial, 1, 9, 8, 8)
		control_struct.addWidget (self.Frequency_Spin, 9, 11, 1, 4)
		
		Layout = QGridLayout()
		Layout.addWidget (label, 0, 0, 1, 17)
		Layout.addLayout (control_struct, 1, 0, 10, 17)
		Layout.addWidget (self.Start, 12, 8)
		Layout.addWidget (self.Stop, 12, 9)
		
		self.Stop.setStyleSheet ("color : Black; background-color: #B8B8B8; font : bold 16px; font-family: Lucida Console; height: 20px")
		self.Stop.setEnabled(False)
		
		self.setLayout(Layout)
		
		self.connect (self.Power_Dial, SIGNAL("valueChanged(int)"), self.UpdatePulse1_1)
		self.connect (self.Power_Spin, SIGNAL("valueChanged(double)"), self.UpdatePulse1_2)
		self.connect (self.Frequency_Dial, SIGNAL("valueChanged(int)"), self.UpdatePulse2)
		self.connect (self.Frequency_Spin, SIGNAL("valueChanged(double)"), self.UpdatePulse2)
		self.connect (self.Start, SIGNAL("clicked()"), self.LaserStart)
		self.connect (self.Stop, SIGNAL ("clicked()"), self.LaserStop)
		
	def UpdatePulse1_1 (self, val):
		global record
		self.Power_Spin.setValue(float(val)/10)
		self.power = val/10.0
		
	def UpdatePulse1_2 (self, val):
		global record
		self.Power_Dial.setValue(float(val*10.0))
		self.power = val
	
	def UpdatePulse2 (self, val):
		global record
		self.Frequency_Dial.setValue (val)
		self.Frequency_Spin.setValue (float(val))
		self.freq = val * 1000
		self.time_period = 1000000 / self.freq				#here the time period is in microsecond
		
		self.duty, self.pwr = record.getData(int(self.freq/1000))
		x = np.array(self.duty)
		y = np.array(self.pwr)
		self.min_duty = float(8.0 * 100 / self.time_period)
		self.max_duty = float((self.time_period - 12) * 100 / self.time_period)
		self.min_power = CubicSpline(x, y)(self.min_duty)
		self.max_power = CubicSpline(x, y)(self.max_duty)
		self.Power_Spin.setRange(self.min_power, self.max_power)
		self.Power_Dial.setRange((self.min_power*10), (self.max_power*10))
			
	def	ResetData (self):
		global ser
		self.Power_Dial.setValue (0)
		self.Power_Spin.setValue (0)
		self.Frequency_Dial.setValue (1)
		self.Frequency_Spin.setValue (1)
		self.power = 0
		self.freq = 1000
		self.on = 0
		self.off = 0
		self.on_clock = 0
		self.off_clock = 0
		self.time_period = 1000
		self.Count = 0
	
	def LaserStart (self):
		global ser
		self.duty, self.pwr = record.getData(int(self.freq/1000))
		
		x = np.array (self.pwr)
		y = np.array (self.duty)
		self.dutycycle = CubicSpline(x, y)(self.power)
		self.on = self.dutycycle * self.time_period / 100					#self.on is on time of pulse in Micro Seconds
		self.on_clock = int(float(self.on - 7.67) * 1000 / 62.5) - 1									#on_clock is appropriate number of clock used to generate same time in arduino.
		self.off = self.time_period - self.on
		self.off_clock = int((self.off - 11)*1000 / 62.5) -1
	
		s = "R\nM2;O"+str(int(self.on_clock))+";F"+str(int(self.off_clock))+";\nS"
		print "On:", self.on_clock
		print "Off:",self.off_clock
		print "On Time:", self.on
		print "Off Time:", self.off
		print "Minimum Duty:", self.min_duty
		print "Minimum Power:",self.min_power
		print "Maximum Duty:", self.max_duty
		print "Maximum Power:", self.max_power
		print "Duty cycle:", self.dutycycle
		print "Time Period:", self.time_period
		try:
			if ser.isOpen() == False:
				ser.open()
			ser.write (s.encode("utf-8"))
			#ser.close()
			self.Start.setStyleSheet ("color : Black; background-color: #B8B8B8; font : bold 16px; font-family: Lucida Console; height: 20px")
			self.Start.setEnabled (False)
			self.Stop.setStyleSheet ("color : Black; background-color: #FF1700; font : bold 16px; font-family: Lucida Console; height: 20px")
			self.Stop.setEnabled (True)
		except BaseException as e:
			#ser.close()
			self.emit(SIGNAL('E'), str(e))
				
	def LaserStop (self):
		global ser
		try:
			if ser.isOpen() == False:
				ser.open()
			ser.write (('X\nR'.encode("utf-8")))
			#ser.close()
			self.Stop.setEnabled (False)
			self.Stop.setStyleSheet ("color : Black; background-color: #B8B8B8; font : bold 16px; font-family: Lucida Console; height: 20px")
			self.Start.setEnabled(True)
			self.Start.setStyleSheet ("color : Black; background-color: #FF00DC; font : bold 16px; font-family: Lucida Console; height: 20px")
		except BaseException as e:
			#ser.close()
			self.emit(SIGNAL('E'), str(e))

	
class Burst_Mode (QWidget):
	def __init__(self, parent):
		self.on = 0
		self.off = 0
		self.on_clock = 0
		self.off_clock = 0
		self.time_period = 1000			# 1 millisecond
		self.dutycycle = 0
		self.freq = 1000
		self.power = 1
		self.power_max = 30				#30 Watt which is maximum power of GEM-30 LASER 
		self.bursts = 1
		global record
		self.duty, self.pwr = record.getData(int(self.freq / 1000))
		x = np.array(self.duty)
		y = np.array(self.pwr)
		self.min_duty = float(8.0 * 100 / self.time_period)
		self.max_duty = 72
		self.min_power = CubicSpline(x, y)(self.min_duty)
		self.max_power = CubicSpline(x, y)(self.max_duty)
		self.power = self.min_power
		self.dutycycle = self.min_duty
		self.on = self.dutycycle * self.time_period / 100					#self.on is on time of pulse in Micro Seconds
		self.on_clock = int((self.on - 7.67) * 1000 / 62.5) - 1									#on_clock is appropriate number of clock used to generate same time in arduino.
		self.off = self.time_period - self.on
		self.off_clock = int((self.off - 18)*1000 / 62.5) -1
		
		self.off = self.time_period - self.on						#ncpatel edit this  two line
		self.off_clock = int((self.off - 18)*1000 / 62.5) -1
		
		super(Burst_Mode, self).__init__(parent)
		
		label = QLabel ("<font size=7 color=maroon><b>Burst Mode</b></font>")
		self.Power_Label = QLabel ("<font size=5><b>POWER (Watt)</b></font>")
		self.Power_Spin = QDoubleSpinBox(self)
		self.Power_Spin.setRange(self.power, self.pwr[8]*10)
		self.Power_Spin.setValue(0)
		self.Power_Spin.setStyleSheet ("color : red; font : bold 16px; font-family: Arial Black")
		self.Power_Dial = QDial(self)			#Virtual Power Nobe of Power value
		self.Power_Dial.setRange((self.power*10), (self.pwr[8]*10))
		self.Power_Dial.setNotchesVisible (True)
		
		self.Frequency_Label =QLabel ("<font size=5><b>FREQUENCY (kHz)</b></font>")
		self.Frequency_Spin = QDoubleSpinBox(self)
		self.Frequency_Spin.setRange(1, 25)
		self.Frequency_Spin.setValue (0)
		self.Frequency_Spin.setStyleSheet ("color : blue; font : bold 16px; font-family: Arial Black")
		self.Frequency_Dial = QDial(self)			#virtual Frequency nobe for Frequency value
		self.Frequency_Dial.setRange(1,25)
		self.Frequency_Dial.setNotchesVisible (True)
		self.Burst_Spin = QSpinBox(self)
		self.Burst_Spin.setValue (1)
		self.Burst_Spin.setStyleSheet ("color : green; font : bold 18px; font-family: MS Sans Serif")
		self.BurstSpinLabel = QLabel("<font size=5 color=red><b>Burst No. :</b></font>")
		
		self.Start = QPushButton ("START")
		self.Start.setStyleSheet ("color : Black; background-color: #FF00DC; font : bold 16px; font-family: Lucida Console; height: 20px")
		self.Stop = QPushButton ("STOP")
		self.Stop.setStyleSheet ("color : Black; background-color: #FF1700; font : bold 16px; font-family: Lucida Console; height: 20px")
		
		control_struct = QGridLayout()
		control_struct.addWidget (self.Power_Label, 0, 2, 1, 4)
		control_struct.addWidget (self.Power_Dial, 1, 0, 8, 8)
		control_struct.addWidget (self.Power_Spin, 9, 2, 1, 4)
		control_struct.addWidget (self.Frequency_Label, 0, 11, 1, 8)
		control_struct.addWidget (self.Frequency_Dial, 1, 9, 8, 8)
		control_struct.addWidget (self.Frequency_Spin, 9, 11, 1, 4)
		
		Layout = QGridLayout()
		Layout.addWidget (label, 0, 0, 1, 17)
		Layout.addLayout (control_struct, 1, 0, 10, 17)
		Layout.addWidget (self.BurstSpinLabel, 12, 2, 2, 2)
		Layout.addWidget (self.Burst_Spin, 12, 5, 2, 2)
		Layout.addWidget (self.Start, 12, 10)
		Layout.addWidget (self.Stop, 12,11)
		
		self.setLayout(Layout)
		
		self.connect (self.Power_Dial, SIGNAL("valueChanged(int)"), self.UpdatePulse1_1)
		self.connect (self.Power_Spin, SIGNAL("valueChanged(double)"), self.UpdatePulse1_2)
		self.connect (self.Frequency_Dial, SIGNAL("valueChanged(int)"), self.UpdatePulse2)
		self.connect (self.Frequency_Spin, SIGNAL("valueChanged(double)"), self.UpdatePulse2)
		self.connect (self.Start, SIGNAL("clicked()"), self.LaserStart)
		self.connect (self.Stop, SIGNAL ("clicked()"), self.LaserStop)
		self.connect (self.Burst_Spin, SIGNAL ("valueChanged(int)"), self.UpdatePulse3)
		
	def UpdatePulse1_1 (self, val):
		global record
		self.Power_Spin.setValue(float(val)/10)
		self.power = val/10
		
	def UpdatePulse1_2 (self, val):
		global record
		self.Power_Dial.setValue(float(val*10))
		self.power = val
		
	def UpdatePulse2 (self, val):
		global record
		self.duty, self.pwr = record.getData(int(val))
		self.Frequency_Dial.setValue (val)
		self.Frequency_Spin.setValue (float(val))
		self.freq = val * 1000
		self.time_period = 1000000 / self.freq				#here the time period is in microsecond
		
		self.duty, self.pwr = record.getData(int(self.freq/1000))
		x = np.array(self.duty)
		y = np.array(self.pwr)
		self.min_duty = float(8.0 * 100 / self.time_period)
		self.max_duty = float((self.time_period - 12) * 100 / self.time_period)
		self.min_power = CubicSpline(x, y)(self.min_duty)
		self.max_power = CubicSpline(x, y)(self.max_duty)
		self.Power_Spin.setRange(self.min_power, self.max_power)
		self.Power_Dial.setRange((self.min_power*10), (self.max_power*10))	
	
	def UpdatePulse3 (self, val):
		self.bursts = val		
	
	def	ResetData (self):
		global ser
		self.Power_Dial.setValue (1)
		self.Power_Spin.setValue (1)
		self.Frequency_Dial.setValue (1)
		self.Frequency_Spin.setValue (1)
		self.Burst_Spin.setValue (1)
		self.power = 1
		self.freq = 1000
		self.on = 0
		self.off = 0
		self.on_clock = 0
		self.off_clock = 0
		self.time_period = 1000		
	
	def LaserStart (self):
		global ser
		self.duty, self.pwr = record.getData(int(self.freq/1000))
		x = np.array (self.pwr)
		y = np.array (self.duty)
		self.dutycycle = CubicSpline(x, y)(self.power)
		self.on = self.dutycycle * self.time_period / 100					#self.on is on time of pulse in Micro Seconds
		self.on_clock = int((self.on - 7.67) * 1000 / 62.5) - 1									#on_clock is appropriate number of clock used to generate same time in arduino.
		
		self.off = self.time_period - self.on						#ncpatel edit this  two line
		self.off_clock = int((self.off - 18)*1000 / 62.5) -1
		self.bursts = self.Burst_Spin.value()
		
		s = "R\nM3;O"+str(int(self.on_clock))+";F"+str(int(self.off_clock))+";N"+str(self.bursts)+";\nS"
		print "On:", self.on_clock
		print "Off:",self.off_clock
		print "On Time:", self.on
		print "Off Time:", self.off
		print "Duty cycle:", self.dutycycle
		print "Time Period:", self.time_period
		try:
			if ser.isOpen() == False:
				ser.open()
			ser.write (s.encode("utf-8"))
			#ser.close()
			self.Start.setStyleSheet ("color : Black; background-color: #B8B8B8; font : bold 16px; font-family: Lucida Console; height: 20px")
			self.Start.setEnabled (False)
			self.Stop.setStyleSheet ("color : Black; background-color: #FF1700; font : bold 16px; font-family: Lucida Console; height: 20px")
			self.Stop.setEnabled (True)
		except serial.SerialException as e:	
			#ser.close()
			self.emit(SIGNAL('E'), str(e))
		except BaseException as e:
			#ser.close()
			self.emit(SIGNAL('E'), str(e))		
		
	def LaserStop (self):
		global ser
		try:
			if ser.isOpen() == False:
				ser.open()
			ser.write (('X'.encode("utf-8")))
			#ser.close()
			self.Stop.setEnabled (False)
			self.Stop.setStyleSheet ("color : Black; background-color: #B8B8B8; font : bold 16px; font-family: Lucida Console; height: 20px")
			self.Start.setEnabled(True)
			self.Start.setStyleSheet ("color : Black; background-color: #FF00DC; font : bold 16px; font-family: Lucida Console; height: 20px")
		except serial.SerialException as e:
			#ser.close()
			self.emit(SIGNAL('E'), str(e))
		except BaseException as e:
			#ser.close()
			self.emit(SIGNAL('E'), str(e))	
	
		
class Calibration_Window (QWidget):
	def __init__(self, parent):
		global record
		self.on = 0
		self.off = 0
		self.on_clock = 0
		self.off_clock = 0
		self.time_period = 0
		self.freq = 1
		self.duty =[]
		self.pwr = []
		self.iduty = 0
		self.next_count = 0

		super(Calibration_Window, self).__init__(parent)
		
		self.welcome_label = QLabel ("<font color=maroon size=10><b>Welcome to CO2 LASER Calibration</b></font>")
		self.Instruction_label  = QLabel ("<font color=red size=5>Please press </font><font color=maroon size=5><b>Start Calibration</b></font> <font color=red size=5>button to begin the calibration</font>")
		self.Instruction_Steps = QLabel ()
		self.ExtraLabel = QLabel()
		self.Frequency_Label = QLabel ()
		self.FreqTitle = QLabel("<font size=5><b>Frequency:</b></font>")
		self.DutyCycle = QLabel ("<font size=5><b>Duty Cycle (%): </b></font>")
		self.Frequency = QLabel ("<font size=5><b>Frequency (kHz): </b></font>")
		
		self.FreqSelect = QComboBox ()
		self.FreqSelect.addItems(['1 kHz','2 kHz','3 kHz','4 kHz','5 kHz','6 kHz','7 kHz','8 kHz','9 kHz','10 kHz','11 kHz','12 kHz','13 kHz','14 kHz','15 kHz','16 kHz','17 kHz','18 kHz','19 kHz','20 kHz','21 kHz','22 kHz','23 kHz','24 kHz','25 kHz'])
		self.FreqTitle.setBuddy(self.FreqSelect)
		self.Go = QPushButton ("GO!")
		self.Go.setStyleSheet ("background-color : Orange; color : #0017FF; font-family : Lucida Grande; font : bold 18px")
		self.Start_Cal = QPushButton ("Start the Calibration")
		self.Start_Cal.setStyleSheet ("background-color : #BCFFFB; color : #DB00DF; font : bold 20px; height : 30px")
		self.Next = QPushButton ("Next")
		self.Next.setStyleSheet ("background-color : #F3FF00; color : #0017FF; font-family : Lucida Grande; font : bold 18px")
		self.Abort = QPushButton ("Abort")
		self.Abort.setStyleSheet ("background-color : #FADAFA; color : #000000; font-family : Lucida Grande; font : bold 18px")
		self.Back = QPushButton ("Back")
		self.Back.setStyleSheet ("background-color : #43FF9B; font-family : Lucida Grande; font : bold 18px")
		self.Continue_ = QPushButton ("Continue")
		self.Continue_.setStyleSheet ("background-color : #FDCCFF; font-family : Lucida Grande; font : bold 18px")
		self.Skip = QPushButton ("Skip")
		self.Skip.setStyleSheet ("background-color : #D0D6FF; font-family : Lucida Grande; font : bold 18px")
		self.Finish = QPushButton ("Finish")
		self.Finish.setStyleSheet ("background-color : #B0FFBB; color : Red; font-family : Lucida Grande; font : bold 18px")
		self.SkipAll = QPushButton ("SkipAll")
		self.SkipAll.setStyleSheet ("background-color : #ADB8FF; font-family : Lucida Grande; font : bold 18px")
		
		self.OnTime = QLabel ("<font color = green size=5><b>On: --</b></font>")
		self.OffTime = QLabel ("<font color = red size=5><b>Off: --</b></font>")
		self.Power_Label = QLabel ("<font color = orange size=5><b>Enter the Power(Watt): </b></font>")
		self.Power_Indicator = QLineEdit()
		self.Power_Indicator.setEnabled(False)
		
		control_struct = QGridLayout ()
		control_struct.addWidget (self.DutyCycle, 0, 2, 2, 5)
		control_struct.addWidget (self.Frequency, 0, 7, 2, 5)
		control_struct.addWidget (self.Power_Label, 3, 2, 2, 1)
		control_struct.addWidget (self.Power_Indicator, 3, 3, 2, 3)
		control_struct.addWidget (self.OnTime, 5, 2, 1, 1)
		control_struct.addWidget (self.OffTime, 6, 2, 1, 1)
		
		buttons = QHBoxLayout ()
		buttons.addWidget (self.Go)
		buttons.addStretch (1)
		buttons.addWidget (self.Next)
		buttons.addStretch (1)
		buttons.addWidget (self.Back)
		buttons.addStretch (1)
		buttons.addWidget (self.Abort)
		buttons.addStretch (1)
		buttons.addWidget (self.Continue_)
		buttons.addStretch (1)
		buttons.addWidget (self.Skip)
		buttons.addStretch (1)
		buttons.addWidget (self.SkipAll)
		buttons.addStretch (1)
		buttons.addWidget (self.Finish)
		
		
		Layout = QGridLayout()
		Layout.addWidget (self.welcome_label, 0, 0, 1, 17)
		Layout.addWidget (self.Instruction_label, 1, 0, 1, 17)
		Layout.addWidget (self.Instruction_Steps, 2, 0, 1, 17)
		Layout.addWidget (self.ExtraLabel, 3, 0, 1, 21)
		Layout.addWidget (self.Frequency_Label, 4, 0, 1, 2)
		Layout.addWidget (self.FreqTitle, 4, 5, 1, 1)
		Layout.addWidget (self.FreqSelect, 4, 7, 1, 1)
		Layout.addWidget (self.Start_Cal, 5, 5, 2, 5)
		Layout.addLayout (control_struct, 5, 0, 8, 15)
		Layout.addLayout (buttons, 13, 5, 2, 9)
		
		self.DutyCycle.setVisible (False)
		self.Frequency.setVisible (False)
		self.Power_Label.setVisible (False)
		self.Power_Indicator.setVisible (False)
		self.Go.setVisible (False)
		self.Next.setVisible (False)
		self.Abort.setVisible (False)
		self.Back.setVisible (False)
		self.Finish.setVisible (False)
		self.OnTime.setVisible (False)
		self.OffTime.setVisible (False)
		self.Frequency_Label.setVisible (False)
		self.ExtraLabel.setVisible (False)
		self.Continue_.setVisible (False)
		self.Skip.setVisible (False)
		self.SkipAll.setVisible (False)
		self.FreqSelect.setVisible (False)
		self.FreqTitle.setVisible (False)
		self.setLayout(Layout)
		
		self.connect (self.Go, SIGNAL("clicked()"), self.go)
		self.connect (self.Power_Indicator, SIGNAL("returnPressed()"), self.next)
		self.connect (self.Next, SIGNAL("clicked()"), self.next)
		self.connect (self.Back, SIGNAL("clicked()"), self.back)
		self.connect (self.Start_Cal, SIGNAL("clicked()"), self.decision)
		self.connect (self.FreqSelect, SIGNAL("currentIndexChanged(int)"), self.setFreq)
		self.connect (self.Finish, SIGNAL("clicked()"), self.finish)
		self.connect (self.Skip, SIGNAL("clicked()"), self.skip)
		self.connect (self.Continue_, SIGNAL("clicked()"), self.calibrate)
		self.connect (self.SkipAll, SIGNAL("clicked()"), self.skipall)
		self.connect (self.Abort, SIGNAL("clicked()"), self.decision)
	
	def setFreq (self):
		self.freq = 1 + self.FreqSelect.currentIndex()
		self.iduty = 0
		self.decision()
	
	def skipall (self):
		global record
		if self.freq != [] and self.pwr != []:
			record.setPower (self.freq, self.pwr, self.duty)
		self.conclusion()
	
	def skip (self):
		self.freq += 1
		if self.freq > 25:
			self.conclusion()
		else:
			self.decision()
	
	def decision  (self):
		self.next_count = 0
		self.duty = record.getDuties (self.freq)
		self.FreqTitle.setVisible(True)
		self.FreqSelect.setEnabled (True)
		self.FreqSelect.setVisible (True)
		f = str(self.freq)		
		self.Start_Cal.setVisible (False)
		self.Frequency_Label.setVisible (False)
		self.Frequency.setVisible(False)
		self.OnTime.setVisible (False)
		self.OffTime.setVisible (False)
		self.Power_Label.setVisible (False)
		self.Power_Indicator.setVisible (False)
		self.Go.setVisible (False)
		self.Next.setVisible (False)
		self.Abort.setVisible (False)
		self.Back.setVisible (False)
		self.Skip.setVisible (True)
		self.SkipAll.setVisible (True)
		self.Continue_.setVisible (True)
		self.Instruction_Steps.setText ("<font size=5 color=brown>Press <b>Continue</b> to calibrate CO2 LASER at <b>"+f+"kHz</b> Frequency.</font>")
		self.ExtraLabel.setText ("<font size=5 color=brown>Press <b>Skip</b> to Skip Calibrate CO2 LASER at <b>"+f+"kHz</b> Frequency.</font>")
		self.ExtraLabel.setVisible (True)
		
	def calibrate (self):
		self.duty = record.getDuties (self.freq)
		self.Start_Cal.setVisible (False)
		self.Skip.setVisible (False)
		self.SkipAll.setVisible (False)
		self.Continue_.setVisible (False)
		self.Next.setVisible (True)
		self.Next.setEnabled (False)
		self.Abort.setVisible (True)
		self.Abort.setEnabled (True)
		self.Go.setVisible (True)
		self.Go.setEnabled (True)
		self.FreqSelect.setEnabled (False)
		self.FreqSelect.setVisible (False)
		self.FreqTitle.setVisible (False)
		d = str(self.duty[self.iduty])
		f = str(self.freq)
		self.DutyCycle.setText ("<font size=5><b>Duty Cycle (%): </font><font size=5 color=maroon>"+d+" </b></font>")
		self.Frequency.setText ("<font size=5><b>Frequency (kHz): </font><font size=5 color=maroon>"+f+"</font></b>")
		self.Instruction_label.setText ("<font size=5 color=red>The Calibration is ON</font>")
		self.Instruction_Steps.setText ("<font size=5 color=brown>Press <b>GO</b> to calibrate CO2 LASER for<d>"+d+"%</d> Duty Cycle.</font>")
		self.Frequency_Label.setText ("<font size=5 color=Grey><b>"+f+"kHz</b></font>")
		self.DutyCycle.setVisible (True)
		self.Frequency.setVisible (True)
		self.Frequency_Label.setVisible (True)
		self.ExtraLabel.setVisible (False)
		self.Power_Label.setVisible (True)
		self.Power_Indicator.setVisible (True)
		self.Go.setVisible (True)
		self.Next.setVisible (True)
		self.OnTime.setText ("<font color = green size=5><b>On: --</b></font>")
		self.OffTime.setText ("<font color = red size=5><b>Off: --</b></font>")
		
	def go(self):
		global ser
		
		d = str(self.duty[self.iduty])
		f = str(self.freq)
		self.time_period = 1000 / self.freq
		self.on = (self.time_period * self.duty[self.iduty]) / 100
		self.off = self.time_period - self.on
		self.on_clock = int((self.on - 8) * 1000 / 62.5)
		self.off_clock = int((self.off - 18) * 1000 / 62.5)
		
		try:
			s = "M2;O"+str(self.on_clock)+";F"+str(self.off_clock)+";"
			if ser.isOpen() == False:
				ser.open()
			ser.write (s.encode("utf-8"))
			self.Power_Indicator.setEnabled (True)
			self.OnTime.setText("<font color = green size=5><b>On Time in Micro Seconds: "+str(self.on)+"</b></font>")
			self.OffTime.setText("<font color = red size=5><b>Off Time in Micro Seconds:"+str(self.off)+"</b></font>")
			self.emit(SIGNAL("2"),("On Clock is: "+str(int(self.on_clock))+" and "+"Off Clock is: "+str(int(self.off_clock))))
			self.Instruction_Steps.setText ("<font color=brown size=5>Now, Write the Output Power Of LASER GEM-30 for <b>"+d+"%</b> Duty Cycle.\n Then press next to move to next step</font>")
			time.sleep (2)
			ser.write ('S'.encode("utf-8"))
			#ser.close()
			self.Go.setEnabled (False)
			self.Next.setEnabled (True)
		except serial.SerialException as e:
			#ser.close()
			self.emit(SIGNAL('E'), str(e))
		except BaseException as e:
			#ser.close()
			self.emit(SIGNAL('E'), str(e))
	
	def next (self):
		global ser
		global alert
		
		if (unicode(self.Power_Indicator.text()) == None):
			alert.play()
			QMessageBox.warning(self, "Value Error","<b>Power is mandatory!<b>")
		else:
			try:
				val = float (unicode(self.Power_Indicator.text()))
				self.next_count +=1
				if self.next_count == 1:
					x = 0
				else:
					x = self.pwr[-1]
				if x < val:
					self.Power_Indicator.setEnabled (False)
					self.Back.setVisible (True)
					self.Back.setEnabled (True)
					self.pwr.append(val)
					time.sleep (2)
					try:
						if ser.isOpen() == False:
							ser.open()
						ser.write (('X'.encode("utf-8")))
						time.sleep(2)
						ser.write (('R').encode("utf-8"))
						self.iduty +=1
						#ser.close()
						if self.iduty > 7 :
							if self.freq >= 25:
								self.conclusion()
							else:
								record.setPower (self.freq, self.pwr, self.duty)				#here self.pwr and self.duty are arrays
								self.freq += 1
								self.iduty = 0
								self.decision ()
						else:	
							self.calibrate()
					except serial.SerialException as e:
						#ser.close()
						self.emit(SIGNAL('E'), str(e))
					except IOError as e:
						#self.close()
						self.emit(SIGNAL('E'), str(e))
				else:
					alert.play()
					QMessageBox.warning(self, "Value Error","<b>The power should be in increasing sequence!<b>")
					
			except serial.SerialException as e:
				self.close()
				self.emit(SIGNAL('E'), str(e))
			except ValueError:
				self.close()
				alert.play()
				QMessageBox.warning(self, "Value Error", "<b>Power is Invalid!</b>")
		
	def back(self):
		self.iduty -= 1
		self.calibrate()
		self.pwr.pop()
		if self.iduty == 0:
			self.Back.setVisible (False)	
	
	def conclusion(self):
		self.welcome_label.setText("<font color=maroon size=10><b>Welcome to CO2 LASER Calibration</b></font>")
		self.Instruction_label.setText("<font  color=Blue size=5><b>You are all set! Now the software is ready to operate</b></font><font color=red size=5><b>GEM-30 CO2 LASER</b></font>")
		self.Instruction_Steps.setText("<font color=red size=5>Please press </font><font color=maroon size=5><b>Finish</b></font><font color=red size=5>button to go to operation window.</font>")
		self.Start_Cal.setVisible (False)
		self.DutyCycle.setVisible (False)
		self.Frequency.setVisible (False)
		self.Power_Label.setVisible (False)
		self.Power_Indicator.setVisible (False)
		self.Go.setVisible (False)
		self.Next.setVisible (False)
		self.Abort.setVisible (False)
		self.Back.setVisible (False)
		self.Finish.setVisible (True)
		self.Skip.setVisible (False)
		self.SkipAll.setVisible (False)
		self.Continue_.setVisible (False)
	
	def finish(self):		
		self.on = 0
		self.off = 0
		self.on_clock = 0
		self.off_clock = 0
		self.time_period = 0
		self.freq = 1
		self.duty = []
		self.iduty = 0
		
		self.welcome_label.setText("<font color=maroon size=10><b>Welcome to CO2 LASER Calibration</b></font>")
		self.Instruction_label.setText("<font color=red size=5>Please press </font><font color=maroon size=5><b>Start Calibration</b></font> <font color=red size=5>button to begin the calibration</font>")
		self.Instruction_Steps.setText("")
		self.Start_Cal.setVisible (True)
		self.DutyCycle.setVisible (False)
		self.Frequency.setVisible (False)
		self.Power_Label.setVisible (False)
		self.Power_Indicator.setVisible (False)
		self.Go.setVisible (False)
		self.Next.setVisible (False)
		self.Abort.setVisible (False)
		self.Back.setVisible (False)
		self.FreqSelect.setVisible (False)
		self.FreqSelect.setCurrentIndex = 0
		self.FreqTitle.setVisible (False)
		self.Finish.setVisible (False)
		self.SkipAll.setVisible (False)
		self.emit(SIGNAL("co"))
		
	def Reset_Calibration (self):	
		self.on = 0
		self.off = 0
		self.on_clock = 0
		self.off_clock = 0
		self.time_period = 0
		self.freq = 1
		self.duty = []
		self.iduty = 0
		
		self.welcome_label.setText("<font color=maroon size=10><b>Welcome to CO2 LASER Calibration</b></font>")
		self.Instruction_label.setText("<font color=red size=5>Please press </font><font color=maroon size=5><b>Start Calibration</b></font> <font color=red size=5>button to begin the calibration</font>")
		self.Instruction_Steps.setText("")
		self.Start_Cal.setVisible (True)
		self.DutyCycle.setVisible (False)
		self.Frequency.setVisible (False)
		self.Frequency_Label.setVisible (False)
		self.Power_Label.setVisible (False)
		self.Power_Indicator.setVisible (False)
		self.Go.setVisible (False)
		self.Next.setVisible (False)
		self.Back.setVisible (False)
		self.Finish.setVisible (False)
		self.FreqSelect.setVisible (False)
		self.FreqSelect.setCurrentIndex = 0
		self.FreqTitle.setVisible (False)
		
		
class Notification(QThread): 
	def __init__(self):
		super(Notification, self).__init__()
		self.OldPort = None
		self.Message_Dictionary = {'101':"Error in Temperature", '102':"Error in voltage", '103':"Error in water supply", '104':"Error in Mode, Please send data again",
		'105':"Error in On time, Please send data again!", '106':"Error in Off time, Please send data again!", '107':"Error in number of Burst, Please send data again!",
		'201':"Data loaded", '202':"Pulse Mode selected!", '203':"Pulse Mode is executed!", '204':"End of the execution of Pulse Mode",
		'205':"Continuous Mode selected!", '206':"Continuous Mode is started!", '207':"Continuous Mode stopped!",
		'208':"Burst Mode selected!", '209':"Burst Mode is started!", '210':"Burst Mode Ended!", '211':"CW Continue On mode is selected!",
		'212':"Laser is On in CW mode", '213':"Data Reseted successfully!", '214':"Laser is Off",
		'301':"Envelop Modulation is not operable, Please select another mode!"}

	
	def __del__(self):
		self.wait()
	
	def run(self):
		global ser
		old = ""
		new = old
		
		while True:
			try:
				if ser.isOpen() == False:
					ser.open()
				try:
					new = ser.readline().decode("utf-8")
					new = new[0:3]
				except IOError as e:
					self.emit(SIGNAL('E'), e)
					break	
			except serial.SerialException as e:
				self.emit(SIGNAL('E'), str(e))
				break
			except BaseException as e:
				self.emit(SIGNAL('E'), str(e))
				break
			if new != old:
				old = new
				if new=='101' or new=='102' or new=='103':
					self.emit(SIGNAL('LE'), 'LE')
					self.emit(SIGNAL('0'), self.Message_Dictionary[new])
				elif new=='104' or new=='105' or new=='106' or new=='107':
					self.emit(SIGNAL('CE'),'CE')
					self.emit(SIGNAL('0'), self.Message_Dictionary[new])
				elif new=='201':
					self.emit(SIGNAL('DL'), 'DL')
					self.emit(SIGNAL('0'), self.Message_Dictionary[new])
				elif new =='203' or new=='206' or new=='209':
					self.emit(SIGNAL('ON'), 'ON')
					self.emit(SIGNAL('0'), self.Message_Dictionary[new])
				elif new=='204' or new=='207' or new=='210':
					self.emit(SIGNAL('OFF'), 'OFF')
					self.emit(SIGNAL('0'), self.Message_Dictionary[new])
				elif new=='213':
					self.emit(SIGNAL('RS'), 'RS')
					self.emit(SIGNAL('0'), self.Message_Dictionary[new])
			else:
					self.emit(SIGNAL('0'), self.Message_Dictionary[new])
			
	
class Main_Widget (QWidget):
	
	def __init__(self, parent):
		self.Current_Port = None
		super(Main_Widget, self).__init__(parent)
		self.debugging_count = 0
		self.intro_Label = QLabel ("< font color=red size=10 ><b>CO2 Control Panel</b></font>")
		
		self.Pulse = Pulse_Mode (None)
		self.Continuous = Continuous_Mode (None)
		self.Burst = Burst_Mode (None)
		
		self.Operation = QPushButton ("Operation_Desk")
		self.Operation.setStyleSheet ("background-color: orange; color : Blue; font : bold 18px; height : 30px")
		self.Calibration = QPushButton ("Calibration_Desk")
		self.Calibration.setStyleSheet ("background-color: #BCCAC9; color :Red; font : bold 18px; height : 30px")
		self.Debugger = QPushButton ("Debugger")
		self.Debugger.setStyleSheet ("background-color: #BCCAC9; color :Maroon; font : bold 18px; height : 30px")
		self.OperationLabel = QLabel ("<font color=Brown size=5><b>CO2 LASER Operations</b></font>")
		
		self.Co2_Calibration = Calibration_Window (None)
		
		self.Laser_On_Led = QLed (self, onColour=QLed.Green, shape=QLed.Circle)					#LED
		self.Laser_Off_Led = QLed (self, onColour=QLed.Red, shape=QLed.Circle)				#LED		
		
		font1 = QFont()
		font1.setFamily("MS Sans Serif")
		font1.setPointSize (14)
		font1.setWeight (75)
		
		
		self.PulseRadio = QRadioButton ("&Pulse Mode")
		self.PulseRadio.setStyleSheet ("color : #E23535; font : bold 20px; font-family : Courier Header; height : 15px")
		self.ContinuousRadio = QRadioButton ("&Continuous Mode")
		self.ContinuousRadio.setStyleSheet ("color : #62C609; font : bold 20px; font-family : Courier Header; height : 15px")
		self.BurstRadio = QRadioButton ("&Burst Mode")	
		self.BurstRadio.setStyleSheet ("color : #0942C6; font : bold 20px; font-family : Courier Header; height : 15px")
		
		
		self.whiteboard = QTextBrowser(None)
		self.whiteboard.append ("<font color=Blue><b>Communication with Arduino board:</b></font>")
		
		self.check_port = Serial_Check()			#Thread of port checking...
		self.check_port.start()
		self.Notes = Notification()  			#Thread of communication.
		
		self.SerialPort = QComboBox ()
		self.SeralPortLabel = QLabel ("<font color=#00BCAB size=5><b>Ports:</font></b>")
		self.SeralPortLabel.setBuddy (self.SerialPort)
		
		global ser
		ser =serial.Serial()
		
		layout = QHBoxLayout()
		layout.addWidget (self.PulseRadio)
		layout.addStretch (2)
		layout.addWidget (self.ContinuousRadio)
		layout.addStretch (2)
		layout.addWidget (self.BurstRadio)
		
		LOn_label = QLabel ("<font color=Green size=5><b>LASER On</b></font>")
		LOff_label = QLabel("<font color=red size=5><b>LASER OFF</b></font>")
		
		
		self.Laser_Status_Label = QLabel("<font color=grey size=5><b>Laser is ready to be operated.</b></font>")
		
		operationlayout = QGridLayout()
		operationlayout.addWidget (self.OperationLabel, 0, 0)
		operationlayout.addLayout (layout, 1, 0 , 2, 10)
		operationlayout.addWidget (self.Pulse, 3, 0, 15, 18)
		operationlayout.addWidget (self.Continuous, 3, 0, 15, 18)
		operationlayout.addWidget (self.Burst, 3, 0, 15, 18)
		
		self.Grid = QGridLayout()
		self.Grid.addWidget (self.intro_Label, 0, 0, 1, 10)
		self.Grid.addWidget (self.SeralPortLabel, 1, 2, 2, 2)
		self.Grid.addWidget (self.SerialPort, 1, 4, 2, 2)
		self.Grid.addWidget (self.Laser_On_Led, 0, 11)
		self.Grid.addWidget (LOn_label, 0, 12)
		self.Grid.addWidget (self.Laser_Off_Led, 1, 11)
		self.Grid.addWidget (LOff_label, 1, 12)
		self.Grid.addLayout (operationlayout, 3, 1, 16, 17)
		self.Grid.addWidget (self.Co2_Calibration, 3, 0, 16, 17)		
	
		self.whiteboard.setEnabled (False)
		self.whiteboard.setVisible(False)
		
		self.Pulse.setVisible (True)
		self.Continuous.setVisible (False)
		self.Burst.setVisible (False)
		
		self.Co2_Calibration.setVisible (False)
		
		self.FinalLayout = QGridLayout()
		self.FinalLayout.addLayout (self.Grid, 0, 0, 20, 17)
		self.FinalLayout.addWidget (self.Operation, 21, 0, 1, 2)
		self.FinalLayout.addWidget (self.Calibration, 21, 2, 1, 2)
		self.FinalLayout.addWidget (self.Debugger, 21, 4, 1, 2)
		self.FinalLayout.addWidget (self.Laser_Status_Label, 21, 8, 1, 12)
		self.setLayout(self.FinalLayout)
		
		self.connect (self.Operation, SIGNAL("clicked()"), self.Operation_On)
		self.connect (self.Calibration, SIGNAL("clicked()"), self.Calibration_On)
		self.connect (self.Debugger, SIGNAL("clicked()"), self.Debugging)
		self.connect (self.PulseRadio, SIGNAL("toggled(bool)"), self.tab1)
		self.connect (self.ContinuousRadio, SIGNAL("toggled(bool)"), self.tab2)
		self.connect (self.BurstRadio, SIGNAL("toggled(bool)"), self.tab3)
		self.connect (self.Notes, SIGNAL("0"), self.ArduinoSpeaks)
		self.connect (self.check_port, SIGNAL("5"), self.Revise_Port)
		self.connect (self.Notes, SIGNAL ('E'), self.Error_Port)
		self.connect (self.Pulse, SIGNAL ('E'), self.Error_Port)
		self.connect (self.Continuous, SIGNAL ('E'), self.Error_Port)
		self.connect (self.Burst, SIGNAL ('E'), self.Error_Port)
		self.connect (self.Co2_Calibration, SIGNAL ('E'), self.Error_Port)
		self.connect (self.check_port, SIGNAL ('E'), self.Error_Port)
		self.connect (self.SerialPort, SIGNAL ("currentIndexChanged(int)"), self.setPort)
		#self.connect (self, SIGNAL("quit()"), self.closeall)
		self.connect (self.Pulse, SIGNAL ("1"), self.message)
		self.connect (self.Continuous, SIGNAL ("2"), self.message)
		self.connect (self.Burst, SIGNAL ("2"), self.message)
		self.connect (self.Notes, SIGNAL ('LE'), self.LaserStatus)
		self.connect (self.Notes, SIGNAL ('CE'), self.LaserStatus)
		self.connect (self.Notes, SIGNAL ('DL'), self.LaserStatus)
		self.connect (self.Notes, SIGNAL ('RS'), self.LaserStatus)
		self.connect (self.Notes, SIGNAL ('ON'), self.LaserState)
		self.connect (self.Notes, SIGNAL ('OFF'), self.LaserState)
		self.connect (self.Notes, SIGNAL ("END"), self.EndSerialCheck)
		self.connect (self.Co2_Calibration, SIGNAL("co"), self.Operation_On)
	
	def EndSerialCheck(self):
		self.check_port.terminate()
		self.check_port.wait()
	
	def Debugging (self):
		self.debugging_count += 1
		if (self.debugging_count % 2) == 0:
			self.Operation.setStyleSheet ("background-color : orange; color : Blue; font : bold 18px; height : 30px")
			self.Calibration.setStyleSheet ("background-color : #BCCAC9; color : Red; font : bold 18px; height : 30px")
			self.Debugger.setStyleSheet ("background-color : #BCCAC9; color : Maroon; font : bold 18px; height : 30px")
			self.whiteboard.setVisible (False)
			self.whiteboard.setEnabled (False)
		else:
			self.Calibration.setStyleSheet ("background-color : #BCCAC9; color : Red; font : bold 18px; height : 30px")
			self.Operation.setStyleSheet ("background-color : #BCCAC9; color : Blue; font : bold 18px; height : 30px")
			self.Debugger.setStyleSheet ("background-color : Orange; color : Maroon; font : bold 18px; height : 30px")
			self.Grid.addWidget (self.whiteboard, 0, 21, 16, 10)		
			self.whiteboard.setEnabled (True)
			self.whiteboard.setVisible (True)
		
	def Operation_On (self):
		self.Operation.setStyleSheet ("background-color : orange; color : Blue; font : bold 18px; height : 30px")
		self.Calibration.setStyleSheet ("background-color : #BCCAC9; color : Red; font : bold 18px; height : 30px")
		self.Debugger.setStyleSheet ("background-color : #BCCAC9; color : Maroon; font : bold 18px; height : 30px")
		self.whiteboard.setVisible (False)
		self.whiteboard.setEnabled (False)
		self.Grid.removeWidget(self.whiteboard) 
		self.Co2_Calibration.setVisible (False)
		self.OperationLabel.setVisible (True)
		self.PulseRadio.setVisible (True)
		self.PulseRadio.setChecked (False)
		self.ContinuousRadio.setVisible (True)
		self.ContinuousRadio.setChecked (False)
		self.BurstRadio.setVisible (True)
		self.BurstRadio.setChecked (False)
		self.Co2_Calibration.Reset_Calibration ()
	
	def Calibration_On (self):
		self.Operation.setStyleSheet ("background-color : #BCCAC9; color : Blue; font : bold 18px; height : 30px")
		self.Calibration.setStyleSheet ("background-color : orange; color : maroon; font : bold 18px; height : 30px")
		self.Debugger.setStyleSheet ("background-color : #BCCAC9; color : Maroon; font : bold 18px; height : 30px")
		self.whiteboard.setVisible (False)
		self.whiteboard.setEnabled (False)
		self.Grid.removeWidget(self.whiteboard) 
		self.Co2_Calibration.setVisible (True)
		self.OperationLabel.setVisible (False)
		self.PulseRadio.setVisible (False)
		self.PulseRadio.setChecked (False)
		self.ContinuousRadio.setVisible (False)
		self.ContinuousRadio.setChecked (False)
		self.BurstRadio.setVisible (False)
		self.BurstRadio.setChecked (False)
		self.Pulse.setVisible (False)
		self.Continuous.setVisible (False)
		self.Burst.setVisible (False)
	
	def LaserStatus (self, val):
		if val == 'LE':
			self.Laser_Off_Led.Value = True
			self.Laser_On_Led.Value = False
			self.Laser_Status_Label.setText("<font color=red size=5><b>Laser Error!</b></font>")
		elif val == 'CE':
			self.Laser_Status_Label.setText("<font color=orange size=5><b>Error in communication!</b></font>")
		elif val == 'DL':
			self.Laser_Status_Label.setText("<font color=brown size=5><b>Data is Loaded successfully!</b></font>")
		elif val == 'RS':
			self.Laser_Status_Label.setText("<font color=blue size=5><b>Data is Reseted!</b></font>")
			
				
		
	def LaserState (self, val):
		if val == 'ON':
			self.PulseRadio.setEnabled (False)
			self.ContinuousRadio.setEnabled (False)
			self.BurstRadio.setEnabled (False)
			self.Laser_On_Led.value = True
			self.Laser_Status_Label.setText("<font color=brown size=5><b>Laser is Started!</b></font>")
		else:
			self.PulseRadio.setEnabled (True)
			self.ContinuousRadio.setEnabled (True)
			self.BurstRadio.setEnabled (True)
			self.Continuous.Start.setEnabled (True)
			self.Burst.Start.setEnabled (True)
			self.Continuous.Stop.setEnabled (False)
			self.Burst.Stop.setEnabled (False)
			self.Continuous.Stop.setStyleSheet ("color : Black; background-color: #B8B8B8; font : bold 16px; font-family: Lucida Console; height: 20px")
			self.Continuous.Start.setStyleSheet ("color : Black; background-color: #FF00DC; font : bold 16px; font-family: Lucida Console; height: 20px")
			self.Burst.Stop.setStyleSheet ("color : Black; background-color: #B8B8B8; font : bold 16px; font-family: Lucida Console; height: 20px")
			self.Burst.Start.setStyleSheet ("color : Black; background-color: #FF00DC; font : bold 16px; font-family: Lucida Console; height: 20px")
			
			self.Laser_On_Led.value = False
			self.Laser_Status_Label.setText("<font color=brown size=5><b>Laser is Stopped!</b></font>")
		
	def message(self, string):
		self.whiteboard.append ("<font color=green>"+string+"</font>")
	
	def closeall(self):
		global ser
		try:
			if ser.isOpen() == False:
				ser.open()
			ser.write("X\nR".encode("utf-8"))
			time.sleep(1)
			ser.close()
		except:
			ser.close()
			pass
		self.Notes.quit()
		self.check_port.quit()
		ser.close()
			
	def Error_Port (self, e):
		global alert
		alert.play()
		QMessageBox.warning (self, "Comport!","Please check the connection with Arduino or select the appropriate Port!\n"+ str(e))
		self.whiteboard.append("<font color=red size=3><b>"+e+"<b></font>")
		self.Notes.terminate()
		self.Notes.wait()
		self.check_port.start()
		
	
	def Revise_Port(self, portlist):
		self.SerialPort.clear()
		self.SerialPort.addItems(portlist)
		
		#self.ListOfPorts = portlist
	
	def ArduinoSpeaks (self, s):
		self.whiteboard.append("<font color = maroon>Arduino says: </font>" + s)
		
	def setPort (self):
		global ser
		com_port = unicode (self.SerialPort.currentText())
		ser = serial.Serial (com_port, 9600)
		self.Notes.start()

	def tab1(self):
		#self.My_Label.setVisible (False)
		self.Continuous.setVisible(False)
		self.Burst.setVisible(False)
		self.Pulse.setVisible (True)
		
	def tab2(self):
		#self.My_Label.setVisible (False)
		self.Pulse.setVisible (False)
		self.Burst.setVisible (False)
		self.Continuous.setVisible (True)
		
	def tab3(self):
		#self.My_Label.setVisible (False)
		self.Pulse.setVisible (False)
		self.Continuous.setVisible (False)
		self.Burst.setVisible (True)


		
app = QApplication(argv)
Obj = My_Panel()
Obj.show()
alert.play()
#QMessageBox.warning(None , "Warning","Please select the port First!")
app.exec_()	