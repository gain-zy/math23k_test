#-*-encoding=utf8-*-
import numpy as np
import json
import copy
from stanfordcorenlp import StanfordCoreNLP
import time
import math
import codecs
import re
from parameter import *
from pre_data import *

import os

print("start")
if "17NLG" in os.getcwd():
    nlp = StanfordCoreNLP(r'../../stanford/stanford-corenlp-4.2.0', lang='zh')#your Stanford CoreNLP folder path
else:
    nlp = StanfordCoreNLP(r'../../stanford/stanford-corenlp-4.2.0', lang='zh')#your Stanford CoreNLP folder path


sentence = '2020吉祥文化金银币正式发行。'
#print(sentence)
print(nlp.word_tokenize(sentence))
#print(nlp.pos_tag(sentence))
#print(nlp.ner(sentence))
#print(nlp.parse(sentence))
print(nlp.dependency_parse(sentence))
#['2020', '吉祥', '文化', '金', '银币', '正式', '发行', '。']
#[('2020', 'CD'), ('吉祥', 'NN'), ('文化', 'NN'), ('金', 'JJ'), ('银币', 'NN'), ('正式', 'AD'), ('发行', 'VV'), ('。', 'PU')]
#[('2020', 'NUMBER'), ('吉祥', 'MISC'), ('文化', 'MISC'), ('金', 'MISC'), ('银币', 'MISC'), ('正式', 'O'), ('发行', 'O'), ('。', 'O')]
#[('ROOT', 0, 7), ('dep', 3, 1), ('compound:nn', 3, 2), ('compound:nn', 5, 3), ('amod', 5, 4), ('nsubj', 7, 5), ('advmod', 7, 6), ('punct', 7, 8)]


def generate_stanford_group():

    with open("data/Math_23K_processed.json",'r') as f1:
        group = json.load(f1)
    f = open("data/Math_23K.json",'r')
    js = ""
    data = []
    g_id=0
    for i, s in enumerate(f):
        js += s
        i += 1
        if i % 7 == 0:  # every 7 line is a json
            data_d = json.loads(js)
            question, equation, answer = data_d['segmented_text'].strip(), data_d['equation'], data_d['ans']            
            equation = equation.replace('"千米/小时"', '')
            if equation[:2] == 'x=':
                equation = equation[2:]
            js = ""
            
            question = question.replace('%', '/100')
            id_=data_d['id']
            g=group[g_id]
            if id_==g["id"]:
            	print("*****************************")
            	print(question)
            	ques_list=question.split()
            	temp_list=[]
            	for id_temp, word_ in enumerate(ques_list):
            		temp_list.append((word_,id_temp))
            	print(temp_list)
            	print(g["group_num"])
            	print(nlp.pos_tag(question))
            	print(nlp.ner(question))
            	print(nlp.dependency_parse(question))
            else:
                print("wrong")
            g_id+=1


def load_Math23K_id(filename):  # load the json data to list(dict()) for MATH 23K
    print("Reading lines...")
    f = open(filename,'r')
    js = ""
    data = []
    for i, s in enumerate(f):
        js += s
        i += 1
        if i % 7 == 0:  # every 7 line is a json
            data_d = json.loads(js)
                
            question, equation, answer,id_ = data_d['segmented_text'].strip(), data_d['equation'], data_d['ans'],data_d['id']
            
            equation = equation.replace('"千米/小时"', '')
            if equation[:2] == 'x=':
                equation = equation[2:]
            js = ""
            #try:
            #    if is_equal(eval(equation), eval(answer)):
            data.append((question, equation, answer,id_))
            #    else:
            #        print(equation)
            #        print(answer)
            #        print(eval(equation))
            #except:
            #    continue
    return data

