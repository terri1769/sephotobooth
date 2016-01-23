import Tkinter as tk
import tkMessageBox
import tkFont
import subprocess
import time
import picamera
import pytumblr
import config
import PythonMagick
import os
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
from email_validator import validate_email, EmailNotValidError
from PIL import Image, ImageTk
import logging
from logging.handlers import RotatingFileHandler
import RPi.GPIO as GPIO

# Set up variables
# First we set up the GPIO pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(8, GPIO.OUT)
GPIO.setup(18, GPIO.OUT)
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(25, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Then we set up some variables used throughout the app
email_address = tk.StringVar  # global to handle the email address to send ot
site_post = tk.IntVar  # global set by check box for whether or not to post to Tumblr
file_name = tk.StringVar  # global for the current working file name for the pic just taken. May not need
file_list = []  # global for the list of pic files for this sequence.
edited_file_name = tk.StringVar  # global to hold the file name of the final edited pic file that will be delivered
status = "online"  # online, offline or maintenance
LOG_FILENAME = config.pics_folder + 'log.log'  # Like, the log file, man.

# Set up a specific logger with our desired output level
log = logging.getLogger('log')
log.setLevel(logging.WARNING)

# Add the log message handler to the logger
handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=10000000, backupCount=5, )
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)
log.addHandler(logging.StreamHandler())


def set_status(channel):
    '''Reads GPIO pins 23 and 24 which are hooked up to a 3 position key switch.
    This lets us put the app in online, offline, or maintenance mode'''
    global status
    log.debug("23 = " + str(GPIO.input(23)))
    log.debug("24 = " + str(GPIO.input(24)))
    if (GPIO.input(23) == 0) and (GPIO.input(24) == 1):
        status = "online"
        log.debug("Status = " + status)
        main()
    elif (GPIO.input(24) == 0) and (GPIO.input(23) == 1):
        status = "offline"
        log.debug("Status = " + status)
        main()
    elif (GPIO.input(23) == 1) and (GPIO.input(24) == 1):
        status = "maintenance"
        log.debug("Status = " + status)
    else:
        log.error(
            "How the hell did we get to this status?")  # Only way we ever get here is if the key switch breaks physically.


def on_exit():
    """When you click the "X" in the top right corner of the window,to exit, this function is called.
    This is to break the user's ability to close the window."""
    log.warning("Close X clicked. Requested not to do that")
    tkMessageBox.showwarning("STOP!", "Please don't do that.")


def submit_callback():
    """Submit button functionality.  Gets data then closes window and keyboard"""
    global email_address
    global site_post
    bad_flag = False  # Used to signal invalid email address
    email_address = E1.get()  # Contains email address (list) as entered by user
    site_post = CheckVar1.get()  # Shows whether or not the option to post to Tumblr was checked
    log.info("Submit button pressed")
    log.debug("email address = " + email_address)
    log.debug("Post to site = " + str(site_post))

    # First check to see if we have anyplace at all to send/post the pics
    if email_address == "" and site_post == 0:
        log.warning("No email and Tumblr not selected")
        tkMessageBox.showwarning("Post or email?", "Please enter an email address or choose to post to Tumblr.")
    # Then break out the individual email addresses if there is more than one
    elif email_address != "":
        addresses = email_address.split(";")
        # Loop through the individual email addresses for validation
        for address in addresses:
            if address != "":
                log.debug("Single address: " + address)
                val_state = val_email(address)  # Call the email address validation routine
                log.debug("Validation state: " + str(val_state))
                # If the email address is found to be invalid, post an error
                if val_state[0] == False:
                    tkMessageBox.showwarning(address, val_state[1])
                    log.warning(val_state[1])
                    bad_flag = True
        # All entered email addresses were valid
        if not bad_flag:
            log.info("no bad addresses found")
            # Remove the keyboard and dialogs from the screen
            kbd.kill()
            root.destroy()
            return email_address, site_post  # Not really used.  Maybe in the future
    # If we got here, no email address was entered but we did select to post to Tumblr
    else:

        kbd.kill()
        root.destroy()
        return email_address, site_post  # Not really used.  Maybe in the future


