#!/usr/bin/env python3

import sys
import os
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

    for match in re.findall('<link.+type="text/css".+href="(.+)".+>|<link.+href="(.+)".+type="text/css".+>', r.text):
        for group in match:
            if group:
                print('... found ' + group)
                yield group
                # css may import other css
                for subcss in findCssUrls(group):
                      yield subcss

    for match in re.findall('@import url\((.+)\)', r.text):
        print('... found ' + match)
        yield match 
        # css may import other css
        for subcss in findCssUrls(match):
            yield subcss
                

def findFontUrl(line, fontHost = GOOGLE_FONT_HOST):
    try:
        url = line.split(fontHost)[1].split(') ')[0]
        return 'https://' + fontHost + url
    except:
        return None

def localiseCssFonts(inputCss, outputCss, localHost):
    
    cssLines = inputCss.readlines()
    
    for i in range(len(cssLines)):
        fontUrl = findFontUrl(cssLines[i])
    
        if fontUrl:
            urlParts = fontUrl.split('/')
            fontFace = urlParts[4]
            fontVariant = urlParts[6]
            print('google font found: {} ({})'.format(fontFace, fontUrl))        
            
            localFontPath = localHost + '/fonts/' + fontFace + '-' + fontVariant
            localFont = open(localFontPath, 'wb')
            download(fontUrl, localFont)
    
            cssLines[i] = cssLines[i].replace(fontUrl, 'https://' + localFontPath)
    
    for line in cssLines:
        outputCss.write(line)

if len(sys.argv) < 2:
    raise Exception('Usage: ungooglefonts.py <your_site_host>')

siteHost = sys.argv[1]

for path in [siteHost, siteHost + '/fonts']:
    if not os.path.exists(path):
        os.makedirs(path)


googleFontsCssPath = siteHost + '/googleFonts.css'
googleFontsCss = open(googleFontsCssPath, 'x')
googleFontsCss = open(googleFontsCssPath, 'ab')

print('finding css from https://{}'.format(siteHost))

for cssUrl in findCssUrls('https://' + siteHost):
    if GOOGLE_CSS_HOST in cssUrl:
        print('google font css --> appending to {}'.format(googleFontsCssPath))
        download(
            cssUrl,
            googleFontsCss, 
            # provide user agent for woff2 support
            API_REQUEST_HEADERS
            )
    
print('downloading google fonts occurring in {}'.format(googleFontsCssPath)) 
localiseCssFonts(open(googleFontsCssPath, 'r'), open(siteHost + '/fonts.css', 'w'), siteHost)

