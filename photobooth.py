######################################################################
#                                                                    #
#                                MATT CAM                            #
#                              Version : 1.1                         #
#                                                                    #
#    Description :                                                   #
#                 Raspberry PI Photobooth Software                   #
#         Author :                                                   #
#                 Matt Inglis                                        #
#                                                                    #
######################################################################

#IMPORTS
import RPi.GPIO as gpio
import picamera
import pygame
import time
import os
import PIL.Image
import ImageDraw
import cups

from threading import Thread
from pygame.locals import *
from time import sleep
from PIL import Image


#initialise global variables
closeme = True #Loop Control Variable
timepulse = 999 #Pulse Rate of LED
LEDon = False #LED Flashing Control
gpio.setmode(gpio.BCM) #Set GPIO to BCM Layout
Numeral = "" #Numeral is the number display
Message = "" #Message is a fullscreen message
SmallMessage = "" #SmallMessage is a lower banner message
TotalImageCount = 1 #Counter for Display and to monitor paper usage
PhotosPerCart = 16 #Selphy takes 16 sheets per tray

#initialise pygame
pygame.mixer.pre_init(44100, -16, 1, 1024*3) #PreInit Music, plays faster
pygame.init() #Initialise pygame
screen = pygame.display.set_mode((800,480),pygame.FULLSCREEN) #Full screen 640x480
background = pygame.Surface(screen.get_size()) #Create the background object
background = background.convert() #Convert it to a background

#UpdateDisplay - Thread to update the display, neat generic procedure
def UpdateDisplay():
   #init global variables from main thread
   global Numeral
   global Message
   global SmallMessage
   global TotalImageCount
   global screen
   global background
   global pygame

   SmallText = "Matt Cam" #Default Small Message Text   
   if(TotalImageCount >= (PhotosPerCart - 2)): #Low Paper Warning at 2 images less
      SmallText = "Paper Running Low!..."
   if(TotalImageCount >= PhotosPerCart): #Paper out warning when over Photos per cart
      SmallMessage = "Paper Out!..."
      TotalImageCount = 0 
   background.fill(pygame.Color("black")) #Black background
   smallfont = pygame.font.Font(None, 50) #Small font for banner message
   SmallText = smallfont.render(SmallText,1, (255,0,0))
   background.blit(SmallText,(10,445)) #Write the small text
   SmallText = smallfont.render(`TotalImageCount`+"/"+`PhotosPerCart`,1, (255,0,0))
   background.blit(SmallText,(710,445)) #Write the image counter

   if(Message != ""): #If the big message exits write it
      font = pygame.font.Font(None, 180)
      text = font.render(Message, 1, (255,0,0))
      textpos = text.get_rect()
      textpos.centerx = background.get_rect().centerx
      textpos.centery = background.get_rect().centery
      background.blit(text, textpos)
   elif(Numeral != ""): # Else if the number exists display it
      font = pygame.font.Font(None, 800)
      text = font.render(Numeral, 1, (255,0,0))
      textpos = text.get_rect()
      textpos.centerx = background.get_rect().centerx
      textpos.centery = background.get_rect().centery
      background.blit(text, textpos)

   screen.blit(background, (0,0))
   pygame.draw.rect(screen,pygame.Color("red"),(10,10,770,430),2) #Draw the red outer box
   pygame.display.flip()
   
   return
#Pulse Thread - Used to pulse the LED without slowing down the rest
def pulse(threadName, *args):
        #gpio.setmode(gpio.BCM)
   global gpio
        gpio.setup(17, gpio.OUT)
   
   #print timepulse
          while closeme:
             global LEDon

                #print LEDon
                
                if timepulse == 999:
                        gpio.output(17, False)
                        LEDon = True
                else:
                        if LEDon:
                                gpio.output(17, True)
                                time.sleep(timepulse)
                                LEDon = False
                        else:
                                gpio.output(17, False)
                                time.sleep(timepulse)
                                LEDon = True

