#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, re
import json, requests
from hcr import process_img_zone

re_extractid = re.compile(r"^.*/([^/]+)$", re.I)

def buildUrl(url):
    if url.startswith("/"):
        url = "http://animeka.com%s" % url
    return url

def download(url):
    url = buildUrl(url)
    print url
    page = re_extractid.sub(r'\1', url)
    if not os.path.isdir(".cache"):
        os.makedirs(".cache")
    fil = os.path.join(".cache", page)
    if not os.path.exists(fil):
        data = requests.get(url).content
        if "charset=iso-8859-1" in data:
            data = data.decode("iso-8859-15").encode("utf-8")
        with open(fil, "w") as f:
            f.write(data)
    else:
        with open(fil) as f:
            data = f.read()
    return data

re_clean = re.compile(r'<[^>]+>')
clean = lambda x: re_clean.sub('', x)

re_nextPage = re.compile(r'<a href="([^"]+)">Suivant &gt;</a>', re.I)
re_title = re.compile(r'<a href="(/animes/detail/[^"]+)">(.*)</td></tr>', re.I)
re_country = re.compile(r'title="([^"]+)"', re.I)
re_id = re.compile(r'/animes/(?:epis|staff)/id_([^._]+)[._]', re.I)
re_scorePic = re.compile(r'<img src="/animes/([^.]+)\.png"', re.I)
re_idSure = re.compile(r'name="id_serie_note" value="([^"]+)"', re.I)

def addScorePic(anime, _id):
    if _id == None:
        return
    anime["animekaId"] = _id
    anime["scoresPic"] = "http://animeka.com/animes/%s.png" % _id if _id else ""
    download(anime["scoresPic"])
    img = os.path.join('.cache', '%s.png' % _id)
    try:
        anime["votes"] = int(process_img_zone(img, 55, 5, 100, 20))
        anime["score"] = float(process_img_zone(img, 55, 20, 100, 35))
    except (IOError, ValueError):
        anime["votes"] = ""
        anime["score"] = ""

animes = {}
def saveOne(anime=None):
    if anime:
        if "scoresPic" not in anime:
            data = download(anime["url"])
            if '<td class="animestxt">Pas de note' in data:
                addScorePic(anime, re_idSure.search(data).group(1))
            else:
                addScorePic(anime, re_scorePic.search(data).group(1))
        if "scoresPic" not in anime or not anime["animekaId"]:
            print >> sys.stderr, "WARNING: no pic for", anime["url"], "page", anime["source"]
        if anime["animekaId"] in animes:
            print >> sys.stderr, "WARNING: doublon", anime, animes[anime["animekaId"]]
            return {}
        animes[anime["animekaId"]] = dict(anime)
    return {}

def process(url):
    url = buildUrl(url)
    data = download(url)

    curAnime = saveOne()
    nextPage = ""
    for line in data.split("\n"):
        # find next page
        urlNextPage = re_nextPage.search(line)
        if urlNextPage:
            nextPage = urlNextPage.group(1)
        # get title and link
        if '<table class="animesindex">' in line:
            curAnime = saveOne(curAnime)
            curAnime["source"] = url
            anime = re_title.search(line)
            if anime:
                curAnime["url"] = buildUrl(anime.group(1))
                curAnime["name"] = clean(anime.group(2))
            else:
                print >> sys.stderr, "WARNING: anime line but no name/link", line
        # get scores pic
        elif "/animes/staff/id_" in line or "/animes/epis/id_" in line:
            if "animekaId" in curAnime:
                continue
            _id = re_id.search(line).group(1)
            addScorePic(curAnime, _id)
        # get country
        elif "/_distiller/show_flag.php" in line:
            curAnime["country"] = re_country.search(line).group(1)
    saveOne(curAnime)
    if nextPage:
        print "TOTAL", len(animes.keys())
        process(nextPage)


if __name__ == "__main__":
    process("http://animeka.com/animes/series/~_1.html")
    print "TOTAL", len(animes.keys())
    with open("data.json", 'w') as f:
        json.dump(animes, f)

# FIX #PNG 9117 <> #ANIMES 9151
# FIELDS
# - studios
# - genres
# - auteurs
# - format
#  + episodes
#  + format
# EXTRACT NOTE + VOTERS FROM SCOREPICS

