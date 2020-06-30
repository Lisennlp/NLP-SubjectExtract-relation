import re
import os
import time
import argparse
import json
import random
import jieba
from tqdm import tqdm
from tools import BOOK_LIST, SPEECH_PATH_BASE, NR_TABLE_PATH_BASE
from tools import has_speech, getRandomCase, is_cjk_char, is_true_np
from pyltp import Postagger

MANY_PEOPLE_NAME = [
    '两个人', '一个', '三人', '此人', '两人', '二人', '众人',
    '男子', '一位', '那人', '男人', '几人', '几个人', '女子', '女人'
]


class Speech:
    def __init__(self):
        self.postagger = Postagger()
        self.postagger.load('data/ltp_data/pos.model')

    # lsp: 根据人名表和相应的规则过滤出一些符合人名的table，然后取了1/4的长度。这个part参数没用到吧？
    def load_nr_table(self, book_name, part=1):
        names_table = open(NR_TABLE_PATH_BASE + book_name + '.nps.txt').read().splitlines()
        names = []
        for name in names_table[1:]:
            info = name.split(',')
            # print(info)
            info[4] = info[4].strip()
            # if(info[4]!='n' and info[4]!='-' and (not info[4].startswith('m+'))):
            if (
                    # info[4] == 'n' or
                    # info[4].startswith('m') or
                    # info[4].startswith('r') or
                    # info[4].startswith('zhe') or
                    # info[4].startswith('na')
                    info[4] == 'np' or
                    info[4].startswith('np+') or
                    info[4].startswith('n+') or
                    info[4].startswith('v') or
                    info[4].startswith('h') or
                    info[4].startswith('a')
            ):
                if(info[0][-1] not in ['人', '男', '女', '们', ]):
                    names.append(info[0])
            # names.append(info[0]+':'+info[4])

        n = int(len(names) / 4)  # lsp: 这里的4应该是part
        names = [name for name in names[:n] if is_true_np(name)]
        return names[:n]

    # lsp: 这个if也太多了，可以简单些
    def get_person_name(self, text, nr_table):
        if (text == 'None' or text == 'mental'): return False
        if (',' in text): return False
        if ('<-' in text): return False
        if (':' in text): return False
        name = text
        if (name[0] == '?'): return False
        if (name not in nr_table): return False
        if (name in MANY_PEOPLE_NAME): return False
        return name

    def is_legal_content(self, text):
        flag = False
        speech = re.search(r'".*?"', text)
        if (speech == None): return flag
        for w in speech.group():
            if (is_cjk_char(w)):
                flag = True
                break
        return flag

    def data_init(self, book_name):
        lines = open(SPEECH_PATH_BASE + book_name + '.labeled').read().splitlines()
        part_nr_table = self.load_nr_table(book_name, 4)
        nr_table = self.load_nr_table(book_name)
        speeches = {}
        for line in lines:
            data = line.split('::')
            person_name = self.get_person_name(data[0], part_nr_table)
            if (person_name == False): continue
            if (self.is_legal_content(data[1])): continue
            text = data[1]
            if (not has_speech(text)): continue
            if (person_name not in speeches): speeches[person_name] = []
            text = self.name_hide(text, nr_table, person_name)
            speeches[person_name].append(text)
        res = {}
        for it in speeches:
            if (len(speeches[it]) > 40): res[it] = speeches[it]
        return res

    def name_hide(self, text, nr_table, speaker):
        pron_table = ['他', '她', '它']
        nr_table = list(set(nr_table).difference(set(pron_table)))
        res = text
        try:
            res = re.sub(speaker, 'OO', res)
        except Exception:
            print('"{0}" failed hide in "{1}"'.format(speaker, res))
        for name in pron_table:
            try:
                res = re.sub(name, 'TA', res)
            except Exception:
                print('"{0}" failed hide in "{1}"'.format(name, res))
        for name in nr_table:
            try:
                res = re.sub(name, 'XX', res)
            except Exception:
                print('"{0}" failed hide in "{1}"'.format(name, res))

        words = list(jieba.cut(res))
        postager = self.postagger.postag(words)
        for i in range(len(postager)):
            try:
                if (postager[i] == 'nh'):
                    res = re.sub(words[i], 'XX', res)
            except Exception:
                print('"{0}" failed hide in "{1}"'.format(words[i], res))
        return res

    def get_test(self, speeches, ans, k, book_list):
        N = len(book_list)
        if (ans):
            book_name = book_list[random.randint(0, N - 1)]
            book_speech = speeches[book_name]
            person_name = list(book_speech.keys())[random.randint(0, len(book_speech) - 1)]
            speech = book_speech[person_name]
            test = getRandomCase(2 * k, speech)
            test_info = {
                'book': book_name,
                'ans': str(ans),
                'speaker': person_name
            }
            test_content = [test[:k], test[k:]]
        else:
            a, b = book_list[random.randint(0, N - 1)], book_list[random.randint(0, N - 1)]
            is_same_book = random.randint(0, 1)
            book_speech_a = speeches[a]
            if (is_same_book):
                book_speech_b = speeches[a]
                book_name = a
                a, b = random.sample(range(1, len(book_speech_a)), 2)
            else:
                book_speech_b = speeches[b]
                book_name = '{0}+{1}'.format(a, b)
                a, b = random.randint(0, len(book_speech_a) - 1), random.randint(0, len(book_speech_b) - 1)
            # print(a, b, len(list(book_speech_a.keys())), len(list(book_speech_b.keys())))
            speech_a, speeche_b = list(book_speech_a.keys())[a], list(book_speech_b.keys())[b]
            test_info = {
                'book': book_name,
                'ans': str(ans) + '+' + str(is_same_book),
                'speaker': '{0}+{1}'.format(speech_a, speeche_b)
            }

            test_content = [getRandomCase(k, book_speech_a[speech_a]), getRandomCase(k, book_speech_b[speeche_b])]
        return {'info': test_info, 'content': test_content}


