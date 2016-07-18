#######################################################################################################################
# This module provides basic functionality for the MCP-8 repeater controllers from www.ICS-CTRL.com
#
# This code can be freely modified to fit your specific requirements.  This code is intended only as a starting point, 
# and ICS-CTRL highly encourages all users to contribute to the open source project which can be found on github 
# (this code is also available on github as well)
#
# For software support issues, please do no contact ICS-CTRL directly, instead please join the yahoo users group for
# for ICS-CTRL at the link below.  The user group is full of # technical savvy people who are well versed in the ICS 
# product lines and are monitored by the design team as well.
# 
# https://groups.yahoo.com/neo/groups/ICS-Controllers/info
#
# For suspected hardware issues, please follow the factory # test procedure as outlined on the product support page.
#
#######################################################################################################################

################### Revision History ##################################################################################
# Author: Daniel Loranger, KG7PAR, ICS-CTRL
# Initial Date: 03-July-2016
# Current Revision: 01
#
# Revision History
# Revision 01: Initial release
#
#######################################################################################################################

################### IMPORT CALLS ######################################################################################
import RPi.GPIO as GPIO		# we need access to GPIO
#import datetime				# used to manage the system time
import subprocess
import os					# so we can handle the restart requests
import pygame.mixer			# for audio playback
import time					# used for ID timer, etc
from multiprocessing import Queue, Process
from datetime import datetime, timedelta

#################### Communication Queues #############################################################################
idAnnouncerQueue = Queue() # Queue for notifying the ID announcer to announce
TransmitterEnableQueue = Queue() # Queue for the ID_Watchdog to configure the outputs

#################### General Functions ################################################################################
#SETUP ONBOARD GPIO
def OB_GPIO_config (Pin,Dir,pull_dir):
	try:
		global LogFilePath
		if Dir == GPIO.IN:
			GPIO.setup(Pin,Dir,pull_up_down=pull_dir)
		else:
			GPIO.setup(Pin,Dir)
		writeText = 'Configure pin: '+str(Pin)+' DIRN: '+str(Dir)+' PUD: '+str(pull_dir)
		WriteToLog(writeText)
		return 0
	except:
		WriteToLog("Failed to configure pin "+str(Pin))
		return 1

# basic password checker function, used to validate dtmf 
def PasswordCheck(SuspectPassword="y",ApprovedPassword="x"):
   if SuspectPassword == ApprovedPassword:
      WriteToLog("Password Verified")
      return 0
   else:
      WriteToLog("Password Rejected")
      return 1

def ID_Watchdog(conn):
	activity = "0"
	Delay = 1  # minutes
	SendID = False
	while True:	# Run forever
		SendID = False  # clear the SendID variable every Delay minutes
		TimeFinish = datetime.now() + timedelta(minutes=Delay)
		TimeNow = datetime.now()
		#print (TimeFinish)
		while TimeFinish >= TimeNow:
			try:
				# This is expected to timeout after 1 second, exception will
				# serve as an extra delay to keep the processor burden low
				activity= conn.get(block=True, timeout=1) # Did someone keyup?
														
			except:
				time.sleep (1)
			if activity == "1" or SendID == True: # want the value to stay set
				SendID = True
			if activity == "Q": # terminate process
				sys.exit()
			TimeNow = datetime.now()
            #print (TimeNow)
		if SendID == True:
			WriteToLog("ID announced")
			TransmitterEnableQueue.put(1) # turn on the outputs
			pygame.mixer.music.load("/home/pi/MPC8/MessagesEnglish/StationID/StationCallSignVoice.mp3")
			pygame.mixer.music.play()
			while pygame.mixer.music.get_busy() == True:
				continue
			TransmitterEnableQueue.put(0)# turn off the outputs	
		else:
			WriteToLog("ID NOT announced")
    #conn.close()	# close the queue, not really needed as runs forever
	  
def GetTimeString():
   # get preformatted time stamp
   return (datetime.strftime(
      datetime.now(),'%Y%m%d_%H:%M:%S'))
