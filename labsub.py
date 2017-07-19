import paho.mqtt.client as paho
import os
import socket
import ssl
import json
import RPi.GPIO as gpio
from time import sleep
AC=3
LED=2

#setting up GPIO pins ,Pin=3=>AC,Pin=2=>LED as output to update according to desired state
gpio.setmode(gpio.BCM)
gpio.setup(AC,gpio.OUT)
gpio.setup(LED,gpio.OUT)

#checking connecton,and subscribing to topic in AWS IoT
def on_connect(mqtt_client, obj, flags, rc):
    if rc==0:
        print("Connection returned result: " + str(rc) +" success!!")
        mqtt_client.subscribe("$aws/things/MyRaspberryPi/shadow/update/accepted",qos=0)

        

    
#display message availabe on subscribed topic to terminal  
def on_message(mqttc, obj, msg): 
    print("Message received :"+msg.topic+" | QoS: "+str(msg.qos)+"| Data Recieved:"+str(msg.payload))
    payloadJson=json.loads(str(msg.payload))
    ACDesiredState=payloadJson['state']['desired']['AC']
    LEDDesiredState=payloadJson['state']['desired']['LED']


    print("Turned AC "+ACDesiredState)
    print("Turned LED "+LEDDesiredState)

    if(ACDesiredState=="ON"):
        gpio.output(AC,gpio.HIGH)
    else:
        gpio.output(AC,gpio.LOW)
    if(LEDDesiredState=="ON"):
        gpio.output(LED,gpio.HIGH)
    else:
        gpio.output(LED,gpio.LOW)

    payload="{\"state\":{\"reported\":{\"AC\":\""+ACDesiredState+"\",\"LED\":\""+LEDDesiredState+"\"}}}"
    mqtt_client.publish("$aws/things/MyRaspberryPi/shadow/update/delta",payload,0,True)

    

mqtt_client=paho.Client()
mqtt_client.on_connect=on_connect
mqtt_client.on_message=on_message

mqtt_client.tls_set("aws-iot-rootCA.crt",certfile="cert.pem",
                    keyfile="privkey.pem",cert_reqs=ssl.CERT_REQUIRED,
                    tls_version=ssl.PROTOCOL_TLSv1_2,ciphers=None)
mqtt_client.connect("apmhtrg5pymzk.iot.us-east-1.amazonaws.com",port=8883,keepalive=60)
mqtt_client.loop_forever()



'''gpio.setmode(gpio.BCM)
gpio.setup(2,gpio.IN)

    
gpio.cleanup()'''
