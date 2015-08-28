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
re_spaces = re.compile(r'(&nbsp;|\s)+')
clean = lambda x: re_spaces.sub(' ', re_clean.sub('', x)).strip().replace("&amp;", "&")

re_nextPage = re.compile(r'<a href="([^"]+)">Suivant &gt;</a>', re.I)
re_title = re.compile(r'<a href="(/animes/detail/[^"]+)">(.*)</td></tr>', re.I)
re_country = re.compile(r'title="([^"]+)"', re.I)
re_id = re.compile(r'/animes/(?:epis|staff)/id_([^._]+)[._]', re.I)
re_scorePic = re.compile(r'<img src="/animes/([^.]+)\.png"', re.I)
re_idSure = re.compile(r'name="id_serie_note" value="([^"]+)"', re.I)
re_format = re.compile(r'^(\d+ )?(\S+)(?: (\d+) mins( \(en cours\))?)?$')

gdint = lambda i: int(i.strip()) if i else None
arrType = lambda v: v.replace("é","É").strip("] [").split("] [")

def addScorePic(anime, _id):
    if _id == None:
        return
    anime["animekaId"] = _id
    anime["scorePic"] = "http://animeka.com/animes/%s.png" % _id if _id else ""
    download(anime["scorePic"])
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
        if "scorePic" not in anime:
            data = download(anime["url"])
            if '<td class="animestxt">Pas de note' in data:
                addScorePic(anime, re_idSure.search(data).group(1))
            else:
                addScorePic(anime, re_scorePic.search(data).group(1))
        if "scorePic" not in anime or not anime["animekaId"]:
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
        # get score pic
        elif "/animes/staff/id_" in line or "/animes/epis/id_" in line:
            if "animekaId" in curAnime:
                continue
            _id = re_id.search(line).group(1)
            addScorePic(curAnime, _id)
        # get country
        elif "/_distiller/show_flag.php" in line:
            curAnime["country"] = re_country.search(line).group(1)
        elif '<td class="animestxt">' in line:
            line = clean(line)
            if line.endswith(" :"):
                key = line.rstrip(" :")
                value = ""
            else:
                key, value = clean(line).split(' : ', 1)
            if key == "TITRE ORIGINAL":
                curAnime["name_original"] = value
            elif key.endswith(" DE PRODUCTION"):
                if " - " in value:
                    curAnime["date_start"], curAnime["date_end"] = (gdint(v) for v in value.split(" - "))
                else:
                    curAnime["date_start"] = gdint(value)
                    curAnime["date_end"] = gdint(value)
            elif key.startswith("STUDIO"):
                curAnime["studios"] = arrType(value)
            elif key.startswith("GENRE"):
                curAnime["categories"] = arrType(value)
            elif key.startswith("AUTEUR"):
                curAnime["authors"] = arrType(value)
            elif " DUR" in key:
                if value == "Non sp&eacute;cifi&eacute;":
                    continue
                match = re_format.search(value)
                curAnime["format"] = match.group(2).lower()
                curAnime["episodes"] = gdint(match.group(1))
                curAnime["duration"] = gdint(match.group(3))
                try:
                    curAnime["duration_global"] = curAnime["duration"] * curAnime["episodes"]
                except:
                    pass
                curAnime["running"] = not not match.group(4)
    saveOne(curAnime)
    if nextPage:
        print "TOTAL", len(animes.keys())
        process(nextPage)


if __name__ == "__main__":
    process("http://animeka.com/animes/series/~_1.html")
    print "TOTAL", len(animes.keys())
    with open(os.path.join("data", "data.json"), 'w') as f:
        json.dump(animes, f)