def transfer_num_id(data):  # transfer num into "NUM"
    print("Transfer numbers...")
    pattern = re.compile("\d*\(\d+/\d+\)\d*|\d+\.\d+%?|\d+%?|\d*\(?\d*\.?\d+/\d+\)?\d*")
    pairs = []
    generate_nums = []
    generate_nums_dict = {}
    copy_nums = 0
    count_empty=0

    UNK2word_vocab={}
    input1=open("data//UNK2word_vocab","r").readlines()
    for word in input1:
        UNK2word_vocab[word.strip().split("###")[0]]=word.strip().split("###")[1]
    count_too_lang=0
    exp_too_lang=0
    for d in data:
        nums = []
        input_seq = []
        seg_line = d[0].strip()
        for UNK_word in UNK2word_vocab:
            if UNK_word in seg_line:
                seg_line=seg_line.replace(UNK_word,UNK2word_vocab[UNK_word])
        seg=seg_line.split(" ")
        equations = d[1]
        group=d[3]

        for s in seg:
            pos = re.search(pattern, s)
            if pos and pos.start() == 0:
                nums.append(s[pos.start(): pos.end()])
                input_seq.append("NUM")
                if pos.end() < len(s):
                    input_seq.append(s[pos.end():])
            else:
                if len(s)>0:
                    input_seq.append(s)
                else:
                    count_empty=count_empty+1
        if copy_nums < len(nums):
            copy_nums = len(nums)


        num_pos = []
        for i, j in enumerate(input_seq):
            if j == "NUM":
                num_pos.append(i)
        assert len(nums) == len(num_pos)

        if len(input_seq) > Max_Question_len :
            count_too_lang+=1
            continue

        nums_fraction = []

        for num in nums:
            if re.search("\d*\(\d+/\d+\)\d*|\d*\(\d+\.\d+/\d+\)\d*", num):
                nums_fraction.append(num)
        nums_fraction = sorted(nums_fraction, key=lambda x: len(x), reverse=True)

        def seg_and_tag(st):  # seg the equation and tag the num
            res = []
            for n in nums_fraction:
                if n in st:
                    p_start = st.find(n)
                    p_end = p_start + len(n)
                    if p_start > 0:
                        res += seg_and_tag(st[:p_start])
                    if nums.count(n) >= 1:
                        res.append("N"+str(nums.index(n)))
                    else:
                        res.append(n)
                    if p_end < len(st):
                        res += seg_and_tag(st[p_end:])
                    return res
                elif n[0]=='(' and n[-1] ==')':
                    n_1=n[1:-1]
                    if n_1 in st:
                        p_start = st.find(n_1)
                        p_end = p_start + len(n_1)
                        if p_start > 0:
                            res += seg_and_tag(st[:p_start])
                        if nums.count(n) >= 1:
                            res.append("N"+str(nums.index(n)))
                        else:
                            res.append(n)
                        if p_end < len(st):
                            res += seg_and_tag(st[p_end:])
                        return res
            pos_st = re.search("\d+\.\d+%?|\d+%?", st)
            if pos_st:
                p_start = pos_st.start()
                p_end = pos_st.end()
                if p_start > 0:
                    res += seg_and_tag(st[:p_start])
                st_num = st[p_start:p_end]
                if nums.count(st_num) == 1:
                    res.append("N"+str(nums.index(st_num)))
                else:
                    res.append(st_num)
                if p_end < len(st):
                    res += seg_and_tag(st[p_end:])
                return res
            for ss in st:
                res.append(ss)
            return res

        out_seq = seg_and_tag(equations)
        for s in out_seq:  # tag the num which is generated
            if s[0].isdigit() and s not in generate_nums and s not in nums:
                generate_nums.append(s)
                generate_nums_dict[s] = 0
            if s in generate_nums and s not in nums:
                generate_nums_dict[s] = generate_nums_dict[s] + 1

        if USE_just_char_number==True:
            realnum_input=[]
            realnum_pos=[]
            prob_start=0
            for i in range(len(num_pos)):
                num_index=num_pos[i]
                realnum_input.extend(input_seq[prob_start:num_index])
                realnum_pos.append(len(realnum_input))
                prob_start=num_index+1
                num_word=nums[i]
                for num_char in num_word:
                    realnum_input.append(num_char)
            realnum_input.extend(input_seq[prob_start:])
        # pairs.append((input_seq, out_seq, nums, num_pos, d["ans"]))
        if len(out_seq) >0:
            if len(out_seq)> Max_Expression_len:
                exp_too_lang+=1
            else:
                if USE_just_char_number==True:
                    pairs.append((realnum_input, out_seq, nums, realnum_pos,group))
                else:
                    pairs.append((input_seq, out_seq, nums, num_pos,group))
    print("count_empty")
    print(count_empty)
    print("data_set_size is %d, num of exp>60  is %d,about %.4f" %(len(pairs),exp_too_lang,float(exp_too_lang)/len(pairs)))
    print("data_set_size is %d, num of problem>150  is %d,about %.4f" %(len(pairs),count_too_lang,float(count_too_lang)/len(pairs)))

    if dataset=="APE":
        orderList=list(generate_nums_dict.values())  
        orderList.sort(reverse=True)  
        max_order_list=orderList[0:10]
        min_generate_vocab_appear=max_order_list[-1]
        temp_g = []
        for g in generate_nums:
            if generate_nums_dict[g] >= min_generate_vocab_appear:
                temp_g.append(g)
        print("generate_num size is %d" %(len(temp_g)))
        print("min_generate_vocab_appear times is %d" %(min_generate_vocab_appear))
    else:
        temp_g = []
        for g in generate_nums:
            if generate_nums_dict[g] >= 5:
                temp_g.append(g)
    return pairs, temp_g, copy_nums



train_data = load_Math23K_id('data/Math_23K.json')
pairs, generate_nums, copy_nums = transfer_num_id(train_data)

temp_pairs = []
for p in pairs:
    temp_pairs.append((p[0], from_infix_to_prefix(p[1]), p[2], p[3],p[4]))
pairs = temp_pairs


