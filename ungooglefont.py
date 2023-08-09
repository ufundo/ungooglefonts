#!/usr/bin/env python3

import sys
import os
from urllib.parse import urlparse, urlunparse
import requests
import re

GOOGLE_CSS_HOST = 'fonts.googleapis.com'
# urls like https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&display=swap

GOOGLE_FONT_HOST = 'fonts.gstatic.com'
# urls like https://fonts.gstatic.com/s/librebaskerville/v14/kmKiZrc3Hgbbcjq75U4uslyuy4kn0qviTgY3KcA.woff2

API_REQUEST_HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}


def download(url, targetFile, headers = None):

    r = requests.get(url, allow_redirects=True, headers=headers)

    if r.status_code != 200:
        raise Exception('download failed for ' + url)

    targetFile.write(r.content)

def findCssUrls(url):
    r = requests.get(url, allow_redirects=True)

    if r.status_code != 200:
        raise Exception('cant get specified url')

    for match in re.findall('<link.+href="(.+\.css)".*?>', r.text):
        print('... found ' + match)
        yield match 
        # css may import other css
        for subcss in findCssUrls(match):
            yield subcss

    for match in re.findall('@import url\((.+)\)', r.text):
        print('... found ' + match)
        yield match 
        # css may import other css
        for subcss in findCssUrls(match):
            yield subcss

    for match in re.findall('@import\"(.+?)\"', r.text):
        print('... found ' + match)
        yield match 
        # css may import other css
        for subcss in findCssUrls(match):
            yield subcss
                
def localiseCssFonts(inputCss, outputCss, localFontsPath):
    
    inputCss.seek(0)
    cssLines = inputCss.readlines()
    
    for i in range(len(cssLines)):
        for googleFontUrl in re.findall('url\((https?:\/\/' + GOOGLE_FONT_HOST + '.+)\) format', cssLines[i]): 

            urlParsed = urlparse(googleFontUrl)

            fontFace = urlParsed.path.split('/')[2]
            print('google font found: {} ({})'.format(fontFace, googleFontUrl))        
            
            localFontPath = localFontsPath + '/' + urlParsed.path[1:].replace('/','-')
            localFont = open(localFontPath, 'wb')

            download(googleFontUrl, localFont)
    
            cssLines[i] = cssLines[i].replace(googleFontUrl, 'https://' + localFontPath)
    
    for line in cssLines:
        outputCss.write(line)


def processUrl(siteUrl, cssUrls = None):
    siteUrl = urlparse(siteUrl, scheme='https')
    siteHost = siteUrl.hostname
    
    fontsDir = siteHost + '/fonts'
    cssDir = siteHost + siteUrl.path.replace('/','-')
    
    for path in [siteHost, fontsDir, cssDir]:
        if not os.path.exists(path):
            os.makedirs(path)
    
    googleFontsCssPath = cssDir + '/googleFonts.css'
    
    # check file doesn't exist to avoid appending to existing file
    try:
        googleFontsCss = open(googleFontsCssPath, 'x')
    except:
        print('Hmmm, {} already exists. Are you sure you want to continue? This could result in duplicate css being appended to the file'.format(googleFontsCssPath))
        if input('Continue? (yN)') != 'y':
            return 0 
    
    googleFontsCss = open(googleFontsCssPath, 'ab')
    
    # use css urls explicitly provided on command line
    if cssUrls:
        print('using explicitly provided css urls:')
        for url in cssUrls:
            print(' - ' + url)
    else:
        siteUrlString = urlunparse(siteUrl)
        print('finding css from {}'.format(siteUrlString))
        cssUrls = findCssUrls(siteUrlString)
    
    
    for cssUrl in cssUrls:
        if GOOGLE_CSS_HOST in cssUrl:
            print('google font css --> appending to {}'.format(googleFontsCssPath))
            download(
                cssUrl,
                googleFontsCss, 
                # provide user agent for woff2 support
                API_REQUEST_HEADERS
                )

    googleFontsCss.close()
        
    print('downloading google fonts occurring in {}'.format(googleFontsCssPath)) 
    localiseCssFonts(open(googleFontsCssPath, 'r'), open(cssDir + '/fonts.css', 'w'), fontsDir)



if __name__ == "__main__":

    if len(sys.argv) < 2:
        raise Exception('Usage: ungooglefonts.py <url>')

    processUrl(sys.argv[1], sys.argv[2:])
