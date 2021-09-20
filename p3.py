# Import libraries
import RPi.GPIO as GPIO
import random
import ES2EEPROMUtils
import os
import time

# some global variables that need to change as we run the program
end_of_game = None  # set if the user wins or ends the game
address = 0
score = 0

# DEFINE THE PINS USED HERE
LED_value = [11, 13, 15]
LED_accuracy = 32
btn_submit = 16
btn_increase = 18
buzzer = 33
eeprom = ES2EEPROMUtils.ES2EEPROM()
PWM_b = None
PWM_l = None
numberOfGuess = 0
value = 1

# Print the game banner
def welcome():
    os.system('clear')
    print("  _   _                 _                  _____ _            __  __ _")
    print("| \ | |               | |                / ____| |          / _|/ _| |")
    print("|  \| |_   _ _ __ ___ | |__   ___ _ __  | (___ | |__  _   _| |_| |_| | ___ ")
    print("| . ` | | | | '_ ` _ \| '_ \ / _ \ '__|  \___ \| '_ \| | | |  _|  _| |/ _ \\")
    print("| |\  | |_| | | | | | | |_) |  __/ |     ____) | | | | |_| | | | | | |  __/")
    print("|_| \_|\__,_|_| |_| |_|_.__/ \___|_|    |_____/|_| |_|\__,_|_| |_| |_|\___|")
    print("")
    print("Guess the number and immortalise your name in the High Score Hall of Fame!")


# Print the game menu
def menu():
    global end_of_game
    global value
    global score
    global PWM_b
    global PWM_l
    PWM_b.stop()
    PWM_l.stop()
    end_of_game = False
    option = input("Select an option:   H - View High Scores     P - Play Game       Q - Quit\n")
    option = option.upper()
    if option == "H":
        os.system('clear')
        print("HIGH SCORES!!")
        s_count, ss = fetch_scores()
        display_scores(s_count, ss)
    elif option == "P":
        os.system('clear')
        score = 0
        print("Starting a new round!")
        print("Use the buttons on the Pi to make and submit your guess!")
        print("Press and hold the guess button to cancel your game")
        value = generate_number()
        while not end_of_game:
            pass
    elif option == "Q":
        print("Come back soon!")
        exit()
    else:
        print("Invalid option. Please select a valid one!")


def display_scores(count, raw_data):
    # print the scores to the screen in the expected format
    num_in_range = 3
    if (count < 3):
        num_in_range = count
    if (count == 0):
        print("There are no scores available")
        return
    if (count == 1):
        print("There is 1 score available.")
    else: 
        print("There are {} scores. Here are the top {}!".format(count,num_in_range))
    # print out the scores in the required format
    for i in range(num_in_range):
        print("{} - {} took {} guesses".format(i+1,raw_data[i][0],raw_data[i][1]))


# Setup Pins
def setup():
    global PWM_b, PWM_l
    # Setup board mode
    GPIO.setmode(GPIO.BOARD)
    # Setup regular GPIO
    GPIO.setup(LED_value[0],GPIO.OUT)
    GPIO.setup(LED_value[1],GPIO.OUT)
    GPIO.setup(LED_value[2],GPIO.OUT)
    clearLeds()
    GPIO.setup(btn_submit,GPIO.IN,pull_up_down=GPIO.PUD_UP)
    GPIO.setup(btn_increase,GPIO.IN,pull_up_down=GPIO.PUD_UP)
    GPIO.setup(buzzer,GPIO.OUT)
    GPIO.setup(LED_accuracy,GPIO.OUT)
    
    # Setup PWM channels
    GPIO.output(buzzer,0)
    PWM_b = GPIO.PWM(buzzer,1)

    GPIO.output(LED_accuracy, 0)
    PWM_l = GPIO.PWM(LED_accuracy, 100000)

    # Setup debouncing and callbacks
    GPIO.add_event_detect(btn_submit,GPIO.FALLING,callback=btn_guess_pressed,bouncetime=500)
    GPIO.add_event_detect(btn_increase,GPIO.FALLING,callback=btn_increase_pressed,bouncetime=200)

    pass


# Load high scores
def fetch_scores():
    # get however many scores there are
    score_count = eeprom.read_byte(0)
    # Get the scores
    scores = []
    for i in range(score_count):
        x = eeprom.read_block((i+1)*10,16)
        name = ""
        for k in range(15):
            if (x[k]!=0):
                name += chr(x[k])
            else:
                break
        score = x[15]
        scores.append([name,score])
    # convert the codes back to ascii
    
    # return back the results
    return score_count, scores


