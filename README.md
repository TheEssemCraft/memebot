# Meme Bot

This is a Python bot that looks up images from a specified subreddit and automatically posts them on Twitter. It is based on [reddit-twitter-bot](https://github.com/rhiever/reddit-twitter-bot). Memebot was created for the [@ItMeIRL](https://twitter.com/ItMeIRL), [@ItsMeowIRL](https://twitter.com/ItsMeowIRL), and [@PrequelMemesBot](https://twitter.com/PrequelMemesBot) Twitter accounts.

## Disclaimer

I hold no liability for what you do with this script or what happens to you by using this script. Abusing this script *can* get you banned from Twitter, so make sure to read up on proper usage of the Twitter API.

## Dependencies

First, you will need to install Python 3 on your system. After that, you will also need to install the [tweepy](https://github.com/tweepy/tweepy), [PRAW](https://praw.readthedocs.org/en/), [py-gfycat](https://github.com/ankeshanand/py-gfycat), and [PhotoHash](https://github.com/bunchesofdonald/photohash) libraries. You can do so by running these commands:

    pip3 install tweepy
    pip3 install praw
    pip3 install gfycat
    pip3 install PhotoHash

## Setting up the bot

All settings for the bot can be found in the `config.ini` file. Open the file in any text editor and add the following info:

1. Under the [BotSettings] section, add the name of the subreddit to `SubredditToMonitor` (do not include the /r/)
2. By default, the bot will wait at least 600 seconds between tweets to prevent spamming, you can change this by editing the `DelayBetweenTweets` setting in the [BotSettings] section
3. By default, the bot's Repost Protection feature is enabled. Read the below 'Repost options' section to learn more.

Next, you'll need to give Meme Bot access to a Twitter account, and add the required information to the config file.

1. [Sign in](https://dev.twitter.com/apps) with the Twitter account you want to use with the bot
2. Click the 'Create New App' button
3. Fill out the Name, Description, and Website fields with anything you want (you can leave the callback field blank)
4. Make sure that 'Access level' says 'Read and write'
5. Click the 'Keys and Access Tokens' tab
6. Click the 'Create my access token' button
7. Fill out the [PrimaryTwitterKeys] section in the config file with the info

You can also optionally use another Twitter account to reply to every tweet with the original source on Reddit ([example](https://twitter.com/IRL_Context/status/846069261474938880)). The bot will work fine if you skip this step.

1. [Sign in](https://dev.twitter.com/apps) with the Twitter account you want to use with the bot
2. Click the 'Create New App' button
3. Fill out the Name, Description, and Website fields with anything you want (you can leave the callback field blank)
4. Make sure that 'Access level' says 'Read and write'
5. Click the 'Keys and Access Tokens' tab
6. Click the 'Create my access token' button
7. Fill out the [AltTwitterKeys] section in the config file with the info

In addition, you will have to create an application on Reddit:

1. Sign in with your Reddit account
2. Go to your [app preferences](https://www.reddit.com/prefs/apps) and create a new application at the bottom
3. Select the application type as 'script'
4. Add the token (seen below the name of the bot after it's generated) and the secret to the [Reddit] section of the config file

## Repost options

Memebot 2.2 introduced a new 'Repost Protection' feature. This uses the [PhotoHash library](https://github.com/bunchesofdonald/photohash) to store a hash of every image the bot posts. When enabled, Repost Protection keeps the bot from posting the same images over and over again in a row.

There are two options you can change in `config.ini`, in the `[RepostSettings]` section. The first option, `RepostProtection`, will turn the feature on or off (true is on, false is off).

The second option, `RepostLimit`, determines how many previous posts the bot will check. For example, if this is set to 3, the bot will check the previous three images it has tweeted. If one of those images matches the image about to be tweeted, the tweet is canceled.

The image checking algorithm uses a fuzzy logic, so images that are similar will still be posted. For example, different text on the same meme template would not be identifed as reposts.

## Usage

Once you edit the bot script to provide the necessary API keys and the subreddit you want to tweet from, you can run the bot on the command line:

    python memebot.py
