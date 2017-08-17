#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import threading
from papirus import PapirusComposite
from PIL import Image, ImageDraw
from collections import deque

class BitcoinTicker:
	api = 'https://bitcoinapi.de/widget/current-btc-price/rate.json?culture=de'
	updateRate = 60 # seconds
	updatesUntilFullRedraw = 5
	logo = 'bitcoin.bmp'
	paddingX = 10
	paddingY = 20
	graphHeightRatio = 0.5
	graphRateRange = 50 # upper/lower bound relative to current rate in euro
	rateTextSize = 20

	def __init__(self):
		self.composite = PapirusComposite(False)
		width = self.composite.papirus.width
		height = self.composite.papirus.height

		# logo
		logoSide = height - self.paddingY*2
		self.composite.AddImg(self.logo,
				x=self.paddingX,
				y=self.paddingY,
				size=(logoSide,logoSide))

		# graph
		graphPosX = logoSide + self.paddingX*2 # next to logo
		graphPosY = (1 - self.graphHeightRatio) * height # lower part
		graphWidth = width - graphPosX
		graphHeight = height - graphPosY
		self.graph = Graph(graphPosX, graphPosY, graphWidth, graphHeight)

		# rate
		ratePosX = graphPosX # left aligned with graph
		ratePosY = graphPosY/2 - self.rateTextSize/2 # center in upper part
		self.composite.AddText('',
				x=ratePosX,
				y=ratePosY,
				size=self.rateTextSize,
				Id='rate')

		self.stopEvent = threading.Event()

	def start(self):
		self.stopEvent.clear()
		self.thread = threading.Thread(target=self.run)
		self.thread.start()

	def stop(self):
		self.stopEvent.set()
		self.thread.join()

	def isRunning(self):
		return not self.stopEvent.is_set()

	def sleep(self, duration):
		self.stopEvent.wait(timeout=duration)

	def run(self):
		numPartialUpdates = self.updatesUntilFullRedraw # full redraw initially
		while self.isRunning():
			# get rate from api
			try:
				rate = self.getRate()
			except requests.exceptions.RequestException as e:
				print(e)
				self.sleep(self.updateRate)
				continue # retry

			# update rate
			rateText = u'%.2f €' % rate
			print(rateText)
			self.composite.UpdateText('rate', rateText)

			# update graph
			self.graph.add(rate)
			high = rate + self.graphRateRange/2
			low = rate - self.graphRateRange/2
			self.graph.draw(self.composite.image, low, high)

			# draw
			if numPartialUpdates < self.updatesUntilFullRedraw:
				self.composite.WriteAll(partialUpdate=True)
				numPartialUpdates += 1
			else:
				self.composite.WriteAll(partialUpdate=False)
				numPartialUpdates = 0

			# delay
			self.sleep(self.updateRate)

	def getRate(self):
		response = requests.get(self.api)
		rateText = response.json()['price_eur']
		rate = ''.join(c for c in rateText if c.isdigit() or c == ',')
		return float(rate.replace(',', '.'))

class Graph:
	def __init__(self, x, y, width, height):
		self.x = x
		self.y = y
		self.width = width
		self.height = height
		self.data = deque([0]*width, maxlen=width)

	def add(self, value):
		self.data.append(value)

	def draw(self, image, low, high):
		imgDraw = ImageDraw.Draw(image)
		imgDraw.rectangle([self.x, self.y, self.x+self.width, self.y+self.height], fill="white") # clear
		for i, value in enumerate(self.data):
			barHeight = (value-low)/(high-low) * self.height
			barHeight = max(0, min(self.height, barHeight)) # clamp
			barEnd = self.y + self.height
			barStart = barEnd - barHeight
			imgDraw.line([self.x+i, barStart, self.x+i, barEnd], fill="black")

if __name__ == "__main__":
	ticker = BitcoinTicker()
	ticker.run() # blocking
