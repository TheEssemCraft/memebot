import praw
import json
import requests
import tweepy
import time
import os
import csv
import configparser
import urllib.parse
import sys
from glob import glob
from gfycat.client import GfycatClient
import distutils.core
import itertools
import photohash

# Location of the configuration file
CONFIG_FILE = 'config.ini'

def strip_title(title):
	if len(title) < 94:
		return title
	else:
		return title[:93] + '...'

def save_file(img_url, file_path):
	resp = requests.get(img_url, stream=True)
	if resp.status_code == 200:
		with open(file_path, 'wb') as image_file:
			for chunk in resp:
				image_file.write(chunk)
		# Return the path of the image, which is always the same since we just overwrite images
		return file_path
	else:
		print('[BOT] File failed to download. Status code: ' + resp.status_code)
		return ''

def get_media(img_url, post_id):
	if any(s in img_url for s in ('i.imgur.com', 'i.redd.it', 'i.reddituploads.com')):
		# This adds support for all imgur links (including galleries), but I need to make a new regex
		#if ('i.imgur.com' not in img_url) and ('imgur.com' in img_url):
			#print('[bot] Attempting to retrieve image URL for', img_url, 'from imgur...')
			#regex = r"(https?:\/\/imgur\.com\/a\/(.*?)(?:\/.*|$))"
			#m = re.search(regex, img_url, flags=0)
			#print(m.group(0))
			#img_url = imgur.get_image(img_url)
		file_name = os.path.basename(urllib.parse.urlsplit(img_url).path)
		file_extension = os.path.splitext(img_url)[-1].lower();
		# Fix for issue with i.reddituploads.com links not having a file extension in the URL
		if not file_extension:
			file_extension += '.jpg'
			file_name += '.jpg'
			img_url += '.jpg'
		file_path = IMAGE_DIR + '/' + file_name
		print('[BOT] Downloading file at URL ' + img_url + ' to ' + file_path + ', file type identified as ' + file_extension)
		if ('gifv' not in img_url): # Can't process GIFV links until Imgur API integration is working
			img = save_file(img_url, file_path)
			return img
		else:
			print('[BOT] GIFV files are not supported yet')
			return ''
	elif ('gfycat.com' in img_url): # Gfycat
		# Twitter supports uploading videos, but Tweepy hasn't updated to support it yet.
		gfycat_name = os.path.basename(urllib.parse.urlsplit(img_url).path)
		client = GfycatClient()
		gfycat_info = client.query_gfy(gfycat_name)
		gfycat_url = gfycat_info['gfyItem']['mp4Url']
		file_path = IMAGE_DIR + '/' + gfycat_name + '.mp4'
		print('[BOT] Downloading Gfycat at URL ' + gfycat_url + ' to ' + file_path)
		gfycat_file = save_file(gfycat_url, file_path)
		return gfycat_file
	else:
		print('[BOT] Post', post_id, 'doesn\'t point to an image/video:', img_url)
		return ''

def tweet_creator(subreddit_info):
	post_dict = {}
	print ('[BOT] Getting posts from Reddit')
	for submission in subreddit_info.hot(limit=20):
		# If the OP has deleted his account, save it as "a deleted user"
		if submission.author is None:
			submission.author = "a deleted user"
			submission.author.name = "a deleted user"
		else:
			submission.author.name = "/u/" + submission.author.name
		post_dict[strip_title(submission.title)] = [submission.id,submission.url,submission.shortlink,submission.author.name]
	return post_dict

def setup_connection_reddit(subreddit):
	print ('[BOT] Setting up connection with Reddit')
	r = praw.Reddit(
		user_agent='bot irl',
		client_id=REDDIT_AGENT,
		client_secret=REDDIT_CLIENT_SECRET)
	return r.subreddit(subreddit)

def duplicate_check(id):
	value = False
	with open(CACHE_CSV, 'rt', newline='') as f:
		reader = csv.reader(f, delimiter=',')
		for row in reader:
			if id in row:
				value = True
	return value
	
def hash_check(hash):
	value = False
	# Only extract last three lines from cache file
	post_list = []
	with open(CACHE_CSV, 'rt', newline='') as f:
		for line in f:
			post_list.append(line)
			if len(post_list) > REPOST_LIMIT:
				post_list.pop(0)
		if any(hash in s for s in post_list):
			value = True
	return value

def log_post(id, hash):
	with open(CACHE_CSV, 'a', newline='') as cache:
			date = time.strftime("%d/%m/%Y") + ' ' + time.strftime("%H:%M:%S")
			wr = csv.writer(cache, delimiter=',')
			wr.writerow([id, date, hash])

def main():
	# Make sure logging file and media directory exists
	if not os.path.exists(CACHE_CSV):
		with open(CACHE_CSV, 'w', newline='') as cache:
			default = ['Post','Date and time','Image hash']
			wr = csv.writer(cache)
			wr.writerow(default)
		print ('[BOT] ' + CACHE_CSV + ' file not found, created a new one')
	if not os.path.exists(IMAGE_DIR):
		os.makedirs(IMAGE_DIR)
		print ('[BOT] ' + IMAGE_DIR + ' folder not found, created a new one')
	# Continue with script
	subreddit = setup_connection_reddit(SUBREDDIT_TO_MONITOR)
	post_dict = tweet_creator(subreddit)
	tweeter(post_dict)