def clearcallback():
    """Clear button was clicked.  Clear the text entry field"""
    E1.delete(0, 'end')
    log.info("Clear button pressed")


def start_pics_callback():
    """Start the picture taking sequence"""
    log.info('Starting pic taking sequence')
    GPIO.output(18, GPIO.LOW)  # turn on lights
    global root
    root.destroy()  # get rid of the GUI window so we can show the preview image
    global file_name  # Will hold the file name for each pic as it's taken and named
    global file_list  # Will hold the list of all files names for the pics taken in this session
    # Set up camera
    with picamera.PiCamera() as camera:
        camera.resolution = (1280, 720)
        camera.start_preview()
        camera.exif_tags['IFD0.Copyright'] = config.exif_copyright
        camera.exif_tags['IFD0.Artist'] = config.exif_artist
        camera.exif_tags['EXIF.UserComment'] = '        ' + config.event_name
        time.sleep(config.time_before)  # Time to wait before taking first pic.  Posing time
        i = 1
        # Actually take the pics.  Number of pics to be taken defined in config.py
        while i <= config.num_pics:
            file_name = (time.strftime("%Y%m%d-%H%M%S") + ".jpg")  # Name each file based on exact time and date
            camera.capture(config.pics_folder + file_name)
            log.debug('Captured image= ' + file_name)
            file_list.append(file_name);  # Add the taken pic's name to the file list for the current session
            log.debug(
                "file list= " + str(file_list))  # this is the file list to be delivered to the editor for processing
            time.sleep(config.time_between)  # Time to wait between pics.  Posing time
            i += 1
        camera.stop_preview()
        GPIO.output(18, GPIO.HIGH)  # Turn off lights
        log.debug("Camera preview stopped")
        # Present a screen that says "Processing..." While the pics are edited together
        bob = tk.Tk()  # Don't ask me why I used bob here instead of root like everywhere else.
        bob.geometry("800x480+0+0")
        bob.title('SE Photo Booth')
        bob.resizable(0, 0)  # Stop user from resizing
        bob.customFont = tkFont.Font(family="Helvetica", size=30)
        label = tk.Label(bob, text="Processing...", font=bob.customFont)
        label.pack(side="bottom", fill="both", expand="yes")
        bob.after((300), edit_pics)
        bob.after((config.processing_time * 1000), lambda: bob.destroy())
        bob.mainloop()


def yes_callback():
    """Yes button was clicked on dialog asking if you want to do it again.  We'll just skip asking for email and
    Tumblr permission and proceed right on to taking the pics."""
    global file_name
    global file_list
    global edited_file_name
    file_name = ""
    file_list = []
    edited_file_name = ""
    start_pics_callback()
    post_and_show()
    do_it_again_loop()


def okay_callback():
    """Okay button callback routine.  Called by okay button on the offline warning screen.
    Just closes that screen"""
    log.info('Okay button clicked on offline warning screen')
    root.destroy()


def cancel_callback():
    """Cancel session and start over.
    May be called from offline warning screen or start pics screen"""
    global cancelled
    log.info("Cancel button pressed")
    root.destroy()
    cancelled = 1  # Used as a marker elsewhere to skip the rest of the routines and return to the beginning.


def write_to_file():
    """Write the list of file names for this session to a file along with the email address and post to site status.
    This will be useful when identifying images later.
    Also necessary for processing when pics were taken while offline
    Note that last file name is the edited (montage) pic"""
    log.info('Writing to file')
    global file_list
    file = open(config.pics_folder + "pic_notes.txt", 'a')
    file.write(str(file_list) + "," + str(email_address) + "," + str(site_post))
    file.write("\n")
    file.close()


