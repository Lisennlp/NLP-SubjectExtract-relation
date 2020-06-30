import jieba
import os
from pyltp import Postagger, Parser, NamedEntityRecognizer
import re
from getTestSet import getRandomCase

NR_TABLE_PATH_BASE = '/nas/xd/data/novels/20191108_69shu_novel/nps+anon/'


class Speaker:
    def __init__(self):
        self.nr_table_name = ''
        # 词性标注
        self.postagger = Postagger()
        self.postagger.load('data/ltp_data/pos.model')

        # 依存句法分析
        self.parser = Parser()
        self.parser.load('data/ltp_data/parser.model')

        self.faker_speakers = open('data/model_data/fake_speakers').read().strip().split(',')

    def getNouns(self, nouns):
        npList = open(nouns).read().splitlines()
        npList = npList[1:]
        for np in npList:
            jieba.add_word(np.split(',')[0].strip())

    def getNrSet(self, path):
        f = open(NR_TABLE_PATH_BASE + path + '.nps.txt')
        data = f.read().splitlines()[1:]
        nrSet = []
        for it in data:
            nr = it.split(',')[0]
            nrSet.append(nr)
        return nrSet

    def loadNrTable(self, nrSet, book):
        path = 'data/npList/' + book + '.nps.table'
        if (not os.path.exists(path)):
            out = open(path, 'w')
            for nr in nrSet:
                out.write(nr + ' nh\n')
            out.close()
        self.postagger.load_with_lexicon('data/ltp_data/pos.model', path)
        for nr in nrSet: jieba.add_word(nr)
        self.nr_table_name = book

    def generate(self, lines):
        res = []
        for line in lines:
            data = line.strip().split('&::&')
            book = data.pop(0)
            begin = data.pop(0)
            end = data.pop()
            case = {
                'begin': begin,
                'dialog': data,
                'end': end,
                'book': book
            }
            res.append(case)
        return res

    def InputWords(self, words):
        postags = self.postagger.postag(words)
        arcs = self.parser.parse(words, postags)
        rely_id = [arc.head for arc in arcs]  # 提取依存父节点id
        relation = [arc.relation for arc in arcs]  # 提取依存关系
        heads = [-1 if id == 0 else id - 1 for id in rely_id]  # 匹配依存父节点词语
        for i, v in enumerate(heads):
            if v == -1:
                return relation, heads, i, postags
        # print(words)
        return None

    def headmatch(self, text, nrSet):
        text = re.sub('[\'\"‘“].*?[’”\'\"]', '', text)
        patern = r',|\.|;|\?|？|!|\^|，|。|；|！| |…'
        text = re.split(patern, text)
        res = []
        for it in text:
            for nr in nrSet:
                if it.startswith(nr):
                    res.append(nr)
        return sorted(list(set(res)), key=res.index)

    def LtpAnalytic(self, text, nrSet):
        nr = []
        s = re.sub('[\'\"“].*?[”\'\"]', '', text)
        words = list(jieba.cut(s))
        relation, heads, root, postags = self.InputWords(words)
        # for i in range(len(words)):
        #     print(relation[i] + '(' + words[i] + ', ' + words[heads[i]] + ')', end=' ')
        # print('')
        queue = [root]
        N = len(words)
        for i in range(N):
            if (postags[i] == 'nh'):
                nr.append(words[i])
        while (queue):
            current = queue.pop(0)
            for i in range(N):
                if (heads[i] == current):
                    if (relation[i] == 'SBV' or relation[i] == 'ATT'):
                        if (relation[i] == 'SBV'):
                            nr.append(words[i])
                        else:
                            if (words[i] in nrSet or postags[i] == 'nh'):
                                nr.append(words[i])
                    elif (relation[i] == 'COO' or relation[i] == 'SBV'):
                        queue.append(i)
        nr = [it for it in nr if nr not in self.faker_speakers]
        return sorted(list(set(nr)), key=nr.index)

    def getSpeakers(self, text):
        nrSet = self.getNrSet(text['book'])
        nr = self.headmatch(text['end'], nrSet)
        if (not nr): nr = self.headmatch(text['begin'], nrSet)
        if (not nr):
            if (self.nr_table_name != text['book']): self.loadNrTable(nrSet, text['book'])
            if (text['end']):
                nr = self.LtpAnalytic(text['end'], nrSet)
            if (text['begin'] and (not nr)):
                nr = self.LtpAnalytic(text['begin'], nrSet)
        text['speakers'] = nr
        return text

    def getManySpeakers(self, data):
        data = self.generate(data)
        return [self.getSpeakers(it) for it in data]


class rotarySpeaker(Speaker):
    def getSpeakers(self, text):
        nrSet = self.getNrSet(text['book'])
        nr1 = self.headmatch(text['begin'], nrSet)
        nr2 = self.headmatch(text['end'], nrSet)
        if (self.nr_table_name != text['book']): self.loadNrTable(nrSet, text['book'])
        nr = nr1 + nr2
        nr = sorted(list(set(nr)), key=nr.index)
        if (len(nr) < 2):
            if (not nr1):
                for it in self.LtpAnalytic(text['begin'], nrSet):
                    if (it not in nr): nr.append(it)
                    if (len(nr) > 1): break
            if (not nr2):
                for it in self.LtpAnalytic(text['end'], nrSet):
                    if (it not in nr): nr.append(it)
                    if (len(nr) > 1): break
        if (len(nr) < 2):
            if (nr1):
                for it in self.LtpAnalytic(text['begin'], nrSet):
                    if (it not in nr): nr.append(it)
                    if (len(nr) > 1): break
            if (nr2):
                for it in self.LtpAnalytic(text['end'], nrSet):
                    if (it not in nr): nr.append(it)
                    if (len(nr) > 1): break
        if nr:
            text['speakers'] = nr
        else:
            text['speakers'] = None
        return text


if __name__ == '__main__':
    case = '这个真的不能忍，他于是摇头'
    book = '世界第一第二第三都是我'
    model = Speaker()
    model.loadNrTable(book)
    res = model.getMain(case, book)
    print(res)
    # pass
    # model = rotarySpeaker()
    # f = open('data/test/ratary2_1')
    # # f = open('data/test/TestSet_part')
    # data = f.read().splitlines()
    # cases = [it for it in model.getManySpeakers(data) if it['speakers']]
    # # print(cases[0]['speakers'])
    # print('the number of case is %d' % len(cases))
    # cases = getRandomCase(100, cases)
    # out = open('data/res/speaker_part','w')
    # for case in cases:
    #     speaksers = case['speakers']
    #     n = len(speaksers)
    #     if(n==0):
    #         out.write('《'+case['book']+'》')
    #         out.write('[unknown]:\n')
    #         out.write(case['begin']+'\n')
    #         out.write('\n'.join(case['dialog'])+'\n')
    #         out.write(case['end']+'\n')
    #     elif(n==1):
    #         out.write('《' + case['book'] + '》')
    #         out.write(speaksers[0]+':\n')
    #         out.write(case['begin']+'\n')
    #         out.write('\n'.join(case['dialog'])+'\n')
    #         out.write(case['end']+'\n')
    #     else:
    #         out.write('《' + case['book'] + '》')
    #         speaksers = '+'.join(speaksers)
    #         out.write(speaksers + ':\n')
    #         out.write(case['begin'] + '\n')
    #         out.write('\n'.join(case['dialog']) + '\n')
    #         out.write(case['end'] + '\n')
    # out.close()
