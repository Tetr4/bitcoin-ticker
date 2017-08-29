#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import threading
from collections import deque

import requests
from PIL import ImageDraw

from papirus import PapirusComposite  # requires python2


class BitcoinTicker:
    api = 'https://bitcoinapi.de/widget/current-btc-price/rate.json?culture=de'
    logo = os.path.join(os.path.dirname(__file__), 'bitcoin.bmp')
    update_rate = 60  # seconds
    max_partial_redraws = 5
    padding_x = 10
    padding_y = 20
    graph_height_ratio = 0.5
    graph_rate_range = 50  # upper/lower bound relative to current rate in euro
    rate_text_size = 20

    def __init__(self):
        self.composite = PapirusComposite(False)
        width = self.composite.papirus.width
        height = self.composite.papirus.height

        # logo
        logo_side = height - self.padding_y * 2
        self.composite.AddImg(self.logo,
                              self.padding_x, self.padding_y,
                              size=(logo_side, logo_side))

        # graph
        graph_X = logo_side + self.padding_x * 2  # next to logo
        graph_y = (1 - self.graph_height_ratio) * height  # lower part
        graph_width = width - graph_X
        graph_height = height - graph_y
        self.graph = Graph(graph_X, graph_y, graph_width, graph_height)

        # rate
        rate_x = graph_X  # left aligned with graph
        rate_y = graph_y / 2 - self.rate_text_size / 2  # center upper part
        self.composite.AddText('',
                               rate_x, rate_y,
                               size=self.rate_text_size,
                               Id='rate')

        self.stop_event = threading.Event()
        self.thread = None

    def start(self):
        self.stop_event.clear()
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join()

    def is_running(self):
        return not self.stop_event.is_set()

    def _sleep(self, duration):
        self.stop_event.wait(timeout=duration)

    def run(self):
        num_partial_updates = self.max_partial_redraws  # full redraw on 1. run
        while self.is_running():
            # get rate from api
            try:
                rate = self.get_rate()
            except requests.exceptions.RequestException as e:
                print(e)
                self._sleep(self.update_rate)
                continue  # retry

            # update rate
            rate_text = u'%.2f €' % rate
            print(rate_text)
            self.composite.UpdateText('rate', rate_text)

            # update graph
            self.graph.add(rate)
            high = rate + self.graph_rate_range / 2
            low = rate - self.graph_rate_range / 2
            self.graph.draw(self.composite.image, low, high)

            # draw
            if num_partial_updates < self.max_partial_redraws:
                self.composite.WriteAll(partialUpdate=True)
                num_partial_updates += 1
            else:
                self.composite.WriteAll(partialUpdate=False)
                num_partial_updates = 0

            # delay
            self._sleep(self.update_rate)

    def get_rate(self):
        response = requests.get(self.api)
        rate_text = response.json()['price_eur']
        rate = ''.join(c for c in rate_text if c.isdigit() or c == ',')
        return float(rate.replace(',', '.'))


class Graph:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.data = deque([0] * width, maxlen=width)

    def add(self, value):
        self.data.append(value)

    def draw(self, image, low, high):
        img_draw = ImageDraw.Draw(image)
        img_draw.rectangle([(self.x, self.y),
                            (self.x + self.width, self.y + self.height)],
                           fill="white")  # clear
        for i, value in enumerate(self.data):
            bar_height = (value - low) / (high - low) * self.height
            bar_height = max(0, min(self.height, bar_height))  # clamp
            bar_end = self.y + self.height
            bar_start = bar_end - bar_height
            img_draw.line([(self.x + i, bar_start),
                           (self.x + i, bar_end)],
                          fill="black")


if __name__ == "__main__":
    ticker = BitcoinTicker()
    ticker.run()  # blocking
