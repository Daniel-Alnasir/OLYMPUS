import board
import busio
import time
from PIL import Image, ImageDraw, ImageFont
import qrcode
from threading import Timer

#https://www.blog.pythonlibrary.org/2021/02/02/drawing-text-on-images-with-pillow-and-python/
#pip3 install adafruit-circuitpython-ssd1306
#sudo apt-get install python3-pil
#sudo apt-get install python3-numpy

i2c = busio.I2C(board.SCL, board.SDA)

import adafruit_ssd1306
#Screen Parameters
WIDTH = 128
HEIGHT = 64
BORDER = 5

#Default text, my measurements
TEXT_HEIGHT = 11
SPACE_WIDTH = 6
font = ImageFont.load_default()

oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=0x3d)


def generate_Gform_QR(new_UID):

    url = f"https://docs.google.com/forms/d/e/1FAIpQLSdXIPnJPoPdBreH9FOQjW-s5nUuZ4QHThNK59u3kmUDplx3Bg/viewform?usp=pp_url&entry.181306502={new_UID}"
    qr = qrcode.QRCode(version = 10,
                       box_size = 1,
                       border = 4)

    qr.add_data(url)
    qr.make(fit=True)

    #Creates a PIL Image
    qr_image = qr.make_image(fill_color = "black" , back_color = "white")
    
    return qr_image

def initialize_OLED_image():
    #Creating a white background the same size as the screen
    desired_size = (128, 64)
    white_background = Image.new("1", desired_size, "white")
    draw = ImageDraw.Draw(white_background)
    oled.image(white_background)
    return white_background, draw
#draw.text((0, 20),text, font=font, fill=0)



def split_OLED_text(message):
    #Splits a message into multiple lines so it fits
    # Load default font.

    MAX_TEXT_LENGTH = 63

    
    lines_of_text = []
    
    (message_width, message_height) = font.getsize(message)
    
    if message_width > MAX_TEXT_LENGTH:
        message = message.split()
        current_line = ""
        for word in message:
            print(current_line)
            (current_line_width, current_line_height) = font.getsize(current_line)
            (word_line_width, word_line_height) = font.getsize(word)
            
            if (current_line_width + word_line_width + SPACE_WIDTH) <= MAX_TEXT_LENGTH:
                if len(current_line) > 0:
                    current_line += " " + word
                else:
                    current_line = word
            else:
                lines_of_text.append(current_line)
                current_line = word
        
        if current_line:
            lines_of_text.append(current_line)
            return lines_of_text
    
    else:
        lines_of_text.append(message)
        return lines_of_text





def draw_text(draw, white_background, text_split_list):
    # Load default font.
    y_position = 0
    speech_delay = 0.25
    print("OLED Message", text_split_list)
    for line in text_split_list:
        draw.text((1, y_position),line, font=font, fill=0)
        time.sleep(speech_delay)
        oled.image(white_background)
        oled.show()
        y_position += 10

def OLED_off(time_out_seconds = 60):
    if time_out_seconds > 0:
        t = Timer(time_out_seconds, shutoff_thread)
        t.start()
    else:
        oled.fill(0)
        oled.show()
    return None

def shutoff_thread():
    oled.fill(0)
    oled.show()


def Process_Message(draw, white_background, message):
    text_split_list = split_OLED_text(message)
    draw_text(draw, white_background, text_split_list)    

    
def Process_Image(draw, white_background, image):
    # Paste the 64x64 image onto the white background
    paste_position = (64, 0)
    white_background.paste(image, paste_position)
    oled.image(white_background)
    oled.show()

def New_Message(message):
    oled.fill(0)
    oled.show()
    
    #Create objects for PIL stuff
    white_background, draw = initialize_OLED_image()

    Process_Message(draw, white_background, message)

def New_Image(image, position = (64, 0)):
    white_background, draw = initialize_OLED_image()
    paste_position = position
    white_background.paste(image, paste_position)
    oled.image(white_background)
    oled.show()

def New_UID_QR_Image(UID):
    white_background, draw = initialize_OLED_image()
    qr_img = generate_Gform_QR(UID)
    Process_Image(draw, white_background, qr_img)
    
# Display imagej
if __name__ == "__main__":
    #Clears the screen and sets the pixels off
    oled.fill(0)
    oled.show()
    
    #Create objects for PIL stuff
    white_background, draw = initialize_OLED_image()
    message = "this is a very long sentence to be split into parts."
    Process_Message(draw, white_background, message)
    print("Sleeping")
    time.sleep(2)
    qr_img = generate_Gform_QR("666666")
    Process_Image(draw, white_background, qr_img)
    time.sleep(2)
    OLED_off()



