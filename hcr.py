#!/usr/bin/env python
# -*- coding: utf-8 -*-
# hcr: Human character recognition

from PIL import Image

TEMPALPHABET = "/tmp/alphabet.json"
try:
    import json
    with open(TEMPALPHABET) as f:
        dico = json.load(f)
except:
    dico = {}

fmt = lambda x: u"█" if x and x != u" " else u" "

def print_img(data, w, h):
    print "\n".join(["".join([fmt(a) for a in data[i*w:(i+1)*w]]) for i in range(h)]) + "\n"

def transpose(data, w, h):
    tlines = ["".join([fmt(data[i*w+j]) for i in range(h)]) for j in range(w)]
    return "".join(tlines)

def img_to_str(img, verbose=False):
    w, h = img.size
    data = list(img.getdata())
    # visual img
    if verbose:
        print_img(data, w, h)
    return transpose(data, w, h)

def add_char(char, height, dico=dico):
    if not char:
        return ""
    if char not in dico:
        width = len(char) / height
        print_img(transpose(char, height, width), width, height)
        dico[char] = raw_input("Input character:")
        try:
            with open(TEMPALPHABET, "w") as f:
                json.dump(dico, f)
        except:
            pass
    return dico[char]

def process_textline(img, dico=dico, verbose=False):
    width, height = img.size
    imgstr = img_to_str(img, verbose=verbose)
    blank = " " * height
    char = ""
    val = ""
    while imgstr:
        line = imgstr[:height]
        imgstr = imgstr[height:]
        if line == blank:
            val += add_char(char, height, dico)
            char = ""
            continue
        char += line
    val += add_char(char, height, dico)
    if verbose:
        print val + "\n"
    return val

def process_img_zone(filepath, x0=0, y0=0, x1=0, y1=0, dico=dico, verbose=False):
    img = Image.open(filepath)
    #img.show()
    width, height = img.size
    if not x1:
        x1 = width - 1
    if not y1:
        y1 = height - 1
    return process_textline(img.crop((x0,y0,x1,y1)), dico, verbose)

if __name__ == "__main__":
    import sys, os
    img = os.path.join('.cache', '%s.png' % sys.argv[1])
    dico = {}
    process_img_zone(img, 55, 5, 100, 20, dico, True)
    process_img_zone(img, 55, 20, 100, 35, dico, True)

