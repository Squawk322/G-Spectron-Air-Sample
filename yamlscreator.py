# -*- coding: utf-8 -*-
"""
Created on Fri Jan 14 17:59:02 2022

TITLE: 

@author: Alejandro Condori aleja
E-mail: alejandrocondori2@gmail.com
"""

import yaml
import urllib
import numpy as np
import itertools

if False:
    config = yaml.safe_load(open("algs/nuclides.yml"))
    with open('algs/nuclides2.yml', 'w') as outfile:
        yaml.dump(config, outfile, default_flow_style=False)
    

    
def lc_read_csv(url):
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:77.0) Gecko/20100101 Firefox/77.0')
    content = urllib.request.urlopen(req)
    return content

def consult(isotope, pr_thres=1, en_thres=50):
    url = 'https://'+'www-nds.iaea.org/relnsd/v0/data?'+'fields=decay_rads&nuclides='+\
           isotope+'&rad_types=g'
    x = lc_read_csv(url).read().decode('utf-8').split("\n")
    lista = []
    for line in x:
        if line != '':
            lista.append(line.split(","))
    # del lista[-2:]
    hue = list(map(list, itertools.zip_longest(*lista, fillvalue=None)))
    
    
    isot = dict()
    for i in hue:
        isot[i[0]] = i[1:]
    
    ener = isot['energy'] = np.array(
        list(map(float, isot['energy']))
    )
    prob = isot['intensity'] = np.array(
        list(map(float, isot['intensity']))
    )
    ener = isot['energy'] = np.array(
        list(map(float, isot['energy']))
    )
    filtro = prob > pr_thres
    ener2 = ener[filtro]
    prob2 = prob[filtro]
    filtro = ener2 > en_thres
    ener2 = ener2[filtro]
    prob2 = prob2[filtro]
    results = np.array([ener2, prob2/100]).T
    reslist = list(map(list, results))
    print(reslist)
    return reslist, hue

consult('131i')
consult('11c')
x = consult('152Eu', 1, 90)[1]