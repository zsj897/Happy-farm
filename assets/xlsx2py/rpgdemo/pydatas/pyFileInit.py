# -*- coding: utf-8 -*-
import json

fileName = 'd_card_dis.py.datas.json'
path ='F:\BaiduYunDownload\v0.6.16\kbengine-0.6.16\assets\scripts\cell\card\'

f = open(fileName, encoding='utf-8')
content = json.load(f)
for id in content:
	print('即将写入id:'+id)
	name = 'card_'+str(id)
	 

