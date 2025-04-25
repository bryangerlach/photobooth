########################################################################################
# Photobooth - Python 3 Update
# Original author: Bryan Gerlach
# Updated by: Gemini AI Assistant
#
# Takes 3 pictures then outputs two copies to be printed on photo paper
#
#########################################################################################

import sys
import os
os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"
import cv2  # For webcam access
from PIL import Image, ImageDraw, ImageEnhance, ImageWin
import pygame
from pygame.locals import *
import time
import threading
import uuid
import win32print
import win32ui
import ftplib
import qrcode
from dotenv import load_dotenv

load_dotenv()

res = (960, 720)
# res = (640, 480)
pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.mixer.init()
pygame.init()

beep = pygame.mixer.Sound("beep.ogg")
camsound = pygame.mixer.Sound("camera.ogg")


# index = 0
# cameras = []
# while True:
#     cap = cv2.VideoCapture(index)
#     if not cap.read()[0]:
#         break
#     else:
#         cameras.append(index)
#     cap.release()
#     index += 1
# available_cameras = cameras

# if not available_cameras:
#     print("No cameras found.")

# print("Available cameras:")
# for i, camera_index in enumerate(available_cameras):
#     print(f"{i + 1}: Camera {camera_index}")

cap = cv2.VideoCapture(0)  # 0 usually represents the default webcam
if not cap.isOpened():
    print("Cannot open webcam")
    sys.exit()
cap.set(cv2.CAP_PROP_FRAME_WIDTH, res[0])
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, res[1])

screen = pygame.display.set_mode(res, pygame.FULLSCREEN)
pygame.display.set_caption('Photobooth')
pygame.font.init()
font1 = pygame.font.SysFont("minecraftten", 100)
font2 = pygame.font.SysFont("minecraftten", 45)
FTP_HOST = os.environ.get("FTP_HOST")
FTP_USER = os.environ.get("FTP_USER")
FTP_PASSWORD = os.environ.get("FTP_PASSWORD")
FTP_INDIVIDUAL_PATH = os.environ.get("FTP_INDIVIDUAL_PATH", "photobooth/individuals/")
FTP_STRIPS_PATH = os.environ.get("FTP_STRIPS_PATH", "photobooth/strips/")
LOCAL_PRINTS_PATH = os.environ.get("LOCAL_PRINTS_PATH", "prints")
LOCAL_PICS_PATH = os.environ.get("LOCAL_PICS_PATH", "pics")

COUNTDOWN = 3  # Define Count down Time in seconds
PHOTOCOUNT = 3  # Number of pictures to take in photo booth mode
LOCKTIME = 3  # seconds until lock starts
RANDOMMAX = 30  # maximum number of seconds between random photos
BORDERLENGTH = 20  # border length for polaroid and photobooth
brightness = 1.0
contrast = 1.0
shots = 0
displaytext = ""
displaytext2 = "Press P1 to Begin"
finishedimage = None

def uploadtoftp(filename):
    try:
        session = ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASSWORD)
        with open(os.path.join(LOCAL_PICS_PATH, filename), 'rb') as f:
            ftp_path = FTP_INDIVIDUAL_PATH.replace("\\", "/") + "/" + filename.replace("\\", "/")
            session.storbinary(f"STOR {ftp_path}", f)
        session.quit()
    except Exception as e:
        print(f"Error uploading {filename} to FTP: {e}")

def uploadtoftp2(filename):
    try:
        session = ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASSWORD)
        with open(os.path.join(LOCAL_PRINTS_PATH, filename), 'rb') as f:
            ftp_path = FTP_STRIPS_PATH.replace("\\", "/") + "/" + filename.replace("\\", "/")
            session.storbinary(f"STOR {ftp_path}", f)
        session.quit()
    except Exception as e:
        print(f"Error uploading {filename} to FTP (strips): {e}")

def disp(phrase, loc, font):
    s = font.render(phrase, True, (200, 200, 200))
    sh = font.render(phrase, True, (50, 50, 50))
    screen.blit(sh, (loc[0] + 1, loc[1] + 1))
    screen.blit(s, loc)

def printPhoto(file_name):
    HORZRES = 8
    VERTRES = 10
    LOGPIXELSX = 88
    LOGPIXELSY = 90
    PHYSICALWIDTH = 110
    PHYSICALHEIGHT = 111
    PHYSICALOFFSETX = 112
    PHYSICALOFFSETY = 113

    printer_name = win32print.GetDefaultPrinter()
    hDC = win32ui.CreateDC()
    hDC.CreatePrinterDC(printer_name)
    printable_area = hDC.GetDeviceCaps(HORZRES), hDC.GetDeviceCaps(VERTRES)
    printer_size = hDC.GetDeviceCaps(PHYSICALWIDTH), hDC.GetDeviceCaps(PHYSICALHEIGHT)
    printer_margins = hDC.GetDeviceCaps(PHYSICALOFFSETX), hDC.GetDeviceCaps(PHYSICALOFFSETY)
    try:
        bmp = Image.open(file_name)
        if bmp.size[0] > bmp.size[1]:
            bmp = bmp.rotate(90)
        ratios = [1.0 * printable_area[0] / bmp.size[0], 1.0 * printable_area[1] / bmp.size[1]]
        scale = min(ratios)
        hDC.StartDoc(file_name)
        hDC.StartPage()
        dib = ImageWin.Dib(bmp)
        scaled_width, scaled_height = [int(scale * i) for i in bmp.size]
        x1 = int((printer_size[0] - scaled_width) / 2)
        y1 = int((printer_size[1] - scaled_height) / 2)
        x2 = x1 + scaled_width
        y2 = y1 + scaled_height
        dib.draw(hDC.GetHandleOutput(), (x1, y1, x2, y2))
        hDC.EndPage()
        hDC.EndDoc()
    except Exception as e:
        print(f"Error printing {file_name}: {e}")
    finally:
        hDC.DeleteDC()

