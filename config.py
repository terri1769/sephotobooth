# The first 4 below are from pytumblr and set up your Oauth session with tumblr.
consumer_key =
consumer_secret =
oauth_token =
oauth_secret =

# Stuff to email the pic to the user
gmail_user =
gmail_pwd =
email_subject = "pictures from testing 2016"
email_text = "Here's the requested pic from the photo booth!"

# Various other variables we may want to change
event_name = "testing 2016"  # Used in EXIF tags on unedited pics and as caption on Tumblr post
pics_folder = "/mnt/data/pics/test/"  # location of the folder to store the pictures
num_pics = 4  # /number of pics to take in a series before editing them together
time_before = 1  # Delay time for posing before the first shot (in seconds)
time_between = 1  # Delay time for posing between each successive shot (in seconds)
time_display = 5  # How long the final edited pic will stay on the screen before cycle restarts (in seconds)
again_display = 5 # How long the page asking if they want to do it again stays up before cancelling and starting over.
tumblr_url = "sephotobooth.tumblr.com" # To show the user where the pic will be posted
tumblr_blog = "sephotobooth"  # Part of the URL that's put together to post
blog_tag = ["testing", "photobooth"]  # Tags for Tumblr post
exif_copyright = 'Copyright (c) 2016'  # EXIF copyright only stored in unedited pics
exif_artist = "SE Photo Booth"  # EXIF artist only stored in unedited pics
processing_time = 3  # How long to show the "Processing..." page, in seconds

#  Variables to set up the montage (the edited final pic)
edit_layout = '2x2'
layout_width = 900
layout_height = 600

