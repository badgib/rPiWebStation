#!/usr/bin/python3
import numpy as np
import tkinter as tk
import tkinter.ttk as ttk
import urllib.request
import subprocess
import io
import json

import matplotlib
matplotlib.use("TkAgg")

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from mpg123 import Mpg123, Out123

from threading import Thread

from PIL import Image, ImageTk
from bs4 import BeautifulSoup



mp3 = Mpg123()
out = Out123()

class weatherRadio:

    def __init__(self, master=None):

        self.flag = True
        self.isFullScreen = True
        self.stationList = ["beatblender", "brfm", "bootliquor", "cliqhop", "covers", "deepspaceone", "defcon", "digitalis", "dronezone", "dubstep", "fluid", "folkfwd", "groovesalad", "gsclassic", "reggae", "illstreet", "indiepop", "seventies", "lush", "metal", "missioncontrol", "n5md", "poptron", "secretagent", "7soul", "sf1033", "scanner", "live", "specials", "sonicuniverse", "spacestation", "suburbsofgoa", "synphaera", "darkzone", "thetrip", "thistle", "u80s", "vaporwaves"]
        self.stationName = 'defcon'
        self.url = 'http://ice.somafm.com/defcon'

        self.lat = 0.0
        self.lon = 0.0
        self.appid = '0123123123123abc'
        self.mapDelayMS = 30000
        self.tracksDelayMS = 90000
        self.forecastDelayMS = 600000

        self.dates = []
        self.temps = []
        self.feels = []
        self.press = []
        self.humis = []
        self.t_kfs = []
        self.cloudss = []
        self.winds = []
        self.gusts = []
        self.visibilitys = []

        # build ui
        self.mainFrame = tk.Tk() if master is None else tk.Toplevel(master)
        self.mainFrame.configure(height=600, width=1024)
        self.mainFrame.minsize(1024, 600)
        self.mapFrame = ttk.Frame(self.mainFrame)
        self.mapFrame.configure(height=600, width=600)
        self.mapLabel = tk.Label(self.mapFrame)
        self.mapLabel.configure(height=600, width=600)
        self.mapLabel.pack(anchor="center", side="top")
        self.mapFrame.pack(anchor="w", side="left")
        self.mapFrame.pack_propagate(0)
        self.rightFrame = ttk.Frame(self.mainFrame)
        self.rightFrame.configure(height=200, width=200)
        self.songListFrame = ttk.Frame(self.rightFrame)
        self.songListFrame.configure(height=200, width=424)
        self.songListLabel = ttk.Label(self.songListFrame)
        self.songListLabel.configure(
            justify="center",
            text="",
            wraplength=424,
        )
        self.songListLabel.pack(anchor="center", expand="true", fill="y", side="top")
        self.songListFrame.pack(anchor="center", expand="true", fill="both", side="top")

        self.fig = Figure()
        self.plotCanvas = FigureCanvasTkAgg(self.fig, self.rightFrame)
        self.plotCanvas.get_tk_widget().pack(anchor="s", fill="x", side="bottom")
        self.plotCanvas.get_tk_widget().configure(height=200, width=424)

        self.buttonFrame = ttk.Frame(self.rightFrame)
        self.buttonFrame.configure(height=200, width=200)
        self.playButton = ttk.Button(self.buttonFrame)
        self.playButton.configure(text="play")
        self.playButton.pack(side="left")
        self.playButton.configure(command=self.playStation)
        self.stopButton = ttk.Button(self.buttonFrame)
        self.stopButton.configure(text="stop")
        self.stopButton.pack(side="left")
        self.stopButton.configure(command=self.stopStation)
        self.volUpButton = ttk.Button(self.buttonFrame)
        self.volUpButton.configure(text="vol+")
        self.volUpButton.pack(side="left")
        self.volUpButton.configure(command=self.volUp)
        self.volDnButton = ttk.Button(self.buttonFrame)
        self.volDnButton.configure(text="vol-")
        self.volDnButton.pack(side="left")
        self.volDnButton.configure(command=self.volDn)
        self.fullButton = ttk.Button(self.buttonFrame)
        self.fullButton.configure(text="full")
        self.fullButton.pack(side="left")
        self.fullButton.configure(command=self.toggleFullscreen)
        self.buttonFrame.pack(anchor="s", side="bottom")
        self.selectedStation = tk.StringVar()
        
        self.stationSelector = ttk.Combobox(self.rightFrame) 
            
        self.stationSelector.configure(textvariable=self.selectedStation, values=self.stationList, state='readonly')
        self.stationSelector.bind('<<ComboboxSelected>>', self.selStat)
        self.stationSelector.pack(anchor="s", expand="false", fill="x", side="bottom")
        self.rightFrame.pack(anchor="e", expand="false", fill="both", side="right")

        self.temp_plot = self.fig.add_subplot()
        self.temp_plot.xaxis.set_major_locator(MaxNLocator(10))

        self.pres_plot = self.temp_plot.twinx()
        self.humi_plot = self.temp_plot.twinx()
        self.feel_plot = self.temp_plot.twinx()
        self.t_kf_plot = self.temp_plot.twinx()
        self.clouds_plot = self.temp_plot.twinx()
        self.wind_plot = self.temp_plot.twinx()
        self.gust_plot = self.temp_plot.twinx()
        self.visibility_plot = self.temp_plot.twinx()

        self.temp_plot.tick_params('y', colors='#FF00FF')
        self.pres_plot.tick_params('y', colors='#FF6599')
        self.feel_plot.tick_params('y', colors='#FF0000')
        self.humi_plot.tick_params('y', colors='#FF8E00')
        self.t_kf_plot.tick_params('y', colors='#FFFF00')
        self.clouds_plot.tick_params('y', colors='#008E00')
        self.wind_plot.tick_params('y', colors='#00C0C0')
        self.gust_plot.tick_params('y', colors='#400098')
        self.visibility_plot.tick_params('y', colors='#8E008E')

        self.interMap()
        self.interForecast()
        self.interTracks()
        if self.flag:

            self.prepStation()
        
        # Main widget
        self.mainwindow = self.mainFrame
        self.mainwindow.attributes('-fullscreen', self.isFullScreen)

    def run(self):

        self.mainwindow.mainloop()

    def playStation(self):

        self.prepStation()

    def stopStation(self):

        self.flag = False

    def volUp(self):

        command = ["amixer", "sset", "Master", "5%+"]
        subprocess.Popen(command)

    def volDn(self):

        command = ["amixer", "sset", "Master", "5%-"]
        subprocess.Popen(command)

    def toggleFullscreen(self):

        self.isFullScreen = not self.isFullScreen
        self.mainwindow.attributes('-fullscreen', self.isFullScreen)

    def selStat(self, opt):
        
        self.stationName = self.selectedStation.get()

        if self.flag:
            
            self.prepStation()

    def prepStation(self):

        self.flag = False
        self.updateTracks()
        self.flag = True

        self.url = f'http://ice.somafm.com/{self.stationName}'
        thread = Thread(target=self.radioPlayer, daemon=True)
        thread.start()

    def updateMap(self):

        try:

            im = urllib.request.urlopen('https://www.blitzortung.org/en/Images/image_b_pl.png').read()
            im = Image.open(io.BytesIO(im))
            im = im.resize((600, 600), Image.Resampling.LANCZOS)
            
            im = ImageTk.PhotoImage(im)

            self.mapLabel.configure(image=im)
            self.mapLabel.image = im

        except Exception as e:
            pass

    def updateTracks(self):

        try:

            data = urllib.request.urlopen(f'https://somafm.com/{self.stationName}/songhistory.html').read()
            
            soup = BeautifulSoup(data, 'html.parser')
            table = soup.find('table')

            trackIDtext = ''
            for e, row in enumerate(table.find_all('tr')):

                if e > 1 and e < 19:

                    tds = row.find_all('td')

                    try:

                        trackIDtext = trackIDtext + f'{tds[1].text} - {tds[2].text}\n'

                    except:

                        trackIDtext = trackIDtext + 'break or broken\n'

            self.songListLabel.configure(text=trackIDtext)
        
        except Exception as e:

            print(f'error trying to get tracklist; {e}')
            self.songListLabel.configure(f'error trying to get tracklist; {e}')

    def updateForecast(self):

        self.dates.clear()
        self.temps.clear()
        self.feels.clear()
        self.press.clear()
        self.humis.clear()
        self.t_kfs.clear()
        self.cloudss.clear()
        self.winds.clear()
        self.gusts.clear()
        self.visibilitys.clear()

        forecast_json = urllib.request.urlopen(f'https://api.openweathermap.org/data/2.5/forecast?lat={self.lat}&lon={self.lon}&lang=pl&units=metric&appid={self.appid}')
        #quality_json = urllib.request.urlopen(f'https://api.openweathermap.org/data/2.5/air_pollution?lat={self.lat}&lon={self.lon}&appid={self.appid}')
        forecast_data = json.load(forecast_json)

        for f in forecast_data['list']:

            date = f['dt_txt'].split(':')[:-2][0].split('-')[1:][1].replace(' ', '@')

            temp = f['main']['temp']
            feel = f['main']['feels_like']
            pres = f['main']['pressure']
            humi = f['main']['humidity']
            t_kf = f['main']['temp_kf']

            clouds = f['clouds']['all']
            wind = f['wind']['speed']
            gust = f['wind']['gust']

            visibility = f['visibility']/1000

            self.dates.append(date)
            self.temps.append(temp)
            self.feels.append(feel)
            self.press.append(pres)
            self.humis.append(humi)
            self.t_kfs.append(t_kf)
            self.cloudss.append(clouds)
            self.winds.append(wind)
            self.gusts.append(gust)
            self.visibilitys.append(visibility)

            # print(f'temp: {temp}\t feel: {feel}\t pres: {pres}\t humi: {humi}\t t_kf: {t_kf}\t clouds: {clouds}\t wind: {wind}\t gust: {gust}\t visibility: {visibility}')
        
        self.pres_plot.clear()
        self.temp_plot.clear()
        self.feel_plot.clear()
        self.humi_plot.clear()
        self.t_kf_plot.clear()
        self.clouds_plot.clear()
        self.wind_plot.clear()
        self.gust_plot.clear()
        self.visibility_plot.clear()

        self.temp_plot.axhline(y=np.median(self.temps), color='#FF00FF', linestyle='dashed', linewidth=1)
        self.temp_plot.axhline(y=0, color='black', linestyle='dashed', linewidth=1)
        self.pres_plot.set_ylim(bottom=930, top=1100)
        self.temp_plot.set_ylim(bottom=-20, top=40)
        self.feel_plot.set_ylim(bottom=-20, top=40)
        self.humi_plot.set_ylim(bottom=0, top=100)
        self.t_kf_plot.set_ylim(bottom=-5, top=15)
        self.clouds_plot.set_ylim(bottom=0, top=100)
        self.wind_plot.set_ylim(bottom=0, top=60)
        self.gust_plot.set_ylim(bottom=0, top=100)
        self.visibility_plot.set_ylim(bottom=0, top=10)

        self.pres_plot.plot(self.dates, self.press, color='#FF6599', linestyle='dashed', linewidth=1)
        self.temp_plot.plot(self.dates, self.temps, color='#FF00FF')
        self.feel_plot.plot(self.dates, self.feels, color='#FF0000')
        self.humi_plot.plot(self.dates, self.humis, color='#FF8E00')
        self.t_kf_plot.plot(self.dates, self.t_kfs, color='#FFFF00', linestyle='dashed', linewidth=1)
        self.clouds_plot.plot(self.dates, self.cloudss, color='#008E00', linestyle='dotted', linewidth=1)
        self.wind_plot.plot(self.dates, self.winds, color='#00C0C0', linestyle='dashdot', linewidth=1)
        self.gust_plot.plot(self.dates, self.gusts, color='#400098', linestyle='dashed', linewidth=1)
        self.visibility_plot.plot(self.dates, self.visibilitys, color='#8E008E', linestyle='dashed', linewidth=1)

        self.temp_plot.xaxis.set_major_locator(MaxNLocator(6))
        self.plotCanvas.draw()
        self.plotCanvas.flush_events()

    def interMap(self):

        self.updateMap()
        self.mainFrame.after(self.mapDelayMS, self.interMap)

    def interTracks(self):

        self.updateTracks()
        self.mainFrame.after(self.tracksDelayMS, self.interTracks)

    def interForecast(self):

        self.updateForecast()
        self.mainFrame.after(self.forecastDelayMS, self.interForecast)

    def radioPlayer(self):

        response = urllib.request.urlopen(self.url)

        while self.flag:

            chunk = response.read(4096)

            if not chunk:

                break

            mp3.feed(chunk)

            for frame in mp3.iter_frames(out.start):

                out.play(frame)


if __name__ == "__main__":

    app = weatherRadio()
    app.run()
