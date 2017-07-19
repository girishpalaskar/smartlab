import paho.mqtt.client as paho
import os
import socket
import ssl
import json
import serial
import RPi.GPIO as gpio
from time import sleep
import requests
#import dht
import Temp_DHT
from random import uniform

connflag=False
AC=3
LED=2

#setting up GPIO pins ,Pin=3=>AC,Pin=2=>LED as input to get reported state
gpio.setmode(gpio.BCM)
gpio.setup(LED,gpio.IN)
gpio.setup(AC,gpio.IN)

'''ser=serial.Serial('/dev/ttyACM0',9600)'''


pin_to_light=17

#RC time caluation method for LDR and 1uF capacitor
def rc_time (pin_to_light):
    count=0
    gpio.setup(pin_to_light,gpio.OUT)
    gpio.output(pin_to_light,gpio.LOW)
    sleep(0.1)

    gpio.setup(pin_to_light,gpio.IN)
    
    while(gpio.input(pin_to_light)==gpio.LOW):
        count = count+1
    return count

#checking connecton, and setting connection flag method
def on_connect(mqtt_client, obj, flags, rc):
    if rc==0:
        print("Connection returned result: " + str(rc) +" success!!")
        global connflag
        connflag=True
        
        
    
#display msg to terminal if any from AWS IoT 
def on_message(mqttc, obj, msg): 
    print("Message received :"+msg.topic+" | QoS: "+str(msg.qos)+"| Data Recieved:"+str(msg.payload))


 
    

mqtt_client=paho.Client()#initalize  MQTT client
mqtt_client.on_connect=on_connect#call to on_connect method
mqtt_client.on_message=on_message#call to on_message method

#configuring network encryption and authentication options. Enables SSL/TLS support.
mqtt_client.tls_set("aws-iot-rootCA.crt",certfile="cert.pem",
                    keyfile="privkey.pem",cert_reqs=ssl.CERT_REQUIRED,
                    tls_version=ssl.PROTOCOL_TLSv1_2,ciphers=None)
#connect with AWS IoT thing over port 8883
mqtt_client.connect("apmhtrg5pymzk.iot.us-east-1.amazonaws.com",port=8883,keepalive=60)
mqtt_client.loop_start()





while True:
    if connflag==True:
        #r=requests.get('http://api.openweathermap.org/data/2.5/weather?q=pune&APPID=735b03717053acba94b5a4b867f6c2ce')
        temp=Temp_DHT.temp#Get temperature from DHT11 
        '''while (isinstance(dht.Temperature,int)):
            temp=Temp_DHT #dht.Temperature #r.json()['main']['temp']-273       #ser.readline()  #
        else:
            temp=r.json()['main']['temp']-273 '''
        print("current room temp:"+str(temp))

        light=12000-rc_time (pin_to_light) #calibrate RC time to light intensity,Dark :less light intensity and Bright:more light intensity
        print("current room light intensity:"+str(light))
        #ACCurrentStatus=input("AC status 0/1:")
        #LEDCurrentStatus=input("LED status 0/1:")
        
        tempPayload="{\"value\":\""+str(temp)+"\"}"
        lightPayload="{\"value\":\""+str(light)+"\"}"
        mqtt_client.publish("temperature",tempPayload,qos=1)#publish temperature value on user defined topic in JSON format  with QoS=1
        print("msg sent:temperature="+"%.2f" % temp)
        mqtt_client.publish("light",lightPayload,qos=1)#publish light intensity value on user defined topic in JSON format with QoS=1
        print("msg sent:light="+"%.2f" % light)

        #by reading gpio pin current statue of AC and LED  is set
        if(gpio.input(AC)==gpio.HIGH):
            ACCurrentStatus="ON"
        else:
            ACCurrentStatus="OFF"
        if(gpio.input(LED)==gpio.HIGH):
            LEDCurrentStatus="ON"
        else:
            LEDCurrentStatus="OFF" 

        #ACCurrentStatus=input("AC status 0/1:")
        #LEDCurrentStatus=input("LED status 0/1:")
        print("ACCurrentStatus:"+ACCurrentStatus)
        print("LEDCurrentStatus:"+LEDCurrentStatus)


        if(temp>=30 and light<=10000):
            print("Turn AC ON,as temp>30")
            print("Turn LED bulb ON,as light<10000")
            #to publish message payload on reserved topic ,framing payload in JSON format
            payload="{\"state\":{\"reported\":{\"AC\":\""+ACCurrentStatus+"\",\"LED\":\""+LEDCurrentStatus+"\"},\"desired\":{\"AC\":\"ON\",\"LED\":\"ON\"}}}"
            mqtt_client.publish("$aws/things/MyRaspberryPi/shadow/update",payload,0,True)
        elif(temp<=30 and light<=10000):
            print("Turn AC OFF,as temp<30")
            print("Turn LED bulb ON,as light<10000")
            payload="{\"state\":{\"reported\":{\"AC\":\""+ACCurrentStatus+"\",\"LED\":\""+LEDCurrentStatus+"\"},\"desired\":{\"AC\":\"OFF\",\"LED\":\"ON\"}}}"
            mqtt_client.publish("$aws/things/MyRaspberryPi/shadow/update",payload,0,True)
        elif(temp>=30 and light>=10000):
            print("Turn AC ON,as temp>30")
            print("Turn LED bulb OFF,as light>10000")
            payload="{\"state\":{\"reported\":{\"AC\":\""+ACCurrentStatus+"\",\"LED\":\""+LEDCurrentStatus+"\"},\"desired\":{\"AC\":\"ON\",\"LED\":\"OFF\"}}}"
            mqtt_client.publish("$aws/things/MyRaspberryPi/shadow/update",payload,0,True)
        elif(temp<=30 and light>=10000):
            print("Turn AC OFF,as temp<30")
            print("Turn LED bulb OFF,as light>10000")
            payload="{\"state\":{\"reported\":{\"AC\":\""+ACCurrentStatus+"\",\"LED\":\""+LEDCurrentStatus+"\"},\"desired\":{\"AC\":\"OFF\",\"LED\":\"OFF\"}}}"
            mqtt_client.publish("$aws/things/MyRaspberryPi/shadow/update",payload,0,True)
        
    else:
        print("waiting for connection...")
    sleep(20)
