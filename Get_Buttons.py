import board
import RPi.GPIO as GPIO
import time

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)


def get_button(pin_number):
    #Is the admin button being pressed?
    #Define pin 13 as the input for the button
    GPIO.setup(pin_number, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 
    state = GPIO.input(pin_number)
    return state



def read():
    #switch_pin = 19; button_pin = 26
    switch_pin = 17; button_pin = 27

    GPIO.setup(switch_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 
    GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    
    if GPIO.input(switch_pin) == 1:
        switch_state = True
    else:
        switch_state = False
    
    if GPIO.input(button_pin) == 1:
        button_state = True
    else:
        button_state = False
    
    return switch_state, button_state
        
def set_pin(pin_number, state):
    GPIO.cleanup(pin_number)
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    
    GPIO.setup(pin_number, GPIO.OUT)
    if state == False:
        GPIO.output(pin_number, GPIO.LOW)
    if state == True:
        GPIO.output(pin_number, GPIO.HIGH)
    
def main():
    GPIO.cleanup()
    
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    button_pin1 = 19
    button_pin2 = 26
    LED_pin = 20
    GPIO.setup(LED_pin, GPIO.OUT)
    GPIO.output(LED_pin, GPIO.LOW)
    GPIO.setup(button_pin1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 
    GPIO.setup(button_pin2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    while True:
        time.sleep(1)
        print(f"B1: {GPIO.input(button_pin1)}")
        print(f"B2: {GPIO.input(button_pin2)}")
        switch_pin = 19
        button_pin = 26
        if GPIO.input(switch_pin) == 1:
            switch_state = True
        else:
            switch_state = False
    
        if GPIO.input(button_pin) == 1:
            button_state = True
        else:
            button_state = False
        print(f"Switch {switch_state}, Button {button_state}")
if __name__ == "__main__":
    main()
    
    
    
# def main2():
    # while True:
        # button_pin1 = 35
        # button_pin2 = 37
        # B1 = get_button(button_pin1)
        # B2 = get_button(button_pin2)
        # print(f"Button 1 = {B1}, Button 2 = {B2}")
# def button_call():
    # print("Button was pressed")
    
# def main1():
    # GPIO.setwarnings(False)
    # GPIO.setmode(GPIO.BCM)
    # button_pin1 = 24
    # button_pin2 = 25
    # GPIO.setup(button_pin1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 
    # GPIO.setup(button_pin2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    
    # GPIO.add_event_detect(button_pin1, GPIO.RISING, callback=button_call)
    # GPIO.add_event_detect(button_pin2, GPIO.RISING, callback=button_call)
    # message = input('Press Enter to quit')
    # GPIO.cleanup()