#Main Thread
def main(threadName, *args):

   #Setup Variables
        gpio.setup(24, gpio.IN) #Button on Pin 24 Reprints last image
        gpio.setup(22, gpio.IN) #Button on Pin 22 is the shutter
        global closeme
        global timepulse
   global TotalImageCount
   global Numeral
   global SmallMessage
   global Message
      
   Message = "Loading..."
        UpdateDisplay()
   time.sleep(5) #5 Second delay to allow USB to mount

        #Initialise the camera object
        camera = picamera.PiCamera()
        #Transparency allows pigame to shine through
        camera.preview_alpha = 120
        camera.vflip = False
        camera.hflip = True
        camera.rotation = 90
        camera.brightness = 45
        camera.exposure_compensation = 6
        camera.contrast = 8
        camera.resolution = (1280,720)
        #Start the preview
        camera.start_preview()

   Message = "USB Check..."
   UpdateDisplay()

        #Following is a check to see there is a USB mounted if not it loops with a USB message
        usbcheck = False
        rootdir = '/media/'

        while not usbcheck:
                dirs = os.listdir(rootdir)
                for file in dirs:
                    folder = os.path.join(rootdir,file)
                    if not file == 'SETTINGS' and os.path.isdir(folder):
                        usbcheck = True
                        imagedrive = os.path.join(rootdir,file)
                        imagefolder = os.path.join(imagedrive,'PhotoBooth')
                        #If a photobooth folder on the usb doesn't exist create it
                        if not os.path.isdir(imagefolder):
                                os.makedirs(imagefolder)

   Message = "Initialise"
   UpdateDisplay()
        #Procedure checks if a numerical folder exists, if it does pick the next number
        #each start gets a new folder i.e. /photobooth/1/ etc
        notfound = True
        folderno = 1
        while notfound:
        
                tmppath = os.path.join(imagefolder,`folderno`)
                if not os.path.isdir(tmppath):
                        os.makedirs(tmppath)
                        imagefolder = tmppath
                        notfound = False
                else:
                        folderno = folderno + 1

        imagecounter = 0

   Message = ""
   UpdateDisplay()

        #Main Loop
        while closeme:
                
                try:
                        for event in pygame.event.get():
                                if event.type == pygame.QUIT:
                                        closeme = False
                                if event.type == pygame.KEYDOWN:
                           if event.key == pygame.K_ESCAPE:
                              closeme = False
                except KeyboardInterrupt:
                                closeme = False
                        
                #input_value is the shutter
                input_value = gpio.input(22)
                #input_value2 is photo reprint
                input_value2 = gpio.input(24)
            
      UpdateDisplay()

                #Load a beep music file
                pygame.mixer.music.load('/home/pi/Desktop/Beep.mp3')
                #Reprint Button has been pressed
                if input_value2==False:
                        #If the temp image exists send it to the printer
                        if os.path.isfile('/home/pi/Desktop/tempprint.jpg'):
                      #Open a connection to cups
                       conn = cups.Connection()
                     #get a list of printers
                       printers = conn.getPrinters()
                     #select printer 0
                       printer_name = printers.keys()[0]
                       Message = "Re-Print..."
                       UpdateDisplay()
                  #print the buffer file
                  printqueuelength = len(conn.getJobs())
                  if  printqueuelength > 1:
                     Message = "PRINT ERROR"
                     conn.enablePrinter(printer_name)
                     UpdateDisplay()
                  elif printqueuelength == 1:
                     SmallMessage = "Print Queue Full!"
                     UpdateDisplay()
                     conn.enablePrinter(printer_name)
                  conn.printFile(printer_name,'/home/pi/Desktop/tempprint.jpg',"PhotoBooth",{})
                       time.sleep(20)
                       Message = ""
                  UpdateDisplay()

            #input_value is the shutter release
                if input_value == False:
                    subimagecounter = 0
               #Increment the image number
               imagecounter = imagecounter + 1
               #play the beep
               pygame.mixer.music.play(0)
               #Display the countdown number
               Numeral = "5"
               UpdateDisplay()
               #Flash the light at half second intervals
               timepulse = 0.5
               # 1 second between beeps
               time.sleep(1)

               pygame.mixer.music.play(0)
               Numeral = "4"
               UpdateDisplay()
               timepulse = 0.4
               time.sleep(1)
               
               pygame.mixer.music.play(0)
               Numeral = "3"
               UpdateDisplay()
               timepulse = 0.3
                                 time.sleep(1)

                              pygame.mixer.music.play(0)
                              Numeral = "2"
                        UpdateDisplay()
                        timepulse = 0.2
                              time.sleep(1)
                
                              pygame.mixer.music.play(0)
                              Numeral = "1"
                        UpdateDisplay()
                        timepulse = 0.1
                                time.sleep(1)

               #Camera shutter sound
                              pygame.mixer.music.load('/home/pi/Desktop/camera.mp3')
                              pygame.mixer.music.play(0)
                              Numeral = ""
                        Message = "Smile!"
                        UpdateDisplay()
               #increment the subimage
               subimagecounter = subimagecounter + 1
               #create the filename
                              filename = 'image'
                              filename += `imagecounter`
                              filename += '_'
                              filename += `subimagecounter`
                              filename += '.jpg'
               #capture the image
                              camera.capture(os.path.join(imagefolder,filename))
               #create an image object
                              im = PIL.Image.open(os.path.join(imagefolder,filename)).transpose(Image.FLIP_LEFT_RIGHT)
                              pygame.mixer.music.load('/home/pi/Desktop/Beep.mp3')
                              Message = "Get Ready"
                              UpdateDisplay()
                        timepulse = 999
                              time.sleep(3)

                                pygame.mixer.music.play(0)
                              Message = ""
               Numeral = "5"
               UpdateDisplay()
                              timepulse = 0.5
                              time.sleep(1)
                        
                              pygame.mixer.music.play(0)
                              Numeral = "4"
               UpdateDisplay()
               timepulse = 0.4
                              time.sleep(1)

                              pygame.mixer.music.play(0)
                              Numeral = "3"
               UpdateDisplay()
               timepulse = 0.3
                              time.sleep(1)
                                
                              pygame.mixer.music.play(0)
                              Numeral = "2"
               UpdateDisplay()
               timepulse = 0.2
                              time.sleep(1)
                        
                              pygame.mixer.music.play(0)
                              Numeral = "1"
               UpdateDisplay()
                              timepulse = 0.1
                              time.sleep(1)
                        
                              pygame.mixer.music.load('/home/pi/Desktop/camera.mp3')
                              pygame.mixer.music.play(0)
               Numeral = ""
               Message = "Smile!"
               UpdateDisplay()

                              subimagecounter = subimagecounter + 1

                                filename = 'image'
                              filename += `imagecounter`
                              filename += '_'
                              filename += `subimagecounter`
                              filename += '.jpg'
                              camera.capture(os.path.join(imagefolder,filename))
                              im2 = PIL.Image.open(os.path.join(imagefolder,filename)).transpose(Image.FLIP_LEFT_RIGHT)
                              pygame.mixer.music.load('/home/pi/Desktop/Beep.mp3')
                              Message = "Another One"
               UpdateDisplay()
               timepulse = 999
                              time.sleep(3)
                  
                              pygame.mixer.music.play(0)
                              Numeral = "5"
               Message = ""
               UpdateDisplay()
                              timepulse = 0.5
                              time.sleep(1)
                        
                              pygame.mixer.music.play(0)
                              Numeral = "4"
               UpdateDisplay()
               timepulse = 0.4
                              time.sleep(1)

                              pygame.mixer.music.play(0)
                              Numeral = "3"
               UpdateDisplay()
               timepulse = 0.3
                              time.sleep(1)
                                
                              pygame.mixer.music.play(0)
                              Numeral = "2"
               UpdateDisplay()
               timepulse = 0.2
                              time.sleep(1)
                        
                              pygame.mixer.music.play(0)
                              Numeral = "1"
               UpdateDisplay()
                              timepulse = 0.1
                              time.sleep(1)
                        
                              pygame.mixer.music.load('/home/pi/Desktop/camera.mp3')
               pygame.mixer.music.play(0)
               Numeral = ""
               Message = "Smile!"
               UpdateDisplay()

                              subimagecounter = subimagecounter + 1

                              filename = 'image'
                              filename += `imagecounter`
                              filename += '_'
                              filename += `subimagecounter`
                              filename += '.jpg'
                              camera.capture(os.path.join(imagefolder,filename))
                              im3 = PIL.Image.open(os.path.join(imagefolder,filename)).transpose(Image.FLIP_LEFT_RIGHT)
                              pygame.mixer.music.load('/home/pi/Desktop/Beep.mp3')
                              Message = "Final One!"
               UpdateDisplay()
               timepulse = 999
                              time.sleep(3)
                        
                              pygame.mixer.music.play(0)
                              Message = ""
               Numeral = "5"
               UpdateDisplay()
               timepulse = 0.5
                              time.sleep(1)
                        
                              pygame.mixer.music.play(0)
                              Numeral = "4"
               UpdateDisplay()
               timepulse = 0.4
                              time.sleep(1)

                              pygame.mixer.music.play(0)
                              Numeral  = "3"
               UpdateDisplay()
               timepulse = 0.3
                              time.sleep(1)
                        
                                pygame.mixer.music.play(0)
                              Numeral = "2"
               UpdateDisplay()
               timepulse = 0.2
                              time.sleep(1)
                        
                              pygame.mixer.music.play(0)
                              time.sleep(0.1)
                              Numeral = "1"
               UpdateDisplay()
                              timepulse = 0.1
                              time.sleep(1)
                        
                              pygame.mixer.music.load('/home/pi/Desktop/camera.mp3')
                              pygame.mixer.music.play(0)
                              Numeral = ""
               Message = "Smile!"
               UpdateDisplay()
               subimagecounter = subimagecounter+1
   
                              filename = 'image'
                              filename += `imagecounter`
                              filename += '_'
                              filename += `subimagecounter`
                              filename += '.jpg'
                              camera.capture(os.path.join(imagefolder,filename))
                              Message = "Working.."
               UpdateDisplay()
               im4 = PIL.Image.open(os.path.join(imagefolder,filename)).transpose(Image.FLIP_LEFT_RIGHT)
                  
               #Load the background template
                              bgimage = PIL.Image.open("/home/pi/Desktop/template.jpg")
               #thumbnail the 4 images
                              im.thumbnail((560,400))
                              im2.thumbnail((560,400))
                              im3.thumbnail((560,400))
                              im4.thumbnail((560,400))
               #paste the thumbnails to the background images
                              bgimage.paste(im,(15,20))
                              bgimage.paste(im2,(15,410))
                              bgimage.paste(im3,(15,820))
                              bgimage.paste(im4,(15,1230))
               #two columns of 4
                              bgimage.paste(im,(620,20))
                              bgimage.paste(im2,(620,410))
                              bgimage.paste(im3,(620,820))
                              bgimage.paste(im4,(620,1230))
               #Create the final filename
                              Final_Image_Name = os.path.join(imagefolder,"Final_"+`imagecounter`+".jpg")
               #Save it to the usb drive
                              bgimage.save(os.path.join(imagefolder,"Final_"+`imagecounter`+".jpg"))
               #Save a temp file, its faster to print from the pi than usb
                              bgimage.save('/home/pi/Desktop/tempprint.jpg')
                  
               #Connect to cups and select printer 0
                              conn = cups.Connection()
                              printers = conn.getPrinters()
                              printer_name = printers.keys()[0]
                        
               #Increment the large image counter
                              TotalImageCount = TotalImageCount + 1
               Message = "Print..."
               UpdateDisplay()
               #print the file
               printqueuelength = len(conn.getJobs())
               #If multiple prints in the queue error
               if  printqueuelength > 1:
                  Message = "PRINT ERROR"
                  conn.enablePrinter(printer_name)
                  UpdateDisplay()
               elif printqueuelength == 1:
                  SmallMessage = "Print Queue Full!"
                  conn.enablePrinter(printer_name)
                  UpdateDisplay()
                     
               conn.printFile(printer_name,'/home/pi/Desktop/tempprint.jpg',"PhotoBooth",{}) 
                              time.sleep(20)
                        
                              Message = ""
               UpdateDisplay()
               timepulse = 999
               #reset the shutter switch
                              while input_value == False:
                                      input_value = gpio.input(22)
   #we are exiting so stop preview
   camera.stop_preview()

#launch the main thread
Thread(target=main, args=('Main',1)).start()
#launch the pulse thread
Thread(target=pulse, args=('Pulse',1)).start()
#sleap
time.sleep(5)