def WriteToLog(LogEntry):
   # generic log file entry
   with open(LogFilePath, "a+") as log:
      Text = GetTimeString()+" - " +LogEntry+"\n"
      log.write(Text)
########################### Configure GPIO MODE #######################################################################
GPIO.setmode (GPIO.BOARD)	# use header pin numbers
GPIO.setwarnings(False)     # turn off during debug, should be left on during normal usage
#################### Configure On-Board GPIO ##########################################################################


# CONFIGURE On-Board GPIO PINS
DebugPin	= 7
DebugPin_DIRN = GPIO.OUT
DebugPin_PUD = GPIO.PUD_UP

# PIN NUMBERS
DTMF_INT   	= 31
COS_INT    	= 33
CTCSS_INT  	= 35
RESETn     	= 37
ADC_EOCn   	= 15 
RTC_RDY    	= 11
AUDIO_SDTI  = 40
AUDIO_SDTO  = 38
AUDIO_LRCK  = 36
AUDIO_MCLK  = 34
AUDIO_SCLK  = 18
GPI_INT    	= 16
SPI_ADC_CS 	= 24

def PI_PIN_SETUP():

	# PIN DIRECTIONS
	DTMF_INT_DIRN   = GPIO.IN
	COS_INT_DIRN    = GPIO.IN
	CTCSS_INT_DIRN  = GPIO.IN
	RESETn_DIRN     = GPIO.IN
	ADC_EOCn_DIRN   = GPIO.IN
	RTC_RDY_DIRN    = GPIO.IN
	AUDIO_SDTI_DIRN = GPIO.OUT
	AUDIO_SDTO_DIRN = GPIO.IN
	AUDIO_LRCK_DIRN = GPIO.OUT
	AUDIO_MCLK_DIRN = GPIO.OUT
	AUDIO_SCLK_DIRN = GPIO.OUT
	GPI_INT_DIRN    = GPIO.IN
	SPI_ADC_CS_DIRN = GPIO.OUT

	# PIN PULL UP/DOWN DIRECTION IF PIN IS DEFINED AS INPUT
	DTMF_INT_PUD   	= GPIO.PUD_UP
	COS_INT_PUD    	= GPIO.PUD_UP
	CTCSS_INT_PUD  	= GPIO.PUD_UP
	RESETn_PUD		= GPIO.PUD_UP
	ADC_EOCn_PUD	= GPIO.PUD_UP
	RTC_RDY_PUD		= GPIO.PUD_UP
	AUDIO_SDTI_PUD	= GPIO.PUD_UP
	AUDIO_SDTO_PUD	= GPIO.PUD_UP
	AUDIO_LRCK_PUD	= GPIO.PUD_UP
	AUDIO_MCLK_PUD	= GPIO.PUD_UP
	AUDIO_SCLK_PUD	= GPIO.PUD_UP
	GPI_INT_PUD		= GPIO.PUD_UP
	SPI_ADC_CS_PUD	= GPIO.PUD_UP

	OB_GPIO_config(DTMF_INT  ,DTMF_INT_DIRN   ,DTMF_INT_PUD)
	OB_GPIO_config(COS_INT   ,COS_INT_DIRN    ,COS_INT_PUD)
	OB_GPIO_config(CTCSS_INT ,CTCSS_INT_DIRN  ,CTCSS_INT_PUD)
	OB_GPIO_config(RESETn    ,RESETn_DIRN     ,RESETn_PUD)
	OB_GPIO_config(ADC_EOCn  ,ADC_EOCn_DIRN   ,ADC_EOCn_PUD)
	OB_GPIO_config(RTC_RDY   ,RTC_RDY_DIRN    ,RTC_RDY_PUD)
	OB_GPIO_config(AUDIO_SDTI,AUDIO_SDTI_DIRN ,AUDIO_SDTI_PUD)
	OB_GPIO_config(AUDIO_SDTO,AUDIO_SDTO_DIRN ,AUDIO_SDTO_PUD)
	OB_GPIO_config(AUDIO_LRCK,AUDIO_LRCK_DIRN ,AUDIO_LRCK_PUD)
	OB_GPIO_config(AUDIO_MCLK,AUDIO_MCLK_DIRN ,AUDIO_MCLK_PUD)
	OB_GPIO_config(AUDIO_SCLK,AUDIO_SCLK_DIRN ,AUDIO_SCLK_PUD)
	OB_GPIO_config(GPI_INT   ,GPI_INT_DIRN    ,GPI_INT_PUD)
	OB_GPIO_config(SPI_ADC_CS,SPI_ADC_CS_DIRN ,SPI_ADC_CS_PUD)
	
	OB_GPIO_config(DebugPin,DebugPin_DIRN ,DebugPin_PUD)
	GPIO.output(DebugPin, 0)
	
	# Enable the Interrupts with appropriate edge detections
	GPIO.add_event_detect(RESETn, GPIO.FALLING, callback=RESET_INT_CALLBACK)
	GPIO.add_event_detect(COS_INT, GPIO.RISING, callback=COS_INT_CALLBACK_START)
