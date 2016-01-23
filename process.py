"""
This app is to post and send pics taken while the app was in offline mode
"""import pytumblr
import config
import smtplib
import os
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
import logging
from logging.handlers import RotatingFileHandler

LOG_FILENAME = config.pics_folder + 'processlog.log'

# Set up a specific logger with our desired output level
log = logging.getLogger('log')
log.setLevel(logging.INFO)

# Add the log message handler to the logger
handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=10000000, backupCount=5,)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)
log.addHandler(logging.StreamHandler())

def main():
    """Main routine to cycle through the list of pics, emails and post permissions, and actually send/post them."""
    file = config.pics_folder + "pic_notes.txt"
    with open(file, 'r') as f:
        lines = f.readlines()
        for i in range(0, len(lines)):
            line = lines[i].split(',')  # Take the line and split it into individual items
            pic_file = line[config.num_pics]
            edited_pic_file = pic_file[2:-2]
            email_address = line[config.num_pics+1]
            site_post = line[config.num_pics+2]
            log.debug("full line: " + str(line))
            log.debug("edited file name: " + edited_pic_file)
            log.debug('email address: ' + email_address)
            log.debug('site post bit: ' + site_post)
            if email_address != "":  # No blank email addresses!
                send_email(email_address, edited_pic_file)
            if int(site_post) >> 0:
                post_to_site(edited_pic_file)


def send_email(email_address, file_name):
    """Send email with attachment to specified address(es)"""
    log.info("sending email to: " + email_address)
    msg = MIMEMultipart()
    msg['From'] = config.gmail_user
    msg['To'] = email_address
    msg['Subject'] = config.email_subject

    msg.attach(MIMEText(config.email_text))
    attach = (config.pics_folder + file_name)
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


def post_to_site(pic_file):
    """create a photo post to Tumblr using the local file"""
    log.info("post to site called")
    client = pytumblr.TumblrRestClient(
    config.consumer_key,
    config.consumer_secret,
    config.oauth_token,
    config.oauth_secret,)
    client.create_photo(config.tumblr_blog, state="published", tags=config.blog_tag, caption=config.event_name, data=config.pics_folder + pic_file)
    log.debug("post to site= " + pic_file)

try:
    main()
except KeyboardInterrupt:  # This allows us to stop the app with ctrl + c while running in a console.  Debugging only
    log.exception('Exception: ')
    exit()
except:  # Capture the error to the log and keep on going
    log.exception('Exception: ')