# Save high scores
def save_scores():
    global address
    global eeprom
    global score
    name = input("Please enter your name")
    new_scores = [name,score]
    score_count, scores = fetch_scores()
    score_count += 1
    eeprom.write_block(0,[score_count])
    scores.append(new_scores)
    scores.sort(key=lambda x: x[1])
    for i, high_scores in enumerate(scores):
        data_to_write = []
        for letter in high_scores[0]:
            data_to_write.append(ord(letter))
        while (len(data_to_write)<15):
            data_to_write.append(0)
        while (len(data_to_write)>15):
            data_to_write.pop()
        data_to_write.append(high_scores[1])
        eeprom.write_block((i+1)*10,data_to_write,4)

    # fetch scores
    # include new score
    # sort
    # update total amount of scores
    # write new scores


# Generate guess number
def generate_number():
    return random.randint(0, pow(2, 3)-1)


# Increase button pressed
def btn_increase_pressed(channel):
    global numberOfGuess
    clearLeds()
    numberOfGuess += 1
    guess = numberOfGuess
    if (guess == 8):
        numberOfGuess = 0
        return
    if (guess % 2 == 1):
        guess -= 1
        GPIO.output(LED_value[0],1)
    if (guess % 2 == 0 and guess % 4 != 0):
        guess -= 2
        GPIO.output(LED_value[1],1)
    if (guess % 4 == 0 and guess != 0):
        GPIO.output(LED_value[2],1)

def clearLeds():
    for i in range(3):
        GPIO.output(LED_value[i],0)

# Guess button
def btn_guess_pressed(channel):
    global numberOfGuess
    global end_of_game
    global PWM_l
    global PWM_b
    global value
    global score
    start = time.time()
    while (GPIO.input(btn_submit)==GPIO.LOW):
        time.sleep(0.2)
    end = time.time() - start
    if (end > 1):
        clearLeds()
        numberOfGuess = 0
        PWM_l.stop()
        PWM_b.stop()
        score = 0
        end_of_game = True
        welcome()
        print("Select an option:   H - View High Scores     P - Play Game       Q - Quit")
    else:
        if (numberOfGuess == value):
            clearLeds()
            numberOfGuess = 0
            PWM_l.stop()
            PWM_b.start(0)
            PWM_b.stop()
            save_scores()
            end_of_game = True
        else:
            accuracy_leds()
            trigger_buzzer()
            score += 1

    

    # If they've pressed and held the button, clear up the GPIO and take them back to the menu screen
    # Compare the actual value with the user value displayed on the LEDs
    # Change the PWM LED
    # if it's close enough, adjust the buzzer
    # if it's an exact guess:
    # - Disable LEDs and Buzzer
    # - tell the user and prompt them for a name
    # - fetch all the scores
    # - add the new score
    # - sort the scores
    # - Store the scores back to the EEPROM, being sure to update the score count


def accuracy_leds():
    global PWM_l
    PWM_l.start(50)
    if (numberOfGuess == 0):
        PWM_l.ChangeDutyCycle(int(round(((8-value)/8)*100)))
    elif (value <= numberOfGuess):
        PWM_l.ChangeDutyCycle(int(round(((8-numberOfGuess)/(8-value))*100)))
    else:
        PWM_l.ChangeDutyCycle(int(round((numberOfGuess/value)*100)))

# Sound Buzzer
def trigger_buzzer(): #####also caters for the circular nature of the guess, if guess is 1 but number is 7, will show an absolute difference of 2
    global PWM_b
    global value
    global numberOfGuess
    PWM_b.start(50)
    if ((abs(value - numberOfGuess)==1) or abs(value-numberOfGuess)==7):
        PWM_b.ChangeFrequency(4)
    elif ((abs(value - numberOfGuess)==2) or abs(value - numberOfGuess)==6):
        PWM_b.ChangeFrequency(2)
    elif ((abs(value - numberOfGuess)==3) or abs(value - numberOfGuess)==5):
        PWM_b.ChangeFrequency(1) 
    else: ####for a 4 difference
        PWM_b.stop()


if __name__ == "__main__":
    try:
        # Call setup function
        setup()
        welcome()
        while True:
            menu()
    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()
       # eeprom.clear(2048)