#################### Configure Expander GPIO ##########################################################################

#################### Threaded Callbacks (Interrupts)###################################################################
# These functions will spawn into a new thread to monitor the respective signals
def TransmitterEnable ():
	# we should only get messages here to turn on/off the transmitter
	# transmitter will stay on as long as 1 channel is active
	
	# COS_INT_CALLBACK_XXX and the ID process are the only sources for this data
	cosActive=[0,0,0,0,0,0,0,0] #2-8 & dummy channel 
	while True:
		Transmit = 0 # clear the sticky bits
		status = (8,0) # clear the queue read values
		try:
			Status = TransmitterEnableQueue.get(block=False, timeout=0.05)#(channel,enabled)
		except:
			sleep(0) # no need to wait any longer
		
		# update the array with the new value read in (if any)
		cosActive[Status[0]] = cosActive[1]
		
		#check for a message from the ID transmitting queue
		try:
			idStatus = idTransmitterEnableQueue.get(block=False, timeout=0.05)#(channel,enabled)
		except:
			sleep(0) # no need to wait any longer
		
		# check if any of the bits are active, if so turn/keep the transmitter on
		for x in range (0,6): # remember not to use the last index, dummy channel
			if cosActive[x] == 1 or Transmit == 1 or idStatus == 1:
				Transmit=True
		
		#update the GPIO expander to set the output enables to the daughter cards
		if Transmit == True:
			channelOutputEnable(True)
		else:
			channelOutputEnable(False)
		return								
def channelOutputEnable(transmit):
	if transmit == True:
		#write the active channels list to the GPIO expander
		sleep(0)
	else:
		#clear the GPIO expander output to disable the transmitters
		sleep(0)
	return 0				
def COS_INT_CALLBACK_START (): 
	Channel = "DEFAULT"
	# We need to read back the state of the IO expander
	# to see who actually triggered the interrupt so we can 
	# work on the appropriate signal source
   
   
	# Check to make sure the source is actually an active channel
	# we don't want inactive channels accidently triggering the system
   
	
	#if active channel, notify the ID Announcer process so it can send the call
	WriteToLog("COS Signal detected on channel"+Channel)
	idAnnouncerQueue.put("1")
	
	# Turn on the Transmitter(s) if not already active
	#WriteToLog(Channel+"")
	
	# reconfigure the interrupt to watch for the end of the event
	GPIO.remove_event_detect(COS_INT) 
	GPIO.add_event_detect(COS_INT, GPIO.FALLING, callback=COS_INT_CALLBACK_END)
	
def COS_INT_CALLBACK_END (): 
	Channel = "DEFAULT"
	# We need to read back the state of the IO expander
	# to see who actually triggered the interrupt so we can 
	# work on the appropriate signal source
   
   
	# Check to make sure the source is actually an active channel
	# we don't want inactive channels accidently triggering the system
   
	
	#if active channel, notify the ID Announcer process so it can send the call
	WriteToLog("COS Signal removed on channel"+Channel)
	idAnnouncerQueue.put("0")
	
	# Turn on the Transmitter(s) if not already active
	#WriteToLog(Channel+"stopped receiving")
	
	# reconfigure the interrupt to watch for the end of the event
	GPIO.remove_event_detect(COS_INT) 
	GPIO.add_event_detect(COS_INT, GPIO.RISING, callback=COS_INT_CALLBACK_START)
	
