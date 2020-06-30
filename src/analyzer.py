import re
import random
from collections import Counter, defaultdict
from getSpeaker import Speaker, rotarySpeaker
from getTestSet import getRandomCase
from tools import has_speech, is_pure_speech, strip_to_be_continue, is_comment,\
    is_cjk_char, is_chapter_name, BREAKING_LINES, remove_improper_crlf, fix_and_join, \
    MAX_LINE_LEN, BOOK_BASE_PATH



speakerModel = Speaker()
rotaryModel = rotarySpeaker()


class Analyzer:
    def get_speech_stat(self, lines: list):
        n_speeches, pure_speeches = 0, 0
        pure_speech_1, pure_speech_2, pure_speech_3, pure_speech_n = 0, 0, 0, 0
        queue = 0
        for line in lines:
            if has_speech(line):
                n_speeches += 1
                if is_pure_speech(line):
                    pure_speeches += 1
                    queue += 1
                else:
                    if (queue == 1):
                        pure_speech_1 += 1
                    elif (queue == 2):
                        pure_speech_2 += 2
                    elif (queue == 3):
                        pure_speech_3 += 3
                    else:
                        pure_speech_n += queue
                    queue = 0
            else:
                if (queue == 1):
                    pure_speech_1 += 1
                elif (queue == 2):
                    pure_speech_2 += 2
                elif (queue == 3):
                    pure_speech_3 += 3
                else:
                    pure_speech_n += queue
                queue = 0
        # pure_speech_pct = n_pure_speeches / n_speeches if n_speeches > 0 else 1
        # invalid_speech_pct = n_invalid_speeches / n_speeches if n_speeches > 0 else 0
        # speech_pct = n_speeches / len(lines)

        # round float for pretty printing
        # speech_pct = round(speech_pct, 4)
        # pure_speech_pct = round(pure_speech_pct, 4)
        # mean_len = round(mean_len, 1)
        # invalid_speech_pct = round(invalid_speech_pct, 4)
        # return len(lines), mean_len, sum_len, speech_pct, pure_speech_pct, invalid_speech_pct
        return n_speeches, pure_speeches, pure_speech_1, pure_speech_2, pure_speech_3, pure_speech_n

    def filter_lines(self, lines: list, title, fix_invalid_and_join=True):
        lines = [line.replace(' ', '').replace('\t', '').replace('\u3000', '') for line in lines]  # space and CJK space
        lines = [line.replace('?', '') for line in lines]
        lines = [line.strip() for line in lines]
        lines = [strip_to_be_continue(line) for line in lines]
        lines = [line for line in lines if line != '']

        lines = [line for line in lines if not is_comment(line, title) and not is_chapter_name(line, title)]

        counter = Counter(lines)
        recurring_comment_lines = {line: count for line, count in counter.most_common(5)
                                   if count > 100 and '“' not in line and not (
                    len(set(line)) == 1 and line[0] == '…') and line not in BREAKING_LINES}
        # if verbose: print('recurring comment lines:', recurring_comment_lines, flush=False)
        recurring_comment_lines = {line: count for line, count in recurring_comment_lines.items() if
                                   not is_cjk_char(line[0])}
        lines = [line for line in lines if line not in recurring_comment_lines]

        lines = remove_improper_crlf(lines, title)
        if type(lines) == str: return lines, None

        if fix_invalid_and_join:
            lines, n_joined, total_fixed = fix_and_join(lines, title)

        lines = [line for line in lines if len(line) <= MAX_LINE_LEN]
        return lines

    def get_resolved_pure_speech(self, lines: list):
        resolved_pure_speech = 0
        n = 0
        begin = ''
        for line in lines:
            if (is_pure_speech(line)):
                n+=1
            else:
                # print(n,'(',begin,line,')')
                if (n == 1):
                    if (not has_speech(line) and (not has_speech(begin))):
                        resolved_pure_speech += 1
                elif (n == 2):
                    if ((has_speech(begin) and has_speech(line))):
                        resolved_pure_speech += 2
                begin = line
                n = 0
        return resolved_pure_speech

    def pure_speech_analyse(self, lines: list, title=None, fix_invalid_and_join=True):
        n_speeches, pure_speeches, pure_speech_1, pure_speech_2, pure_speech_3, pure_speech_n = self.get_speech_stat(lines)
        pure_speech_pct = round(pure_speeches / n_speeches, 4)
        pure_speech_1_pct = round(pure_speech_1 / n_speeches, 4)
        pure_speech_2_pct = round(pure_speech_2 / n_speeches, 4)
        pure_speech_3_pct = round(pure_speech_3 / n_speeches, 4)
        pure_speech_n_pct = round(pure_speech_n / n_speeches, 4)
        unresolved_pure_speech = pure_speeches - self.get_resolved_pure_speech(lines)
        unsolved_pure_speech_pct = round(unresolved_pure_speech / n_speeches, 4)
        return pure_speech_pct, pure_speech_1_pct, pure_speech_2_pct, pure_speech_3_pct, pure_speech_n_pct, unsolved_pure_speech_pct

    def deal_pure_dialog(self, lines:list, title):
        speeches = []
        begin = ''
        res = []
        for line in lines:
            if(is_pure_speech(line)):
                speeches.append(line)
            else:
                text = {
                    'begin':begin,
                    'end':line,
                    'speech':speeches,
                    'book':title
                }
                if (len(text['speech']) == 1):
                    if (not has_speech(text['begin']) and (not has_speech(text['end']))):
                        res.append(speakerModel.getSpeakers(text))
                elif (len(text['speech']) == 2):
                    if ((has_speech(text['begin']) and has_speech(text['end']))):
                        res.append(rotaryModel.getSpeakers(text))
                speeches = []
                begin = line
        return res

if __name__ == '__main__':
    pass
    # analyzer = Analyzer()
    # source = open(BOOK_BASE_PATH+'test/pure_speech_100.out')
    # book_list = source.read().splitlines()
    # source.close()
    # out_path = 'data/res/speakers2.res'
    # out = open(out_path, 'w')
    # book_list = [it.split(' ')[5] for it in book_list]
    # book_num = len(book_list)
    # res = []
    # for index, book in enumerate(book_list):
    #     lines = open(BOOK_BASE_PATH+book).read().splitlines()
    #     lines = analyzer.filter_lines(lines, book)
    #     res = res + analyzer.deal_pure_dialog(lines, book)
    #     # res = book+' is '+'pure_speech_pct:%.4f, pure_speech_1_pct:%.4f, pure_speech_2_pct:%.4f, pure_speech_3_pct:%.4f, pure_speech_n_pct:%.4f, unsolved_pure_speech_pct:%.4f' % res
    #     # out.write(res+'\n')
    #     print(book+' {0}/{1}'.format(index+1, book_num))
    #     break
    # views = getRandomCase(50, res)
    # print(views)
    # for text in views:
    #     #print(text)
    #     out.write('《{0}》:{1}\n{2}\n{3}\n{4}\n'.format(
    #         text['book'],
    #         text['speakers'],
    #         text['begin'],
    #         '\n'.join(text['speech']),
    #         text['end']
    #     ))
    # out.close()