def edit_pics():
    """Edit the taken pics together into a single image montage"""
    global edited_file_name
    working_files = []
    for file in file_list:  # go through the list of files for this round
        working_files.append(os.path.join(config.pics_folder, file))
        log.debug("Working files" + str(working_files))
    edited_file_name = file_name
    log.info("edit pics routine")
    edited_file_name = (time.strftime("%Y%m%d-%H%M%S") + ".jpg")
    log.debug("Edited file name" + edited_file_name)
    montage_cmd = ['montage']  # Montage is the command for PythonMagick to squish all of the pics into one
    montage_cmd.extend(working_files)
    montage_cmd.extend(['-tile', config.edit_layout, '-background', 'none', '-geometry', '+0+0', 'jpg:-'])
    # Run the command through the OS to montage the pics.  Resulting pic is piped to stdout and stderr to hold it in
    # memory while we continue resizing it
    p = subprocess.Popen(montage_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    img = PythonMagick.Image(PythonMagick.Blob(stdout))
    geometry = PythonMagick.Geometry(config.layout_width, config.layout_height)
    geometry.aspect(True)
    img.scale(geometry)
    img.write(config.pics_folder + edited_file_name)
    file_list.append(edited_file_name)
    write_to_file()


def send_email():
    """Send email with attachment to specified address(es).
    All we're sending id the final edited (montaged) pic"""

    log.info("sending email to: " + email_address)

    msg = MIMEMultipart()
    msg['From'] = config.gmail_user
    msg['To'] = email_address
    msg['Subject'] = config.email_subject

    msg.attach(MIMEText(config.email_text))
    attach = (config.pics_folder + str(edited_file_name))
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(open(attach, 'rb').read())
    Encoders.encode_base64(part)
    part.add_header('Content-Disposition',
                    'attachment; filename="%s"' % os.path.basename(attach))
    msg.attach(part)

    mailServer = smtplib.SMTP("smtp.gmail.com", 587)
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.ehlo()
    mailServer.login(config.gmail_user, config.gmail_pwd)
    mailServer.sendmail(config.gmail_user, email_address, msg.as_string())
    mailServer.close()


def post_to_site():
    """create a photo post to Tumblr using the local file"""
    log.info("post to site called")
    client = pytumblr.TumblrRestClient(
            config.consumer_key,
            config.consumer_secret,
            config.oauth_token,
            config.oauth_secret, )

    # Creates a photo post using a local file path to saved montaged photo
    client.create_photo(config.tumblr_blog, state="published", tags=config.blog_tag, caption=config.event_name,
                        data=config.pics_folder + edited_file_name)
    log.debug("post to site= " + edited_file_name)


def val_email(email):
    """Validate email address"""
    log.info("validating email address")
    try:
        if status == "online":
            v = validate_email(email,
                               check_deliverability=True)  # validate and get info.  Since we're online, check deliverability
        elif status == "offline":
            v = validate_email(email, check_deliverability=False)  # validate and get info
        email = v["email"]  # replace with normalized form
        return True, email
    except EmailNotValidError as e:
        # email is not valid, exception message is human-readable
        log.warning(str(e))
        return False, (str(e))


def main():
    """Main part of the routine where we set up the first data collection windows"""
    try:
        log.info('Starting main loop')
        global cancelled
        cancelled = 0
        # Set up root tkinter window
        global root
        root = tk.Tk()
        root.geometry("800x160+0+0")
        root.title('SE Photo Booth')
        root.resizable(0, 0)  # Stop user from resizing
        root.customFont = tkFont.Font(family="Helvetica", size=20)  # Enlarge font on all widgets for visibility

        # Initialize keyboard
        cmd = '/usr/local/bin/matchbox-keyboard -g 310x800.190.0'
        global kbd
        kbd = subprocess.Popen(cmd.split())

        # Create window label (requesting email address)
        label_text = tk.Label(root, text="Please enter email address.", font=root.customFont)
        label_text.pack()
        label_text2 = tk.Label(root, text="separate multiple addresses with a semicolon ( ; )", font=root.customFont)
        label_text2.pack()

        # Create and initialize text entry window for email address
        global E1
        E1 = tk.Entry(root, bd=5, width=700, exportselection=0, takefocus=1, font=root.customFont)
        E1.pack()
        E1.focus_set()
        E1.focus()

        # Create and initialize checkbox for posting to Tumblr
        global C1
        global CheckVar1
        CheckVar1 = tk.IntVar()
        C1 = tk.Checkbutton(root, text="Post to Tumblr site?", variable=CheckVar1, onvalue=1, offvalue=0, height=2,
                            width=20, takefocus=0, font=root.customFont, )
        C1.select()
        C1.pack(side=tk.LEFT)

        # Submit button
        submit_button = tk.Button(root, text="Submit", command=submit_callback, font=root.customFont)
        submit_button.pack(side=tk.LEFT)

        # Clear button
        clear_button = tk.Button(root, text="Clear", command=clearcallback, font=root.customFont)
        clear_button.pack(side=tk.LEFT)

        # Keep user from being able to minimize window
        root.wm_protocol("WM_DELETE_WINDOW", on_exit)
        root.bind("<Unmap>", lambda e: root.deiconify())

        # End of main loop for initial window and keyboard
        if status == "maintenance":
            log.debug("Maintenance mode activated")
            kbd.kill()
            root.kill
        root.mainloop()
        kbd.kill()  # Remove keyboard from screen
        log.debug("out of mainloop")

        if status == "offline":
            offline_warning_page()

        # Set up new root window.  This one will be to display all of the screens around taking the pics
        if cancelled == 0:
            start_pics_page()
        if cancelled == 0:
            post_and_show()
        if cancelled == 0:
            do_it_again_loop()

    except KeyboardInterrupt:  # This allows us to stop the app with ctrl + c while running in a console.  Debugging only
        log.exception('Exception: ')
        exit()
    except:
        log.exception('Exception: ')
        # GPIO.cleanup()
        # exit()


def offline_warning_page():
    """Put up a page warning the user there is no internet access and pic will be sent/posted later.
    Give them an option to cancel"""
    log.info("Offline warning page")
    # Set up and show window with warning about lack of internet access
    global root
    root = tk.Tk()
    root.geometry("800x480+0+0")
    root.title('SE Photo Booth')
    root.resizable(0, 0)  # Stop user from resizing
    root.customFont = tkFont.Font(family="Helvetica", size=30)
    label_text2 = tk.Label(root, text="There is currently no internet access.", font=root.customFont)
    label_text3 = tk.Label(root, text="Pic will be posted / sent later", font=root.customFont)
    label_text2.pack()
    label_text3.pack()
    start_button = tk.Button(root, text="Okay", command=okay_callback, font=root.customFont)
    cancel_button = tk.Button(root, text="Cancel", command=cancel_callback, font=root.customFont)
    start_button.pack()
    cancel_button.pack()
    root.mainloop()


def start_pics_page():
    """Page with notice of where pics will be sent / posted and a start button to initiate the pic taking"""
    global root
    root = tk.Tk()
    root.geometry("800x480+0+0")
    root.title('SE Photo Booth')
    root.resizable(0, 0)  # Stop user from resizing
    root.customFont = tkFont.Font(family="Helvetica", size=30)
    label_text2 = tk.Label(root, text="There will be a series of " + str(config.num_pics) + " pictures taken.",
                           font=root.customFont)
    label_text3 = tk.Label(root, text="Please press the button when ready to start!", font=root.customFont)
    label_text2.pack()
    label_text3.pack()
    if site_post == 1:
        label_text4 = tk.Label(root, text="Pictures will be posted to:", font=root.customFont)
        label_text4.pack()
        label_text5 = tk.Label(root, text=config.tumblr_url, font=root.customFont)
        label_text5.pack()
    if email_address != "":
        label_text6 = tk.Label(root, text="Pictures will be emailed to:", font=root.customFont)
        label_text7 = tk.Label(root, text=email_address, font=root.customFont)
        label_text6.pack()
        label_text7.pack()
    start_button = tk.Button(root, text="Start!", command=start_pics_callback, font=root.customFont)
    cancel_button = tk.Button(root, text="Cancel", command=cancel_callback, font=root.customFont)
    start_button.pack()
    cancel_button.pack()
    log.debug('Before leaving main loop')
    root.mainloop()
    log.debug("Out of second main loop")
    log.debug("cancelled status= " + str(cancelled))


def post_and_show():
    """Email and post the pics if online.  Also show the final edited pic to the user"""
    if len(email_address) >> 0 and status == "online":
        send_email()
    if int(site_post) == 1 and status == "online":
        post_to_site()
    global count
    count += 1  # Count the number of pic sessions.  Purely for curiosity
    log.info("Number of users since restart = " + str(count))
    log.debug('Starting show pic')
    path = config.pics_folder + edited_file_name  # Grab the final edited pic
    log.debug("edited pic file: " + config.pics_folder + edited_file_name)
    pil_image = Image.open(path)
    img = pil_image.resize((720, 480), Image.ANTIALIAS)  # Resize the pic to fit on our little display screen
    log.debug("Resized pic file: " + str(img))
    global root
    root = tk.Tk()
    root.title("Title")
    # convert PIL image objects to Tkinter PhotoImage objects
    tk_image2 = ImageTk.PhotoImage(img)
    # display the image on a label
    label2 = tk.Label(root, image=tk_image2)
    label2.pack(padx=5, pady=5)
    root.after((config.time_display * 1000), lambda: root.destroy())  # Remove the pic after n seconds
    log.debug('ending show pic loop')
    root.mainloop()


def do_it_again_loop():
    """Page asking if the user wants to do another session.
    This can save them having to type in the email address(es) again"""
    global root
    root = tk.Tk()
    root.geometry("800x480+0+0")
    root.title('SE Photo Booth')
    root.resizable(0, 0)  # Stop user from resizing
    root.customFont = tkFont.Font(family="Helvetica", size=30)
    label_text2 = tk.Label(root, text="", font=root.customFont)
    label_text3 = tk.Label(root, text="Do it again?", font=root.customFont)
    label_text2.pack()
    label_text3.pack()
    start_button = tk.Button(root, text="YES!", command=yes_callback, font=root.customFont)
    cancel_button = tk.Button(root, text="No", command=cancel_callback, font=root.customFont)
    root.after((config.again_display * 1000), lambda: root.destroy())
    start_button.pack()
    cancel_button.pack()
    root.mainloop()


# Initialize once before loop

log.info('started')
set_status(23)
GPIO.output(18, GPIO.HIGH)  # Turn off lights
GPIO.output(18, GPIO.HIGH)  # Turn on status LED.  We want this on as long as the program is running.
count = 0  # initialize counter for number of sessions from restart

# Set up interrupts based on hardware key switch.  Determines offline or online status and maintenance mode
GPIO.add_event_detect(23, GPIO.RISING, callback=set_status, bouncetime=300)
GPIO.add_event_detect(24, GPIO.RISING, callback=set_status, bouncetime=300)

# Set up a big loop so we can always return to start after processing
while status == "online" or status == "offline":
    log.debug("In online/offline loop")
    try:
        subprocess.call(['killall', 'lxpanel'])  # Kills the OS taskbar
        main()  # Run our main function.  Everything else is called from there or another function
    except KeyboardInterrupt:  # This allows us to stop the app with ctrl + c while running in a console.  Debugging only
        log.exception('Exception: ')
        GPIO.cleanup()  # Un-sets any GPIO pins we tinkered with
        exit()
    except:  # Capture the error to the log and keep on going
        log.exception('Exception: ')
        GPIO.cleanup()

else:
    while status == "maintenance":
        log.debug("In maintenance loop")
        try:
            subprocess.call(['lxpanel'])  # Start the OS taskbar that we killed in the online/offline loop

            """Here we'll set up the power button.
            It will only work while in maintenance mode to keep users from restarting OS."""
            # watch GPIO pin and determine time pressed and let up
            GPIO.wait_for_edge(25, GPIO.FALLING)
            pressed = time.time()
            log.debug(str(pressed))
            GPIO.wait_for_edge(25, GPIO.RISING)
            unpressed = time.time()
            log.debug(str(unpressed))
            log.debug(unpressed - pressed)
            # If pressed for more than 5 seconds, do a graceful shutdown
            if unpressed - pressed >= 5:
                log.info("Shutting down")
                os.system("sudo shutdown -h now")
                mainloop()
            # If pressed more than .5 seconds, reboot.  If less than .5, ignore
            elif unpressed - pressed >= .5:
                log.info("Rebooting")
                os.system("sudo reboot")
                mainloop()

        except KeyboardInterrupt:  # This allows us to stop the app with ctrl + c while running in a console.  Debugging only
            log.exception('Exception: ')
            GPIO.cleanup()
            exit()
        except:  # Capture the error to the log and keep on going
            log.exception('Exception: ')
            GPIO.cleanup()