def DTMF_INT_CALLBACK ():
	PassCheckUser = 0
	PassCheckAdmin = 0;
	WriteToLog("DTMF interrupt detected")

   # We need to read back the state of the IO expander
   # to see who actually triggered the interrupt so we can 
   # work on the appropriate DTMF signal source


   # Now that we know who triggered the interrupt, we need to
   # enable the outputs for that channel and read in the data


   # Decode the data from the DTMF and change config/respond 
   # as appropriate per the command requested

   # validate password (if required)
   ##### READ requests (no password)#####

   
	##### SAFE CONFIG  (user password) #####
	# Request User Password
	DTMFPassword = "123"
	SystemPassword = "456" #user password
   
	##### UNSAFE CONFIG (admin password) #####
	# Request admin Password
	DTMFPassword = "123"
	SystemPassword = "456"	#adminpassword
   
	# validate password
	Passcheck = PasswordCheck(SuspectPassword=DTMFPassword,ApprovedPassword=SystemPassword)
# DTMF_INT_CALLBACK

def RESET():
	WriteToLog("Reset requested, system preparing to reboot")
	print ("Resetting Now!!!")
	# Notify audibly the system is being reset
	pygame.mixer.music.load("/home/pi/MPC8/MessagesEnglish/StationID/StationCallSignVoice.mp3")
	pygame.mixer.music.play()
	pygame.mixer.music.load("/home/pi/MPC8/MessagesEnglish/Status/SystemReset.mp3")
	pygame.mixer.music.play()
	while pygame.mixer.music.get_busy() == True:# wait for announcement to finish
		continue	
	# issue the actual restart event
	os.system('sudo shutdown -r now')
	
def RESET_INT_CALLBACK():
	RESET()	

#################### MAIN Functionality ####################


# Create the log file
LogFileName = GetTimeString() +"_logFile.log"
global LogFilePath 
LogFilePath = "/home/pi/MPC8/SystemLogs/"+LogFileName
print ("Log Path: "+LogFilePath)
with open(LogFilePath, "w") as log:
   log.close()
WriteToLog("Application Launched")
# Configure all the GPIO pins for use
WriteToLog("****** Configuring GPIO Pins *********")
PI_PIN_SETUP()
# Initialize the Audio playback System
pygame.mixer.init()	# must be done first to use the audio 
# Startup the Station ID announcer process
WriteToLog("****** Starting the idAnnouncer Process *********")

idAnnouncer = Process(target=ID_Watchdog, args=(idAnnouncerQueue,))
idAnnouncer.start() 

# Send the stations Call sign
WriteToLog("Sending Initial Callsign")
pygame.mixer.music.load("/home/pi/MPC8/MessagesEnglish/StationID/StationCallSignVoice.mp3")
pygame.mixer.music.play()
# Announce the system is ready for operation
WriteToLog("Announce system is online")
pygame.mixer.music.load("/home/pi/MPC8/MessagesEnglish/Status/SystemOnline.mp3")
pygame.mixer.music.play()
WriteToLog("***** Repeater system normal operation started *****")

#debug pin
time.sleep (65)
print ("Toggling COS_INT ON")
GPIO.output(DebugPin, 1)
time.sleep (5)
print ("Toggling COS_INT OFF")
GPIO.output(DebugPin, 0)

while True:
	try:
		time.sleep (1)
	except keyboardinterrupt:
		idAnnouncerQueue.put("Q") #kill the ID announcer
		sys.exit()


#################### References ############################
#1 raspi.tv/2013/how-to-use-interrupts-with-python-on-the-
#  raspberry-pi-and-rpi-gpio
#2 SoundOfText.com	- useful voice synthesizer (Google based)
#
############################################################
