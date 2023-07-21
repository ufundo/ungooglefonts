#!/usr/bin/env python3

import sys
import os
import requests

GOOGLE_CSS_HOST = 'fonts.googleapis.com'
# urls like https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&display=swap

GOOGLE_FONT_HOST = 'fonts.gstatic.com'
# urls like https://fonts.gstatic.com/s/librebaskerville/v14/kmKiZrc3Hgbbcjq75U4uslyuy4kn0qviTgY3KcA.woff2

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'

def findFontUrl(line, fontHost = GOOGLE_FONT_HOST):
    try:
        url = line.split(fontHost)[1].split(') ')[0]
        return 'https://' + fontHost + url
    except:
        return None

def download(url, targetFile, headers = None):

    r = requests.get(url, allow_redirects=True, headers=headers)

    if r.status_code == 200:
        targetFile.write(r.content)
    else:
        raise Exception('download failed for ' + url)

if len(sys.argv) < 3:
    raise Exception('Usage: ungooglefonts.py <google_css_url> <your_site_host>')

siteHost = sys.argv[1]
cssUrl = sys.argv[2]

for path in [siteHost, siteHost + '/fonts']:
    if not os.path.exists(path):
        os.makedirs(path)

localCssPath = siteHost + '/fonts.css'

localCss = open(localCssPath, 'ab')

download(
    cssUrl,
    localCss, 
    # provide user agent for woff2 support
    {'User-Agent': USER_AGENT}
    )

localCss = open(localCssPath, 'r')

cssLines = localCss.readlines()

for i in range(len(cssLines)):
    fontUrl = findFontUrl(cssLines[i])

    if fontUrl:
        urlParts = fontUrl.split('/')
        fontFace = urlParts[4]
        fontVariant = urlParts[6]
        print('Font identified: {} ({})'.format(fontFace, fontUrl))        
        
        localFontPath = siteHost + '/fonts/' + fontFace + '-' + fontVariant
        localFont = open(localFontPath, 'wb')
        download(fontUrl, localFont)

        cssLines[i] = cssLines[i].replace(fontUrl, 'https://' + localFontPath)

localCss = open(localCssPath, 'w')
for line in cssLines:
    localCss.write(line)