def capture_frame():
    ret, frame = cap.read()
    if ret:
        # OpenCV captures frames in BGR format, convert to RGB for Pillow
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(frame_rgb)
    else:
        print("Error capturing frame")
        return None

def countdown():
    global displaytext
    global displaytext2
    global finishedimage
    displaytext2 = ""
    photos = []
    x = 0
    while x < 3:
        for seconds in range(COUNTDOWN, 0, -1):
            displaytext = str(seconds)
            beep.play()
            time.sleep(1)
        camsound.play()
        actualfilename = f"{uuid.uuid4()}.jpg"
        filename = os.path.join(LOCAL_PICS_PATH, actualfilename)
        frame = capture_frame()
        if frame:
            # b = frame.transpose(Image.FLIP_LEFT_RIGHT) # Removed potentially redundant flip
            frame.save(filename, "JPEG")
            #### upload file to ftp site##################################################################################
            thread = threading.Thread(target=uploadtoftp, args=(actualfilename,))
            thread.start()
            #### done uploading###########################################################################################
            x = x + 1
            displaytext = ""
            time.sleep(1)
            photos.append(filename)
        else:
            print("Failed to capture photo, aborting countdown.")
            displaytext2 = "Error capturing photo"
            return

    if len(photos) == 3:
        try:
            image = Image.open(photos[0])
            xsize, ysize = image.size
            imagebackground = Image.new("RGB", ((xsize + (BORDERLENGTH * 2)) * 2, (len(photos) * (ysize + BORDERLENGTH) + BORDERLENGTH + 500)), "white")
            try:
                footer_image = Image.open("footer.jpg")
                imagebackground.paste(footer_image, (0, 0))
            except FileNotFoundError:
                print("Warning: footer.jpg not found.")

            lasty = 0
            for photo_path in photos:
                try:
                    image = Image.open(photo_path)
                    imagebackground.paste(image, (BORDERLENGTH, lasty + BORDERLENGTH))
                    imagebackground.paste(image, (BORDERLENGTH * 3 + xsize, lasty + BORDERLENGTH))
                    lasty += ysize + BORDERLENGTH
                except FileNotFoundError:
                    print(f"Warning: {photo_path} not found.")
                    return

            actualfilename = f"{uuid.uuid4()}.jpg"
            location = os.path.join(LOCAL_PRINTS_PATH, actualfilename)
            imagebackground.save(location, "JPEG")
            #### upload file to ftp site##################################################################################
            thread = threading.Thread(target=uploadtoftp2, args=(actualfilename,))
            thread.start()
            #### done uploading###########################################################################################
            finishedimage = photos
            ##### print photo ########################################################################################
            printPhoto(location)
            ###########################################################################################################
            # qrimage = qrcode.make(f"http://gerlachwedding.com/gallery/photos/photobooth/strips/{actualfilename}")
            # qrimage.save("qrcode.jpg", "JPEG")
        except Exception as e:
            print(f"Error processing images: {e}")
            displaytext2 = "Error creating print"
            return

    displaytext2 = "Press P1 to Begin"

while True:
    if finishedimage:
        for img_path in finishedimage:
            try:
                a = pygame.image.load(img_path).convert()
                screen.blit(a, (0, 0))
                pygame.display.flip()
                time.sleep(3)
            except pygame.error as e:
                print(f"Error loading image {img_path}: {e}")
        finishedimage = None
        # try:
        #     screen.blit(pygame.image.load("qrcode.jpg").convert(), (200, 0))
        #     pygame.display.flip()
        #     time.sleep(1)
        # except pygame.error as e:
        #     print(f"Error loading qrcode.jpg: {e}")
        # time.sleep(10)

    frame = capture_frame()
    if frame:
        camshot = ImageEnhance.Brightness(frame).enhance(brightness)
        camshot = ImageEnhance.Contrast(camshot).enhance(contrast)
        # Convert PIL Image to Pygame Surface
        mode = frame.mode
        size = frame.size
        data = frame.tobytes()
        camshot_pygame = pygame.image.frombuffer(data, size, mode)
        camshot_flipped = pygame.transform.flip(camshot_pygame, True, False)  # Flip horizontally
        screen.blit(camshot_flipped, (0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            cap.release()  # Release the webcam
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYUP and event.key == K_1:
            thread = threading.Thread(target=countdown)
            thread.start()

    keyinput = pygame.key.get_pressed()
    if keyinput[K_ESCAPE]:
        cap.release()  # Release the webcam
        pygame.quit()
        sys.exit()
    if keyinput[K_q]:
        print("Displaying Capture Pin Properties (Note: This might not work directly with OpenCV)")
        # OpenCV doesn't directly expose these properties in the same way.
        # You might need to use platform-specific APIs or other OpenCV functions.
        pass
    if keyinput[K_w]:
        print("Displaying Capture Filter Properties (Note: This might not work directly with OpenCV)")
        # Similar to K_q, OpenCV handles filters differently.
        pass

    disp(displaytext, (250, 160), font1)
    disp(displaytext2, (1, 160), font2)
    pygame.display.flip()

# Release the webcam when the script ends (although the loop is infinite here)
# Consider adding a proper exit condition and releasing the capture there.