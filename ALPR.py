import cv2
import imutils
from imutils.video import VideoStream
import datetime
import argparse
import numpy as np
import pytesseract	
from PIL import Image
import subprocess
import os
import RPi.GPIO as GPIO   #Giriş çıkış kütüphanesi
import time

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)


while  True:
    #Kamera algılanıyor
    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--picamera", type=int, default=-1,
        help="whether or not the Raspberry Pi camera should be used")
    args = vars(ap.parse_args())


    vs = VideoStream(usePiCamera=args["picamera"] > 0).start()
    time.sleep(2.0)
    detected =0
    while  detected ==0:
        frame = vs.read()
        frame = imutils.resize(frame)
    
        #cv2.imshow("Kamera", frame)
        cv2.imwrite("Araba.jpg", frame)
    
        key = cv2.waitKey(1)#1
        img = cv2.imread('Araba.jpg',cv2.IMREAD_COLOR)
        #img = cv2.resize(img, (620,480) )

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) #convert to grey scale
        gray = cv2.bilateralFilter(gray, 11, 17, 17) #Blur to reduce noise
        edged = cv2.Canny(gray, 30, 200) #Perform Edge detection

        # find contours in the edged image, keep only the largest
        # ones, and initialize our screen contour
        cnts = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        cnts = sorted(cnts, key = cv2.contourArea, reverse = True)[:10]
        screenCnt = None

        # loop over our contours
        for c in cnts:
            # approximate the contour
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.018 * peri, True)
 
            # if our approximated contour has four points, then
            # we can assume that we have found our screen
            if len(approx) == 4:
                screenCnt = approx
                detected =1
                #vs = VideoStream(usePiCamera=args["picamera"] > 0).stop() 
                break
    #camera end
    
    img = cv2.imread('3.jpg',cv2.IMREAD_COLOR)
    img = cv2.resize(img, (620,480) )


    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) #convert to grey scale
    gray = cv2.bilateralFilter(gray, 11, 17, 17) #Blur to reduce noise
    edged = cv2.Canny(gray, 30, 200) #Perform Edge detection

    # find contours in the edged image, keep only the largest
    # ones, and initialize our screen contour
    cnts = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    cnts = sorted(cnts, key = cv2.contourArea, reverse = True)[:10]
    screenCnt = None

    # loop over our contours
    for c in cnts:
        # approximate the contour
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.018 * peri, True)
 
        # if our approximated contour has four points, then
        # we can assume that we have found our screen
        if len(approx) == 4:
            screenCnt = approx
            break
     
    if screenCnt is None:
        detected = 0
        
    else:
        detected = 1

    if detected == 1:
        cv2.drawContours(img, [screenCnt], -1, (0, 255, 0), 3)

    # Masking the part other than the number plate
    mask = np.zeros(gray.shape,np.uint8)
    new_image = cv2.drawContours(mask,[screenCnt],0,255,-1,)
    new_image = cv2.bitwise_and(img,img,mask=mask)
    
    # yeni crop
    (x, y) = np.where(mask == 255)
    (topx, topy) = (np.min(x), np.min(y))
    (bottomx, bottomy) = (np.max(x), np.max(y))
    Cropped = gray[topx:bottomx+1, topy:bottomy+1]

    # Numbara platesini Oku:
    gray  = cv2.bilateralFilter(Cropped , 11, 17, 17) #Blur to reduce noise
    text = pytesseract.image_to_string(gray, config='') #--psm 11
    bos=""
    if text ==bos:
        print("Arabanin Plaka Numarasi Yok.")
        cv2.imshow('image',img)
        cv2.imwrite('plakasiz Araba.jpg', img)
           
    else:    
        print(" Arabanin plaka Numarasi :",text )
        print(text)
        cv2.imshow('image',img)
        cv2.imshow('Cropped',Cropped)
        cv2.imwrite('Cropped.jpg', Cropped)
    i=0
    Araba_Tanimlik =["MAH 41","KA 03 AB 3289","5 6"]    # Plakalar burda tanımlanıyor
    #Graje islemler baslar
    if detected ==1 :
        for num in range(len(Araba_Tanimlik)):
            if text == Araba_Tanimlik[num] :	
                
                GPIO.setup(20,GPIO.OUT) # Garaj kapatma tanımladık
                GPIO.setup(21,GPIO.OUT) # Garaj açma tanımladık
                GPIO.setup(16,GPIO.OUT) #laser Sensör Çalıştırma
                GPIO.setup(26,GPIO.IN)  # 1.Limit Sensör
                GPIO.setup(19,GPIO.IN)  # Optik Sensör
                GPIO.setup(5,GPIO.IN)   # 2.Limit Sensör
                #while True:
                #time.sleep(10)
                print("Tanimli Araba\nGaraj Aciliyor..")
                GPIO.output(20,GPIO.LOW)
                GPIO.output(21,GPIO.HIGH)
                GPIO.output(16,GPIO.HIGH)
                #time.sleep(10)
                d=""
                while True:
                    #print(GPIO.input(26))
                    if GPIO.input(26) == 0:            
                        GPIO.output(21,GPIO.LOW)
                        print("nGaraj Acik\nArabe gicmesi bekleniyor..")
                        time.sleep(10)
                        #print(GPIO.input(19))
                        if GPIO.input(19)==1:
                            GPIO.output(20,GPIO.HIGH)
                            print("Garaj Kapaniyor..")
                            while True:
                                #print(GPIO.input(5))
                                if GPIO.input(5)==0:
                                    GPIO.output(20,GPIO.LOW)
                                    GPIO.output(16,GPIO.LOW)
                                    d=1
                                    
                                    break
                    gpi05 = GPIO.input(5)
                    if gpi05 == 0 and d==1:
                        print("KAPI KAPILI")
                        break
                #Graje islemler bitir
                
                subprocess.call(["tesseract", "Cropped.jpg", "known"])
                #os.system('cat known.txt >> TANIMLI-ARABALAR.txt')
                p = subprocess.Popen("date", stdout=subprocess.PIPE, shell=True)
                (output, err) = p.communicate()
                m=print("Tarih Ve Saat:", output)
                #os.system('echo "Today is", output >> TANIMLI-ARABALAR.txt')
                os.system('echo \tTarih Ve Saat: ' + str(output)+ ' >> TANIMLI-ARABALAR.txt')
                os.system('cat known.txt >> TANIMLI-ARABALAR.txt')
                if text == Araba_Tanimlik[num] :
                    break	
                    
        if text != Araba_Tanimlik[num] :	    
            GPIO.setup(12,GPIO.OUT)  # Kırmzı Led Ve Buzzer
            print("YAPANCI ARABA\nAlaram Calisiyor")
            GPIO.output(12,GPIO.HIGH)
            time.sleep(15)
            GPIO.output(12,GPIO.LOW)
            subprocess.call(["tesseract", "Cropped.jpg", "unknown"])
            p = subprocess.Popen("date", stdout=subprocess.PIPE, shell=True)
            (output, err) = p.communicate()
            m=print("Tarih Ve Saat:", output)
            os.system('echo \tTarih Ve Saat:  ' + str(output)+ '>> YAPANCI-ARABALAR.txt')
            if text == bos:
                os.system('echo \tArabanin Plaka Numarasi Yok.. >> YAPANCI-ARABALAR.txt')
            else:    
                os.system('cat unknown.txt >> YAPANCI-ARABALAR.txt')
                cv2.imwrite('YAPANCI\\' + str(i) + '_img.jpg', img)
                i+=1
    time.sleep(2)
    Devam=""
    yes="y"
    Yes="Y"
    cv2.waitKey(1)
    Devam=input("Devam Etmek için Kelvedan [Y] Botun Basabilirsiniz:")
    if Devam == yes or Devam== Yes :	
        print("Devam Ediyor ...")	
        #cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("Bitti .")
        #cv2.waitKey(0)
        cv2.destroyAllWindows()
        break     
        
                
   
  
     
    
    



