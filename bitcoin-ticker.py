#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import json
import time
from papirus import PapirusComposite
from PIL import Image, ImageDraw
from collections import deque

# dimensions
composite = PapirusComposite(False)
width = composite.papirus.width
height = composite.papirus.height
paddingX = 10
paddingY = 20

# logo
logoSide = height - paddingY*2
composite.AddImg('bitcoin.bmp',
		x=paddingX,
		y=paddingY,
		size=(logoSide,logoSide))

# graph
graphPosX = logoSide + paddingX*2 # next to logo
graphPosY = 0.5 * height # lower part
graphWidth = width - graphPosX
graphHeight = height - graphPosY
graphDraw = ImageDraw.Draw(composite.image)
graphRateRange = 50 # upper/lower bound relative to current rate in euro

# rate
rateSize = 19
ratePosX = graphPosX # left aligned with graph
ratePosY = graphPosY/2 - rateSize/2 # center in upper part
composite.AddText('',
		x=ratePosX,
		y=ratePosY,
		size=rateSize,
		Id='rate')

# update loop
updateRate = 60 # seconds
updatesUntilFullRedraw = 5
numPartialUpdates = updatesUntilFullRedraw # full redraw initially
historicalRates = deque([0]*graphWidth, maxlen=graphWidth)
while True:
	# get rate from api
	try:
		request = requests.get('https://bitcoinapi.de/widget/current-btc-price/rate.json?culture=de')
	except requests.exceptions.RequestException as e:
		# retry
		print(e)
		time.sleep(updateRate)
		continue
	rateText = request.json()['price_eur']
	rateValue = ''.join(c for c in rateText if c.isdigit() or c == ',')
	rateValue = float(rateValue.replace(',', '.'))
	print(rateText)

	# update rate
	composite.UpdateText('rate', rateText)

	# update graph
	historicalRates.append(rateValue)
	high = rateValue + graphRateRange/2
	low = rateValue - graphRateRange/2
	graphDraw.rectangle([graphPosX, graphPosY, graphPosX+graphWidth, graphPosY+graphHeight], fill="white") # clear
	for i, rate in enumerate(historicalRates):
		barHeight = (rate-low)/(high-low) * graphHeight
		barHeight = max(0, min(graphHeight, barHeight)) # clamp
		barEnd = graphPosY + graphHeight
		barStart = barEnd - barHeight
		graphDraw.rectangle([graphPosX+i, barStart, graphPosX+i+1, barEnd], fill="black")

	# draw
	if numPartialUpdates < updatesUntilFullRedraw:
		composite.WriteAll(partialUpdate=True)
		numPartialUpdates += 1
	else:
		composite.WriteAll(partialUpdate=False)
		numPartialUpdates = 0

	# delay
	time.sleep(updateRate)
