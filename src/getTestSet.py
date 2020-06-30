# -*- coding: utf-8 -*-
import re
import os
import random

BASE = '/nas/xd/data/novels/20191108_69shu_novel/'

def not_empty(s):
    return s and s.strip()

def getRandomCase(n, data):
    N = len(data)
    simple = random.sample(range(1, N), n)
    res = []
    for index in simple:
        res.append(data[index])
    return res

def ListFilesToTxt(dir):
    files = os.listdir(dir)
    res = set()
    for name in files:
        if(name.endswith('.labeled')):
            res.add(name[:-8])
    return res

def getPureDialog(path):
    res = []
    f = open(path)
    BookName = f.read().splitlines()
    BOOKNUM = len(BookName)
    f.close()
    for index, book in enumerate(BookName):
        path = BASE + book
        f = open(path)
        data = f.read().splitlines()
        data = list(filter(not_empty,data))
        N = len(data)

        for i in range(1,N-1):
            dialog = data[i].strip()
            # lastFlag, nextFlag = False, False
            lastText, nextText = data[i-1], data[i+1]
            if(re.sub(r'“.*?”','',dialog)==''):
                if(re.search(r'“.*?”', lastText)==None):
                    lastFlag = True
                else:
                    lastFlag = False
                if(re.search(r'“.*?”', nextText)==None):
                    nextFlag = True
                else:
                    nextFlag = False
                if(lastFlag and nextFlag):
                    case = {
                        'dialog':dialog,
                        'begin':lastText,
                        'end':nextText,
                        'book':book
                    }
                    res.append(case)
        print('{0} finish {1} / {2}'.format(book, index+1, BOOKNUM))
    return res

def getRataryDialog(path):
    dialogs = []
    f = open(path)
    BookName = f.read().splitlines()
    BOOKNUM = len(BookName)
    f.close()
    for index in range(BOOKNUM):
        book = BookName[index]
        data = open(BASE+book).read().splitlines()
        data = [it for it in data if it != '']
        queue = []
        begin = ''
        for i, line in enumerate(data):
            if(re.sub(r'\“.*?\”','',line)==''):
                queue.append(line)
            else:
                if(len(queue)==2):
                    dialog = {
                        'begin':begin,
                        'dialogs':queue,
                        'end':line,
                        'book':book
                    }
                    dialogs.append(dialog)
                begin = line
                queue = []
        print('{0} finished {1}/{2}'.format(book,index+1,BOOKNUM))
    return dialogs

if __name__ == '__main__':
    book_list = ListFilesToTxt('/nas/xd/data/novels/20191108_69shu_novel/labeled_b324b72/')
    out = open('data/raw/bookList','w')
    for it in book_list:out.write(it+'\n')
    print (len(book_list))
    # data_path = 'data/raw/rataryDialog'
    # if(not os.path.exists(data_path)):
    #     book_list_path = 'data/raw/bookList'
    #     cases = getRataryDialog(book_list_path)
    #     out = open(data_path, 'w')
    #     for case in cases:
    #         dialogs = '&::&'.join(case['dialogs'])
    #         out.write(case['book'] + '&::&' + case['begin'] + '&::&' + dialogs + '&::&' + case['end'] + '\n')
    #     out.close()
    # else:
    #     cases = []
    #     f = open(data_path)
    #     lines = f.read().splitlines()
    #     for line in lines:
    #         data = line.split('&::&')
    #         book = data.pop(0)
    #         begin = data.pop(0)
    #         end = data.pop()
    #         case = {
    #             'begin': begin,
    #             'dialogs': data,
    #             'end': end,
    #             'book': book
    #         }
    #         cases.append(case)
    # print('the number of two dialog case is %d' % len(cases))
    # case1, case2 = [], []
    # for case in cases:
    #     if(re.search(r'“.*?”',case['begin'])==None and re.search(r'“.*?”',case['end'])==None):
    #         case1.append(case)
    #     elif(re.search(r'“.*?”',case['begin'])!=None and re.search(r'“.*?”',case['end'])!=None):
    #         case2.append(case)
    # print('the number of case1 is {0}, case2 is {1}'.format(len(case1), len(case2)))
    # for i, it in enumerate([case1, case2]):
    #     tests = getRandomCase(500, it)
    #     out = open('data/test/ratary2_'+str(i+1), 'w')
    #     split_tag = '&::&'
    #     for test in tests:
    #         dialogs = split_tag.join(test['dialogs'])
    #         out.write(test['book']  + split_tag +test['begin'] +split_tag+ dialogs +split_tag+ test['end'] + '\n')
    #     out.close()





