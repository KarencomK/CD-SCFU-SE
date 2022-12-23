from umqtt.simple import MQTTClient
from machine import Pin, SoftI2C
from machine import PWM
from time import sleep
import ujson
import time
import ntptime
import dht
import ssd1306
from rtttl import RTTTL
import songs, time


#CONECTA REDE WIFI
def connect_scfu():
    import network
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        sta_if.active(True)
        sta_if.connect('Tudo-Junto-e-Reunido', 'elmamuller')
        while not sta_if.isconnected():
            pass # wait till connection
    print('network config:', sta_if.ifconfig())
    
connect_scfu()

ntptime.host = "1.europe.pool.ntp.org"
ntptime.settime()

# mqtt client setup
CLIENT_NAME = 'pi-iv-a'
BROKER_ADDR = 'broker.hivemq.com'
mqttc = MQTTClient(CLIENT_NAME, BROKER_ADDR, keepalive=60)

BTN_TOPIC = CLIENT_NAME.encode() + b'/dados'
print(BTN_TOPIC)
### -----------------------

#LEITURA DO SENSOR DE TEMPERATURA E UMIDADE DHT11
i=1
while True:
    print(i)
    i=i+1
    
    #ENTRADA DOS SENSORES NA ESP32
    sensor = dht.DHT11(Pin(23))
    led=Pin(15,Pin.OUT)
    led_waring=Pin(16,Pin.OUT)
    i2c = SoftI2C(scl=Pin(19), sda=Pin(21))
    # Setup a PWM reference to GPIO25 which is DAC1
    buz = PWM(Pin(22), freq=550, duty=0)
    #button = Pin(4, Pin.IN, Pin.PULL_UP)
### ------------------------ -------------------------------   
    #CONFIGURA  BUZZER
    # AJUSTE DO VOLUME
    pwm = 50
    
    def play_tone(freq, msec):
        #print('freq = {:6.1f} msec = {:6.1f}'.format(freq, msec))
        if freq > 0:
            buz.freq( int(freq) )
            buz.duty( int(pwm) )
        time.sleep_ms( int(msec * 0.9 ) )
        buz.duty(0)
        time.sleep_ms( int(msec * 0.1 ) )

    def play(tune):
        try:
            for freq, msec in tune.notes():
                play_tone(freq, msec)
        except KeyboardInterrupt:
            play_tone(0, 0)

    def play_song(search):
        play(RTTTL(songs.find(search)))
### ---------------------------------------------------
    
    #CONFIGURA DISPLAY
    oled_width = 128
    oled_height = 64
    oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)
    
### ------------------------------------------------------
    try:
        #VARIÁVEIS COM OS VALORES
        sensor.measure()
        temp = sensor.temperature()
        print("Temperature ", temp)
        humid = sensor.humidity()
        print("humidity ", humid)
        #ACENDE LED 
        led.value(1)
        
      #MOSTRA INFORMAÇÕES NO DISPLAY
        oled.text('Humidity:', 0, 10)
        #CONVERTE O VALOR DE NUMERO PARA STRING
        humidity_string = str(humid)
        oled.text(humidity_string , 10, 20)
        oled.text('%', 30, 20)
        oled.text('Temperature:', 0, 30)
        #CONVERTE O VALOR DE NUMERO PARA STRING
        temperature_string = str(temp)
        oled.text(temperature_string, 10, 40)
        oled.text('C', 30, 40)
        oled.text('FELIZ NATAL', 20, 50)
        oled.show()
        #TOCA A MUSICA
        play_song('StarWars')
        
    except OSError as err:
        print("Waring! Error reading data")
        led_waring.value(1)
        #MOSTRA INFORMAÇÕES NO DISPLAY
        oled.text('WARING!', 30, 20)
        oled.text('Error reading data', 0, 30)
        oled.show()
        #TOCA A MUSICA
        play_song('The Simpsons')
 ### ---------------------------------------------------
        
#OBTEM DATA E HORA DA PUBLICAÇÃO
    ano=time.localtime()[0]
    mes=time.localtime()[1]
    dia=time.localtime()[2]
    hora=time.localtime()[3]
    hfl=[21,22,23,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]
    horalocal=hfl[hora]
    minuto=time.localtime()[4]
    segundo=time.localtime()[5]
    datahora=str(ano)+"-"+str(mes)+"-"+str(dia)+" "+str(horalocal)+ ":"+str(minuto)+ ":"+str(segundo)
    print(datahora)

#VALORES A SEREM PUBLICADOS:
    
#TEMPERATURA    
    dict = {}                                                                                                                                                                                                   
    dict["Valor"] = temp
    dict["DataHora"] = datahora
    dict["Descricao"] = "Temperatura"
    dict["Origem"] = "Karen"
    print(dict)
    
    publicacao = ujson.dumps(dict)
    print(publicacao)
    
#UMIDADE    
    dictu = {}                                                                                                                                                                                                   
    dictu["Valor"] = humid
    dictu["DataHora"] = datahora
    dictu["Descricao"] = "Umidade"
    dictu["Origem"] = "Karen"
    print(dictu)
    
    publicacaoUmidade = ujson.dumps(dictu)
    print(publicacaoUmidade)
    
#CONECTA E PUBLICA VIA MQTT
    mqttc.connect()
    mqttc.publish(BTN_TOPIC, publicacao.encode())
    mqttc.publish(BTN_TOPIC, publicacaoUmidade.encode())
    mqttc.disconnect()

#PUBLICA A CADA 10 MIM
    sleep(300)