def generate_group_num(seq_list,num_pos):
    punc_list=[",","：","；","？","！","，","“","”",",",".","?","，","。","？","．","；","｡"]
    group_this=[]
    #seq_list=pair[0]
    #id_=pair[4]
    #num_pos=pair[3]
    max_seq=len(seq_list)
    for num_id in num_pos:
        if seq_list[num_id]=="NUM":
            if num_id-2>=0 and seq_list[num_id-2] not in punc_list:
                group_this.append(num_id-2)
            if num_id-1>=0 and seq_list[num_id-1] not in punc_list:
                group_this.append(num_id-1)
            group_this.append(num_id)
            if num_id+1<max_seq and seq_list[num_id+1] not in punc_list:
                group_this.append(num_id+1)
            if num_id+2<max_seq and seq_list[num_id+2] not in punc_list:
                group_this.append(num_id+2)
    last_punc=0
    for id_ in range(0, max_seq-1):
        if seq_list[id_] in punc_list:
            if id_ >last_punc:
                last_punc=id_
    keyword_list=["多","少","多少"]
    for num_id in range(last_punc+1,max_seq):
        if seq_list[num_id] in keyword_list:
            if num_id-2>=0 and seq_list[num_id-2] not in punc_list:
                group_this.append(num_id-2)
            if num_id-1>=0 and seq_list[num_id-1] not in punc_list:
                group_this.append(num_id-1)
            group_this.append(num_id)
            if num_id+1<max_seq and seq_list[num_id+1] not in punc_list:
                group_this.append(num_id+1)
            if num_id+2<max_seq and seq_list[num_id+2] not in punc_list:
                group_this.append(num_id+2)
    return group_this

group_list=[]
edge_list=[]
punc_list=[",","：","；","？","！","，","“","”",",",".","?","，","。","？","．","；","｡"]

depen_vocab=[]

pair_id=0
for pair in pairs:
    if pair_id%100==0:
        print(pair_id)
    pair_id+=1
    group_this=[]
    seq_list=pair[0]
    #id_=pair[4]
    num_pos=pair[3]
    max_seq=len(seq_list)

    if "%" in seq_list:
        for i in range(len(seq_list)):
            if seq_list[i] =="%":
                seq_list[i]="百分号"
        print(seq_list)

    seq_line=" ".join(seq_list)
    if pair_id<100:
        print(seq_line)
    dep_list=nlp.dependency_parse(seq_line)
    parse_word_list=nlp.word_tokenize(seq_line)
    word_match_list={}

    ori_len=len(seq_list[0])
    parse_len=0
    ori_id=0
    for parse_id in range(len(parse_word_list)):
        parse_len+=len(parse_word_list[parse_id])

        if parse_len<=ori_len:
            word_match_list[parse_id+1]=ori_id
        else:
            ori_id+=1
            ori_len+=len(seq_list[ori_id])
            while parse_len> ori_len:
                ori_id+=1
                ori_len+=len(seq_list[ori_id])
            if parse_len<=ori_len:
                word_match_list[parse_id+1]=ori_id
            else:
                print("wrong")
                word_match_list[parse_id+1]=ori_id

    list_dependency=[]
    if pair_id<100:
        print(parse_word_list)
        print(word_match_list)
        print(dep_list)
    for id_ in range(len(dep_list)):
        if dep_list[id_][0]!="ROOT":
            # no ('ROOT', 0, 21)
            tuple_dep=dep_list[id_]
            if tuple_dep[0] not in depen_vocab:
                depen_vocab.append(tuple_dep[0])
                print(depen_vocab)

            id_1=dep_list[id_][1]
            #dep_list[id_][1]=word_match_list[id_1]
            id_2=dep_list[id_][2]
            #dep_list[id_][2]=word_match_list[id_2]
            list_this=[tuple_dep[0],word_match_list[id_1],word_match_list[id_2]]
            list_dependency.append(list_this)

    group_this=generate_group_num(pair[0],pair[3])


    if pair_id<100:
        print(list_dependency)
    #print(batch_graph)
    #
    #annotate=nlp.annotate(" ".join(seq_list))
    #print(annotate)
    #cate_graph=[cate_word_edge,cate_index_input,cate_id_match,cate_length,cate_word_edge_dis]
    group={"id":pair[4],"group_this":group_this}
    edge={"id":pair[4],"list_dependency":list_dependency}
    #group[pair[4]]=group_this
    group_list.append(group)
    edge_list.append(edge)


print(depen_vocab)
with open("data/dependency_vocab", 'w') as fw:
    for cate in depen_vocab:
        fw.write(cate+"\n")
with open("data/Math23K_gcngroup.json", 'w') as fw:
    json_str = json.dumps(group_list)
    fw.write(json_str)

with open("data/Math23K_edge.json", 'w') as fw:
    json_str = json.dumps(edge_list)
    fw.write(json_str)


def time_since(s):  # compute time
    m = math.floor(s / 60)
    s -= m * 60
    h = math.floor(m / 60)
    m -= h * 60
    return '%dh %dm %ds' % (h, m, s)


start = time.time()
print("load time", time_since(time.time() - start))