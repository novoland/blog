#!/usr/bin/python
# coding=utf-8

import sys
from bs4 import BeautifulSoup
reload(sys)
sys.setdefaultencoding('utf-8')
from settings import noteList, expire
import sqlite3
import os
import datetime
import re
import urllib
import requests
import hashlib

postDir = '../_posts'
imgDir = '../assets/img'

con = sqlite3.connect("log.db",detect_types=sqlite3.PARSE_DECLTYPES)
con.isolation_level = None
con.text_factory = str
c = con.cursor()
# c.execute('drop table log')
c.execute("create table if not exists log (url varchar(255) primary key,file varchar(255),last_sync_time timestamp, category varchar(255) )")
print "init db successfully"


def sync():
    # 对已有的文件：
    files = [ f for f in os.listdir(postDir) if os.path.isfile(os.path.join(postDir,f)) and f.endswith(".html")]
    for file in files:
        log = c.execute("select * from log where file = ?",(file,)).fetchall()
        # 曾经抓取过，看是否需要重新抓取
        if len(log):
            log = log[0]
            lastSyncTime = log[2]
            url = log[0]
            category = log[3]
            elapsed = (datetime.datetime.now() - lastSyncTime).total_seconds()
            if elapsed >= expire:
                if not capture(url,category,False,file=file):
                    c.execute('delete from log where file = ?',(file,))
                    
        # 没抓取记录，说明这个文件是多余的，删除之
        else:
            # 以下文件不删除：
            # 1. gc.html
            if not re.search('gc\.html',file):
                delete(file)
            pass

    # 对配置的每条笔记
    for category, urls in noteList.items():
        for url in urls:
            url += '?content='
            log = c.execute("select * from log where url = ?",(url,)).fetchall()
            # 如果有抓取记录，则根据过期时间判断是否重新抓取
            if len(log):
                log = log[0]
                lastSyncTime = log[2]
                file = log[1]
                elapsed = (datetime.datetime.now() - lastSyncTime).total_seconds()
                if elapsed >= expire:
                    capture(url,category,False,file=file)
                else:
                    pass
            # 没有，则第一次抓取之
            else:
                capture(url,category,True)

def delete(file):
    os.remove(os.path.join(postDir,file))

def now():
    return datetime.datetime.today()

def log(info):
    print datetime.datetime.today().strftime('[%H:%M:%S]:'), info

def capture(url,category, firstTime, file=None):
    log("sync note: %s, category: %s, firstTime: %s" % (url, category, firstTime))

    log("1. fetching page")
    html = requests.get(url,headers={'referer': url.split('?')[0]}).text

    soup = BeautifulSoup(html)
    body = soup.find("div", class_="ennote")
    
    if not body:
        log('note not exist!')
        return False

    body = body.find('div')

    log("2. downloading images")
    # 将所有保存在 evernote 服务器上的图片抓到本地，其他图片不管
    for img in body.find_all('img'):
        if not re.search('www\.evernote\.com',img['src']):
            continue

        src = img['src']
        suffix = src.split('?')[0].split('.').pop().lower()
        allowedSuffix = set(['png','gif','jpeg','jpg','bmp'])
        if not suffix in allowedSuffix:
            suffix = ''

        imgName = md5(src)
        if suffix != '':
            imgName = imgName + '.' + suffix

        # update img src
        img['src'] = "/assets/img/%s" % imgName

        files = [ f for f in os.listdir(imgDir) if os.path.isfile(os.path.join(imgDir,f)) and f == imgName]
        # 如果本地有图片，不重新抓取
        if len(files) > 0:
            continue
        else:
            # download the image
            urllib.urlretrieve(src, "%s/%s" % (imgDir,imgName))
    
    info = getNoteInfo(body)
    if not file:
        file = info['filename']

    log("3. writing to file %s" % file)

    f = open(os.path.join(postDir, file),"wb")
    f.write("---\n")
    f.write("layout: post\n")
    f.write('title: "%s"\n' % info['title'])
    f.write('category: "%s"\n' % category)
    f.write("---\n\n")

    f.write(str(body))
    f.flush()

    # 记录此次抓取日志
    if not firstTime:
        c.execute('update log set file = ? , last_sync_time = ? where url = ?',(file,datetime.datetime.now(),url))
    else:
        c.execute('insert into log values(?,?,?,?)',(url, file, datetime.datetime.now(), category))

    log("sync done !")
    return True

def getNoteInfo(body):
    title = body.find('h1').extract().contents[0]
    today = datetime.datetime.today().strftime('%Y-%m-%d')
    filename = "%s-%s.html" % (today,title)
    return {'title':title,'filename':filename}

def md5(string):
    return hashlib.md5(string.encode('utf-8')).hexdigest()

if __name__ == '__main__':
    sync()