def alt_tweeter(post_link, op):
	# Make sure alt account works
	auth = tweepy.OAuthHandler(ALT_CONSUMER_KEY, ALT_CONSUMER_SECRET)
	auth.set_access_token(ALT_ACCESS_TOKEN, ALT_ACCESS_TOKEN_SECRET)
	api = tweepy.API(auth)

	try:
		# There's probably a better way to do this, but it works
		latestTweets = api.user_timeline(screen_name = TWITTER_ACCOUNT_NAME, count = 1, include_rts = False)
		newestTweet = latestTweets[0].id
	except BaseException as e:
		print ('[BOT] Error while posting tweet on alt account:', str(e))	
		return

	# Compose the tweet
	tweetText = '@' + TWITTER_ACCOUNT_NAME + ' Originally posted by ' + op + '. ' + post_link
	print('[BOT] Posting this on alt Twitter account:', tweetText)
	api.update_status(tweetText, newestTweet)

def tweeter(post_dict):
	auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_secret)
	api = tweepy.API(auth)
	for post in post_dict:
		# Grab post details from dictionary
		post_id = post_dict[post][0]
		if not duplicate_check(post_id): # Make sure post is not a duplicate
			file_path = get_media(post_dict[post][1], post_dict[post][0])
			post_link = post_dict[post][2]
			post_op = post_dict[post][3]
			# Make sure the post contains media (if it doesn't, then file_path would be blank)
			if (file_path):
				# Scan the image against previously-posted images, but only if repost protection is enabled in config.ini
				hash = photohash.average_hash(file_path)
				print ('[BOT] Image hash check:', hash_check(hash))
				if (REPOST_PROTECTION is True and hash_check(hash) is True):
					print ('[BOT] Skipping', post_id, 'because it seems to be a repost')
				else:
					print ('[BOT] Posting this on main twitter account:', post, file_path)
					log_post(post_id, hash)
					try:
						api.update_with_media(filename=file_path, status=post)
						alt_tweeter(post_link, post_op)
						print('[BOT] Sleeping for', DELAY_BETWEEN_TWEETS, 'seconds')
						time.sleep(DELAY_BETWEEN_TWEETS)
					except BaseException as e:
						print ('[BOT] Error while posting tweet:', str(e))
			else:
				print ('[BOT] Ignoring', post_id, 'because there was not a media file downloaded')
			# Cleanup image file
			if (file_path) is not None:
				if (os.path.isfile(file_path)):
					os.remove(file_path)
					print ('[BOT] Deleted media file at ' + file_path)
		else:
				print ('[BOT] Ignoring', post_id, 'because it was already posted')

if __name__ == '__main__':
	# Make sure config file exists
	try:
		config = configparser.ConfigParser()
		config.read(CONFIG_FILE)
	except BaseException as e:
		print ('[BOT] Error while reading config file:', str(e))
		sys.exit()
	# Create variables from config file
	CACHE_CSV = config['BotSettings']['CacheFile']
	TWITTER_ACCOUNT_NAME = config['BotSettings']['TwitterUsername']
	IMAGE_DIR = config['BotSettings']['MediaFolder']
	DELAY_BETWEEN_TWEETS = int(config['BotSettings']['DelayBetweenTweets'])
	SUBREDDIT_TO_MONITOR = config['BotSettings']['SubredditToMonitor']
	REPOST_PROTECTION = bool(distutils.util.strtobool(config['RepostSettings']['RepostProtection']))
	REPOST_LIMIT = int(config['RepostSettings']['RepostLimit'])
	ACCESS_TOKEN = config['PrimaryTwitterKeys']['AccessToken']
	ACCESS_TOKEN_secret = config['PrimaryTwitterKeys']['AccessTokenSecret']
	CONSUMER_KEY = config['PrimaryTwitterKeys']['ConsumerKey']
	CONSUMER_SECRET = config['PrimaryTwitterKeys']['ConsumerSecret']
	ALT_ACCESS_TOKEN = config['AltTwitterKeys']['AccessToken']
	ALT_ACCESS_TOKEN_SECRET = config['AltTwitterKeys']['AccessTokenSecret']
	ALT_CONSUMER_KEY = config['AltTwitterKeys']['ConsumerKey']
	ALT_CONSUMER_SECRET = config['AltTwitterKeys']['ConsumerSecret']
	REDDIT_AGENT = config['Reddit']['Agent']
	REDDIT_CLIENT_SECRET = config['Reddit']['ClientSecret']
	# Run the main script
	while True:
		main()
		print('[BOT] Sleeping for', DELAY_BETWEEN_TWEETS, 'seconds')
		time.sleep(DELAY_BETWEEN_TWEETS)
		print('[BOT] Restarting main()...')