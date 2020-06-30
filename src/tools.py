import re
import random
from collections import Counter, defaultdict
from np_stoplist import stop_nps

BOOK_BASE_PATH = '/nas/xd/data/novels/20191108_69shu_novel/'
BOOK_LIST_PATH = 'data/raw/bookList'
BOOK_LIST = open(BOOK_LIST_PATH).read().splitlines()
SPEECH_PATH_BASE = '/nas/xd/data/novels/20191108_69shu_novel/labeled_b324b72/'
NR_TABLE_PATH_BASE = '/nas/xd/data/novels/20191108_69shu_novel/nps+anon/'

BREAKING_LINES = ['…', '—', '——', '-', '--', '**']
MAX_LINE_LEN = 512
MAX_AVG_LINE_LEN = 60
BEFORE_SUBJ_SYMBOLS = [
    '，', '。', '？', '！', '：', '；', '……',
    '…', '——', '—', '~', '～', '-', '－',
    ',', '.', '?', '!', ':', ';'
]
PUNCTUATIONS = set(BEFORE_SUBJ_SYMBOLS + ['“', '”'] + ['"']) - {'.'}
CHAPTER_PATTERN = re.compile(r'第[0-9零一二三四五六七八九十百千]+章')
CHAPTER_PATTERN2 = re.compile(r'^[0-9零一二三四五六七八九十百千]+$')
CHAPTER_PATTERN3 = re.compile(r'^[0-9]')
FALSE_SINGLE_CHAR_SPEAKERS = set('脸头口嘴手腿脚身心话这那')

FALSE_SPEAKERS = open('data/npList/false_speakers.txt', 'r').read().strip().split(', ')
FALSE_SPEAKERS = set(FALSE_SPEAKERS)


def maybe_false_speaker(speaker):
    return speaker in FALSE_SPEAKERS or speaker in stop_nps['n'] or speaker in FALSE_SINGLE_CHAR_SPEAKERS


def is_true_np(np):
    return not maybe_false_speaker(np) and np not in ['一个', '一名', '一位', '一只', '一头', '一阵', '一道'] + ['一声']


def is_comment(line, title):
    beginning = line[:10].lower()
    b = beginning.startswith('ps') or beginning.startswith('pps') or '月票' in line or \
        beginning[1:].startswith('ps') or beginning[1:].startswith('pps') or \
        any(line.startswith(s) for s in ['（', '(']) and line[-1] == line[0]
    return b


def has_invalid_speech(line):
    b = ('“' in line or '”' in line) and (line.count('“') != line.count('”') or line.find('“') > line.find('”'))
    return b


def is_cjk_char(char):
    return '\u4e00' <= char <= '\u9fff'


def remove_improper_crlf(lines, title, k=5):
    lengths = [len(line) for line in lines if is_cjk_char(line[-1]) and len(line) >= 20]
    if len(lengths) == 0: return lines
    top_lengths = Counter(lengths).most_common(k + 3)
    top1_count = top_lengths[0][1]
    topk_count = top_lengths[k - 1][1] if len(top_lengths) >= k else 1
    total_count = sum(count for length, count in top_lengths[:k])
    if total_count / len(lines) >= 0.05 and total_count / len(
            lengths) >= 0.4 and top1_count >= 100 and top1_count > topk_count * 2:
        return 'improper_crlf: %s %.4f %.4f' % (str(top_lengths), total_count / len(lengths), total_count / len(lines))
    else:
        return lines


def has_speech(line):
    return '“' in line and any(s + '”' in line for s in BEFORE_SUBJ_SYMBOLS)


def is_pure_speech(line):
    if line is None: return False  # None returned by get()
    return line[0] == '“' and line[-1] == '”' and '“' not in line[1: -1] and '”' not in line[1: -1]


def fix_and_join(lines, title=None):
    total_fixed = defaultdict(int)
    for i, line in enumerate(lines):
        if line.count("”") == 1 and line.count("“") == 1 and line.find("”") < line.find("“"):
            lines[i] = line.replace("”", "\n").replace("“", "”").replace("\n", "“")
            total_fixed['reversed'] += 1
        elif line.count("”") == 2 and line.count("“") == 0:
            first_quote_idx = line.find('”')
            lines[i] = line[: first_quote_idx] + '“' + line[first_quote_idx + 1:]
            total_fixed['both close'] += 1
        elif line.count("“") == 2 and line.count("”") == 0:
            last_quote_idx = line.rfind('“')
            lines[i] = line[: last_quote_idx] + '”' + line[last_quote_idx + 1:]
            total_fixed['both open'] += 1

    joined = [False for i in range(len(lines))]
    for i in range(len(lines)):
        last_lquote_idx = lines[i].rfind("“")
        if last_lquote_idx != -1 and "”" not in lines[i][last_lquote_idx:] and \
                (last_lquote_idx == 0 or lines[i][last_lquote_idx - 1] in BEFORE_SUBJ_SYMBOLS):
            for j in range(i + 1, min(len(lines), i + 1 + 5)):
                if '”' in lines[j] and '“' not in lines[j].split('”')[0]:
                    for m in range(i, j):
                        joined[m] = True
                if '”' in lines[j] or '“' in lines[j]:
                    break
    out = ''.join([line + ('' if i == len(lines) - 1 or joined[i] else '\n') for i, line in enumerate(lines)])
    n_joined = sum(joined)
    out = out.replace('：\n“', '：“')
    return out.split('\n'), n_joined, total_fixed


def strip_to_be_continue(line):
    indexes = [line.find(s) for s in ['(未完', '（未完', '(待续', '（待续']]
    indexes = [i for i in indexes if i >= 0]
    if len(indexes) == 0:
        return line
    return line[: min(indexes)]


def is_chapter_name(line, title):
    b = re.search(CHAPTER_PATTERN, line) is not None or \
        re.search(CHAPTER_PATTERN2, line) is not None or \
        re.search(CHAPTER_PATTERN3, line) is not None and not line.endswith('。')
    return b


def getRandomCase(n, data):
    N = len(data)
    sample = random.sample(range(1, N), n)
    return [data[index] for index in sample]
