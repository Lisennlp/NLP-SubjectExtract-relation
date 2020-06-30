import jieba
import re
import os
import json
import random
import argparse

from tqdm import tqdm
from getSpeech import Speech
from tools import SPEECH_PATH_BASE, BOOK_LIST
from tools import has_speech, getRandomCase


class Relation(Speech):
    def data_init(self, book_name):
        lines = open(SPEECH_PATH_BASE + book_name + '.labeled').read().splitlines()
        part_nr_table = self.load_nr_table(book_name, 4)  # 部分人名表
        nr_table = self.load_nr_table(book_name)
        speeches = {}
        dialog = []
        speakers = []
        last_speaker = ''
        interval_count = 0
        for line in lines:
            interval_count += 1
            data = line.strip().split('::')
            person_name = self.get_person_name(data[0], part_nr_table)
            if (person_name == False): continue
            if (self.is_legal_content(data[1])): continue  # lsp： ？
            if (not has_speech(data[1])): continue
            text = re.findall(r'[‘“](.*?)[’”]', data[1])
            if (text):
                text = '。'.join(text)  # lsp：合并当前人连续说的多句话
            else:
                continue
            if ((not self.has_appellation(text)) and (not dialog)): continue

            if (interval_count > 2):  # lsp： 每提取两个人的并且dialog大于5就存一下
                if (len(dialog) > 5):
                    key = '::'.join(sorted(speakers, reverse=True))
                    if (key in speeches):
                        speeches[key].append(dialog)
                    else:
                        speeches[key] = [dialog]
                speakers, dialog = [], []
                last_speaker = ''
                interval_count = 0
            else:
                interval_count = 0

            text = self.name_hide(text, nr_table, person_name)
            if (person_name in speakers):
                if (last_speaker == person_name):
                    dialog[-1] = dialog[-1] + '。' + text
                else:
                    text = person_name + '>>>' + text
                    dialog.append(text)
                    last_speaker = person_name
            else:
                if (len(speakers) < 2):
                    speakers.append(person_name)
                    text = person_name + '>>>' + text
                    dialog.append(text)
                else:
                    if (len(dialog) > 4):
                        key = '::'.join(sorted(speakers, reverse=True))
                        if (key in speeches):
                            speeches[key].append(dialog)
                        else:
                            speeches[key] = [dialog]
                    text = person_name + '>>>' + text
                    dialog = [text]
                    speakers = [person_name]
                last_speaker = person_name

        res = {}
        speeches_keys = list(speeches.keys())
        tmp = []
        for key in speeches_keys:
            sentences = speeches[key]
            count = 0
            for s in sentences:
                count += len(s)
            if(count>4*k+2*len(sentences)):tmp.append(key)
        speeches_keys = tmp

        # lsp: 判断人名一致性
        for key in speeches_keys:
            A, B = key.split('::')
            # lsp： 下面两行的目的是？
            is_A_in_other_key = [it for it in speeches_keys if (A in it and it != key)]
            is_B_in_other_key = [it for it in speeches_keys if (B in it and it != key)]
            if(is_A_in_other_key or is_B_in_other_key):
                res[key] = speeches[key]
        return res

    # lsp： 以n或nh开头就返回true，包含你我的也返回true 
    def has_appellation(self, speech):
        appellation = ['你', '我']

        for it in appellation:
            if (it in speech):
                return True
        for s in speech.split('。'):
            if ('，' in s):
                begin = s.strip().split('，')[0]
                words = list(jieba.cut(begin))
                if (not words): continue
                postager = self.postagger.postag(words)
                if (postager[0] == 'n' or postager[0] == 'nh'): return True  

        return False

    def __get_AB_dialog(self, name, speech, k):
        """
        k: 对话的句数，其中一句仅一个人的话，因此传入的k为 2 * k
        speech: 两个人的所有对话列表， 但是起始会有人名前缀，如 '张山>>>我今天去爬山了。'
        """
        test = []
        count = 0
        for sentences in speech:
            count += len(sentences)
        while (len(test) < k):
            para = speech[random.randint(0, len(speech) - 1)]
            para_lenth = len(para)
            for i in range(random.randint(0, para_lenth - 3), para_lenth - 1):
                if (para[i].startswith(name)):
                    text = '“{0}”“{1}”'.format(
                        para[i].split('>>>')[1],
                        para[i + 1].split('>>>')[1]
                    )
                    if (text not in test):
                        test.append(text)
                        break

        return test

    def get_test(self, speeches, ans, k, book_list):
        n = len(book_list)
        book_name = book_list[random.randint(0, n - 1)]
        test_info = {
            'book': book_name,
            'ans': str(ans)
        }
        # get the speakers
        book_speech = speeches[book_name]
        key = list(book_speech.keys())[random.randint(0, len(book_speech) - 1)]
        A, B = key.split('::')
        speech = book_speech[key]
        ans = 1
        if (ans):
            if (random.randint(0, 1)):
                test = self.__get_AB_dialog(A, speech, 2 * k)
                test_content = [test[:k], test[k:]]
                test_info['speakers'] = key + '||' + key
            else:
                test_content = []
                test_content.append(self.__get_AB_dialog(A, speech, k))
                test_content.append(self.__get_AB_dialog(B, speech, k))
                test_info['speakers'] = '{0}||{1}::{2}'.format(key, B, A)
        else:
            if(random.randint(0, 1)):
                test_content = [self.__get_AB_dialog(A, speech, k)]
                test_info['speakers'] = key
            else:
                test_content = [self.__get_AB_dialog(B, speech, k)]
                test_info['speakers'] = '{0}::{1}'.format(B, A)
            keys_A = [it for it in list(book_speech.keys())
                    if (A in it and it != key)]
            keys_B = [it for it in list(book_speech.keys())
                    if (B in it and it != key)]
            keys = keys_A if len(keys_A)>len(keys_B) else keys_B
            keys2 = keys[random.randint(0, len(keys) - 1)]
            speech = book_speech[keys2]
            C, D = keys2.split('::')
            if(random.randint(0, 1)):
                test_content.append(self.__get_AB_dialog(C, speech, k))
                test_info['speakers'] = test_info['speakers'] + '||' + keys2
            else:
                test_content.append(self.__get_AB_dialog(D, speech, k))
                test_info['speakers'] = test_info['speakers'] + '||' + '{0}::{1}'.format(D, C)
        return {'info': test_info, 'content': test_content}


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

    model = Relation()

    print('speeches {0}-{1} init start'.format(begin + 1, end))
    # 生成json文件
    N = len(BOOK_LIST)
    speech_save_path = 'data/json/figure_relation/figure_relation_{0}-{1}.json'.format(begin + 1, end)
    if (os.path.exists(speech_save_path)):
        speeches = json.load(open(speech_save_path))
        book_list = list(speeches.keys())
    else:
        speeches = {}
        book_list = BOOK_LIST[begin:end]
        for book_name in tqdm(book_list):
            book_content = model.data_init(book_name)
            if (len(book_content) > 3):speeches[book_name] = book_content
        json.dump(speeches, open(speech_save_path, 'w'))
        book_list = list(speeches.keys())
    print('speeches {0}-{1} completed'.format(begin + 1, end))
    print('speeches {0}-{1} generate {2} cases start'.format(begin + 1, end, n))
    ans = [random.randint(0, 1) for i in range(n)]
    out = open('data/res/figure_relation/figure_relation_%d' % (begin + 1), 'w')
    answers = []
    print(book_list)
    for it in tqdm(ans):
        case = model.get_test(speeches, it, k, book_list)
        record = '{0}\t{1}\t{2}\t{3}\t{4}\n'.format(
            '||'.join(case['content'][0]),
            '||'.join(case['content'][1]),
            case['info']['ans'],
            case['info']['book'],
            case['info']['speakers']
        )
        out.write(record)
    out.close()
    print('speeches {0}-{1} generate {2} cases completed'.format(begin + 1, end, n))