speeches_save_path = 'data/json/figure_speeches/'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-k', type=int, default=5)
    parser.add_argument('-s', type=int, default=0)
    parser.add_argument('-w', type=int, default=10)
    parser.add_argument('-n', type=int, default=5)
    args = parser.parse_args()

    k = args.k
    begin = args.s
    width = args.w
    n = args.n
    end = begin + width

    model = Speech()

    if (end > len(BOOK_LIST)): end = len(BOOK_LIST)
    print('speeches {0}-{1} init start'.format(begin + 1, end))
    # 生成json文件
    N = len(BOOK_LIST)
    if (os.path.exists(speeches_save_path + 'books_speeches_{0}-{1}.json'.format(begin, end))):
        speeches = json.load(open(speeches_save_path + 'books_speeches_{0}-{1}.json'.format(begin, end)))
        book_list = open('data/raw/figure_speech/bookList_{0}-{1}'.format(begin + 1, end)).read().splitlines()
    else:
        speeches = {}
        book_list = BOOK_LIST[begin:end]
        for i, book_name in enumerate(tqdm(book_list)):
            book_content = model.data_init(book_name)
            if (len(book_content) > 3): speeches[book_name] = book_content
        if(not speeches):
            print('No suitable case')
            exit(0)
        json.dump(speeches, open(speeches_save_path + 'books_speeches_{0}-{1}.json'.format(begin, end), 'w'))
        out = open('data/raw/figure_speech/bookList_{0}-{1}'.format(begin + 1, end), 'w')
        for it in speeches.keys(): out.write(it + '\n')
        book_list = list(speeches.keys())
        out.close()
    print('speeches {0}-{1} completed'.format(begin + 1, end))

    print('speeches {0}-{1} generate {2} cases start'.format(begin + 1, end, n))
    ans = [random.randint(0, 1) for i in range(n)]
    out = open('data/res/speech_labeled/speech_labeled_%d' % begin, 'w')
    # out = open('data/res/speech_labeled/speech_labeled_all', 'w')
    for it in tqdm(ans):
        case = model.get_test(speeches, it, k, book_list)
        record = '{0}\t{1}\t{2}\t{3}\n'.format(
            '||'.join(case['content'][0]),
            '||'.join(case['content'][1]),
            case['info']['ans'][0],
            case['info']['book']
        )
        out.write(record)
    out.close()
    print('speeches {0}-{1} generate {2} cases completed'.format(begin + 1, end, n))

    # 直接导入文本
    # out = open('data/res/speech_test.res', 'w')
    # for i, it in enumerate(ans):
    #     case = model.get_test(speeches, it, 5)
    #     out.write('----case %d-----\n' % (i+1))
    #     for content in case:
    #         for j,speech in enumerate(content):
    #             out.write('{0}. {1}\n'.format(j+1,speech))
    #         out.write('==============================\n')
    # out.write('\n\n\n\n\nthe answers is %s' % ','.join([str(it) for it in ans]))
