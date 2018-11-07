import scrapy
from scrapy.crawler import CrawlerProcess
from twisted.internet import reactor
import scrapy
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging


import json
from collections import defaultdict
with open('longListHarryPotterCharacters.json') as f:
    jsonCharacters = json.load(f)["characters"]
    characters = defaultdict(list)
    for character in jsonCharacters:  
        for name in jsonCharacters[character]:
            characters[character].append(name.lower())

import re
from datetime import datetime
from datetime import timedelta
from dateutil import parser

def isUserLink(href):
    m = re.match('/u/\d+/\w+', href)
    if(m is None):
        return False
    return True
def extractUserLink(href):
    m = re.match('.*(?P<link>/u/\d+(/\d+)?/.*)', href)
    if(m is None):
        return ""
    return m.group('link')
def isStoryLink(href):
    m = re.match('.*(?P<link>/s/\d+(/\d+)?/.*)', href)
    if(m is None):
        return False
    return True
def extractStoryLink(href):
    m = re.match('.*(?P<link>/s/\d+(/\d+)?/.*)', href)
    if(m is None):
        return ""
    return m.group('link')
def isReviewLink(href):
    m = re.match('/r/\d+', href)
    if(m is None):
        return False
    return True
def convertDate(strDate):
    now = datetime.now()
    mSeconds = re.match('(?P<seconds>\d+)s', strDate)
    mMinutes = re.match('(?P<minutes>\d+)m', strDate)
    mHours = re.match('(?P<hours>\d+)h', strDate)
    
    mDate = re.match('(?P<month>\w{3}) (?P<day>\d+)(, (?P<year>\d{4}))?', strDate)
    delta = timedelta(0)
    if(mSeconds is not None):
        delta = timedelta(0,int(mSeconds.group('seconds')))
    if(mMinutes is not None):
        delta = timedelta(minutes = int(mMinutes.group('minutes')))  
    if(mHours is not None):
        delta = timedelta(hours = int(mHours.group('hours'))) 
    if(mDate is not None):
        return parser.parseStory(strDate)
    return now + delta

def getOtherInfoAsJson(other_stuff):
    language = ''
    genre = ''
    favorites = 0
    follows = 0
    reviews = 0
    words = -1
    chapters = 1
    language_genre_match = re.search(
            '(?P<language>\w+) - ((?P<genre1>\w+)/(?P<genre2>\w+))', 
            other_stuff)
    if(language_genre_match is not None):
        language = language_genre_match.group('language')
        genre = [language_genre_match.group('genre1'), language_genre_match.group('genre2')]
    
    mReviews = re.search(
            'Reviews: <a.*>(?P<reviews>\d+)</a>', 
            other_stuff)
    if(mReviews is not None):
        reviews = mReviews.group('reviews')
        
    mWords = re.search(
            'Words: (?P<words>(\d+,?)+)', 
            other_stuff)
    if(mWords is not None):
        words = mWords.group('words')
    
    mChapters = re.search(
            'Chapters: (?P<chapters>(\d+,?)+)', 
            other_stuff)
    if(mChapters is not None):
        chapters = mChapters.group('chapters')
    
    mFavorites = re.search(
            'Favs: (?P<favorites>\d+)', 
            other_stuff)
    if(mFavorites is not None):
        favorites = mFavorites.group('favorites')

    mFollows = re.search(
            'Follows: (?P<follows>\d+)', 
            other_stuff)
    if(mFollows is not None):
        follows = mFollows.group('follows')
        
    return {
                'language':language,
                'genre': genre,
                'favorites': favorites,
                'follows': follows,
                'reviews': reviews,
                'words': words,
                'chapters': chapters
           }
import logging
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import string
sid = SentimentIntensityAnalyzer()

