import jieba
import os
from pyltp import  Postagger, Parser, NamedEntityRecognizer
import re

NR_TABLE_PATH_BASE = '/nas/xd/data/novels/20191108_69shu_novel/nps+anon/'

class Sentence:
    def __init__(self, v):
        self.v = v
        self.coo = None
        self.sbv = None
        self.vob = None

class ExtraModel:
    def __init__(self):
        self.nr_table_name = ''
        self.nrTable = None
        # 词性标注
        pos_model_path = os.path.join(os.path.dirname(__file__), '../data/ltp_data/pos.model')
        self.postagger = Postagger()
        # self.postagger.load(pos_model_path)

        # 依存句法分析
        par_model_path = os.path.join(os.path.dirname(__file__), '../data/ltp_data/parser.model')
        self.parser = Parser()
        self.parser.load(par_model_path)

    def getNrTable(self, book):
        f = open(NR_TABLE_PATH_BASE+book+'.nps.txt')
        data = f.read().splitlines()[1:]
        NrTable = []
        for it in data:
            nr = it.split(',')[0]
            NrTable.append(nr)
        return NrTable

    def loadNrTable(self, book, nrTable=None):
        if(nrTable==None):nrTable = self.getNrTable(book)
        path = 'data/npList/' + book + '.nps.table'
        if(os.path.exists(path)):
            self.postagger.load_with_lexicon('data/ltp_data/pos.model', path)
        else:
            out = open('data/npList/' + book, 'w')
            for nr in nrTable:
                out.write(nr + ' nh\n')
            out.close()
            self.postagger.load_with_lexicon('data/ltp_data/pos.model', path)
        for nr in nrTable:jieba.add_word(nr)
        self.nrTable = nrTable
        self.nr_table_name = book

    def InputWords(self, words):
        postags = self.postagger.postag(words)
        arcs = self.parser.parse(words, postags)
        rely_id = [arc.head for arc in arcs]  # 提取依存父节点id
        relation = [arc.relation for arc in arcs]  # 提取依存关系
        print(words)
        print(list(postags))
        heads = [-1 if id == 0 else id - 1 for id in rely_id]  # 匹配依存父节点词语
        for i, v in enumerate(heads):
            if v == -1:
                return relation, heads, i, postags
        return None

    def addCooNode(self, s, word, sbvlink):
        if(s.coo):
            self.addCooNode(s.coo, word, sbvlink)
        else:
            verb = Sentence(word)
            if(word in sbvlink):
                verb.sbv = sbvlink[word]
            s.coo = verb
        return None

    def addVob(self, s, head, word):
        if(s!=None):
            if(s.v == head):
                s.vob = word
            else:
                self.addVob(s.coo, head, word)
        return None

    def getMainSentence(self, s):
        s = self.DialogFliter(s)
        words = list(jieba.cut(s))
        if(not words):
            return []
        relation, heads, root, postags = self.InputWords(words)
        # print(list(postags))
        stack = [words[root]]
        res = {}
        cooLink = {}
        sbvLink = {}
        n = len(words)
        while(stack):
            hed = stack.pop(0)
            res[words[hed]] = Sentence(words[hed])
            for i in range(n):
                r = relation[i]
                if(r == 'COO'):
                    h = heads[i]
                    w = words[i]
                    if (h in cooLink):
                        h = cooLink[h]
                    if(h == hed and h!=w):
                        self.addCooNode(res[words[h]],w, sbvLink)
                        cooLink[w] = h
                if(r == 'VOB'):
                    h = heads[i]
                    if (h in cooLink):
                        h = cooLink[h]
                    if(h==hed):
                        w = words[i]
                        self.addVob(res[words[h]], words[heads[i]], w)
                        if(postags[i]=='v' and (w not in res)):
                            stack.append(w)
                if(r == 'SBV'):
                    h = heads[i]
                    if(h in cooLink):h = cooLink[h]
                    if(h == hed):
                        verb = res[words[h]]
                        while(verb.v!=heads[i]):verb = verb.coo
                        if(verb.sbv):
                            verb.sbv += words[i]
                        else:
                            verb.sbv = words[i]
                    else:
                        sbvLink[heads[i]] = words[i]
        text = []
        for it in res:
            text.append(self.getSentence(res[it]).replace('\n',''))
        # for i in range(len(words)):
        #     print(relation[i] + '(' + words[i] + ', ' + str(heads[i]) + ')',end='+')
        # print('')
        # print(s, text)
        return text

    def DialogFliter(self, s):
        res = re.sub('[\'\"‘“].*?[’”\'\"]','',s)
        # print(res)
        pos  = re.finditer('::',res)
        content = []
        for it in pos:
            content.append(it.span())
        if(len(content)<2):
            res = res[content[0][1]:]
        else:
            res = res[content[0][1]:content[1][0]]
        return res

    def readCoo(self, s):
        text = ''
        if(s):
            if s.sbv:
                text = s.sbv + text
            text = text + s.v
            if(s.vob):
                text = text + s.vob
            return [text] + self.readCoo(s.coo)
        return [text]

    def getSentence(self, sentence):
        text = []
        # print(sentence)
        if(sentence.vob):
            text.append(sentence.v+sentence.vob)
        else:
            text.append(sentence.v)
        # print(sentence.coo, sentence.v)
        if(sentence.coo):
            text =  text + self.readCoo(sentence.coo)
        text = ','.join(text)
        if (sentence.sbv):
            text = sentence.sbv+text
        else:
            text = '[unknown]' + text
        return text

    def getMain(self, text, book):
        nr = []
        words = list(jieba.cut(text))
        relation, heads, root, postags = self.InputWords(words)
        queue = [root]
        N = len(words)
        while (queue):
            current = queue.pop(0)
            for i in range(N):
                if (heads[i] == current):
                    if (relation[i] == 'SBV' or relation[i] == 'ATT'):
                        if (relation[i] == 'SBV'):
                            nr.append((words[i],re.search(words[i],text).start(),postags[i],1))
                        else:
                            if (words[i] in self.nrTable):
                                nr.append((words[i],re.search(words[i],text).start(),postags[i],1))
                    elif (relation[i] == 'COO'):
                        queue.append(i)
        return nr


if __name__ == '__main__':
    case = '“出去！”王铁雄睁开眼睛，眼中精光迸射，瞪着那黑衣人。'
    book = '神道'
    model = ExtraModel()
    model.loadNrTable(book)
    res = model.getMain(case, book)
    print(res)