class FanFicSpider(scrapy.Spider):
    name = "fanFic"
    start_urls = [
        'https://www.fanfiction.net/book/Harry-Potter/?&srt=4&r=103'
        #'https://www.fanfiction.net/s/13025005/1/A-Twist-In-Time'
        #'https://www.fanfiction.net/u/4805578/vandenburgs'
        #'https://www.fanfiction.net/s/13090372/1/This-Labyrinth-of-Suffering'
        #'https://www.fanfiction.net/s/13059900/1/La-For%C3%AAt-des-%C3%82mes-Bris%C3%A9es',
        #'https://www.fanfiction.net/r/8636004/'
    ]
    custom_settings = {
        'LOG_LEVEL': logging.INFO,
        'CONCURRENT_REQUESTS' : 100,
        'COOKIES_ENABLED' : False,
        'DEPTH_PRIORITY' : 1,
        'SCHEDULER_DISK_QUEUE' : 'scrapy.squeue.PickleFifoDiskQueue',
        'SCHEDULER_MEMORY_QUEUE' : 'scrapy.squeue.FifoMemoryQueue',
    }
    
    def parse(self, response):
        nextLinks = {}
        for elem in response.xpath('//a[@class="stitle"]').xpath(".//@href"):
            nextLinks[elem.extract()] = self.parseStory
        for link, func in nextLinks.items():
            yield response.follow(link, callback=func)

    def parseUserPage(self, response):
        profile_top = response.xpath('//div[@id="content_wrapper_inner"]')
        nextLinks = {}
        #follow links to their stories and reviews
        for elem in response.xpath('//div[@class="z-list mystories"]').xpath(".//@href"):
            if(isStoryLink(elem.extract())):
                nextLinks[elem.extract()] = self.parseStory
            if(isReviewLink(elem.extract())):
                nextLinks[elem.extract()] = self.parseReview
        
        #get the favorites
        favorites = []
        for elem in response.xpath('//div[@class="z-list favstories"]'):
            favStory = ''
            favAuthor = ''
            for link in elem.xpath('./a//@href').extract():
                if(isUserLink(link)):
                    favAuthor = link
                    nextLinks[link] = self.parseUserPage
                elif(isStoryLink(link)):
                    favStory = link
                    nextLinks[link] = self.parseStory
                elif(isReviewLink(link)):
                    nextLinks[link] = self.parseReview
            favorites.append({
                'favStory' : favStory,
                'favAuthor': favAuthor
            })
        
        userName = response.xpath('//link[@rel="canonical"]//@href').extract_first()
        userName = extractUserLink(userName)
        yield {
            'pageType': 'user',
            'name': userName,
            'favorites': favorites
        }
        
        for link, func in nextLinks.items():
            yield response.follow(link, callback=func)
        
    def parseStory(self, response):
        nextLinks = {}
        profile_top = response.xpath('//div[@id="profile_top"]')
        storyName = response.xpath('//link[@rel="canonical"]//@href').extract_first()
        storyName = extractStoryLink(storyName)
        
        abstract = (profile_top.xpath('.//div/text()').extract_first())
        rating = profile_top.xpath('.//span/a/text()').extract_first()
        otherInfo = profile_top.xpath('.//span').extract()[3]
        
        date = convertDate(profile_top.xpath('.//span/text()').extract()[3])
        storyType = response.xpath('//div[@id="pre_story_links"]').xpath('.//a/@href').extract()[-1]
        text = response.xpath('//div[@id="storytext"]').extract_first().lower()
        
        #find relevant characters
        characterFreq = {}
        for character, names in characters.items():
            for name in names:
                if(name in text):
                    if(character not in characterFreq):
                        characterFreq[character] = 0
                    characterFreq[character] += text.count(name)	
          
        #get author
        author = ''
        for link in profile_top.xpath('.//@href'):
            if(isUserLink(link.extract())):
                author = link.extract()
                nextLinks[author] = self.parseUserPage
        
        yield {
            'pageType': 'story',
            'storyLink': storyName,
            'author': author,
            'title': response.xpath('//title/text()').extract_first(),
            'storyType': storyType,
            #'abstract': abstract,
            'rating': rating,
            'otherInfo': getOtherInfoAsJson(otherInfo),
            'date': date.strftime('%Y-%m-%d %M:%S'),
            'characters': characterFreq
        }
        
        for link, func in nextLinks.items():
            yield response.follow(link, callback=func)

    def parseReview(self, response):
        nextLinks = {}
        reviewOf = response.xpath('//th').xpath('.//@href').extract_first()
        for review in response.xpath('//table[@id="gui_table1i"]//td'):
            reviewBody = (review.xpath('.//div/text()').extract_first())
            #remove punctuation
            table = str.maketrans("", "", string.punctuation)
            reviewBody = reviewBody.translate(table)
            sentimentScore = sum([sid.polarity_scores(word)['compound'] for word in reviewBody.split()])
            reviewer = (review.xpath('./text()').extract_first())
            if(reviewer is ' '):
                reviewer = (review.xpath('./a/@href').extract_first())
                nextLinks[reviewer] = self.parseUserPage;
            yield{
                'pageType': 'review',
                'reviewOf': reviewOf,
                'reviewer': reviewer,
                #'reviewBody': reviewBody,
                'sentimentScore': sentimentScore
            }
            
        for link, func in nextLinks.items():
            yield response.follow(link, callback=func)