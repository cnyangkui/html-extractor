# -*- encoding: utf-8 -*-
import re
import requests
from collections import Counter
from bs4 import BeautifulSoup

authorset = {'责任编辑', '作者'}

'''
    获取html
'''
def get_html(url):
    obj = requests.get(url)
    return obj.text

'''
    过滤各类标签
    html_str:html字符串
    flag:是否移除所有标签
    return:过滤标签后的html字符串
'''
def filter_tags(html_str, flag):
    html_str = re.sub('(?is)<!DOCTYPE.*?>', '', html_str)
    html_str = re.sub('(?is)<!--.*?-->', '', html_str) #remove html comment
    html_str = re.sub('(?is)<script.*?>.*?</script>', '', html_str) #remove javascript
    html_str = re.sub('(?is)<style.*?>.*?</style>', '', html_str) #remove css
    html_str = re.sub('(?is)<a[\t|\n|\r|\f].*?>.*?</a>', '', html_str)  # remove a
    html_str = re.sub('(?is)<li[^nk].*?>.*?</li>', '', html_str)  # remove li
    #html_str = re.sub('&.{2,5};|&#.{2,5};', '', html_str) #remove special char
    if flag:
        html_str = re.sub('(?is)<.*?>', '', html_str) #remove tag
    return html_str

'''
    根据文本块密度获取正文
    html_str:网页源代码
    return：正文文本
'''
def extract_text_by_block(html_str):
    html = filter_tags(html_str, True)
    lines = html.split('\n')
    blockwidth = 3
    threshold = 86
    indexDistribution = []
    for i in range(0, len(lines) - blockwidth):
        wordnum = 0
        for j in range(i, i + blockwidth):
            line = re.sub("\\s+", '', lines[j])
            wordnum += len(line)
        indexDistribution.append(wordnum)
    startindex = -1
    endindex = -1
    boolstart = False
    boolend = False
    arcticle_content = []
    for i in range(0, len(indexDistribution) - blockwidth):
        if (indexDistribution[i] > threshold and boolstart is False):
            if indexDistribution[i + 1] != 0 or indexDistribution[i + 2] != 0 or indexDistribution[i + 3] != 0:
                boolstart = True
                startindex = i
                continue
        if boolstart is True:
            if indexDistribution[i] == 0 or indexDistribution[i + 1] == 0:
                endindex = i
                boolend = True
        tmp = []
        if boolend is True:
            for index in range(startindex, endindex + 1):
                line = lines[index]
                if len(line.strip()) < 5:
                    continue
                tmp.append(line.strip() + '\n')
            tmp_str = ''.join(tmp)
            if u"Copyright" in tmp_str or u"版权所有" in tmp_str:
                continue
            arcticle_content.append(tmp_str)
            boolstart = False
            boolend = False
    return ''.join(arcticle_content)

'''
    全网页查找根据文本块密度获取的正文，获取文本父级标签内的正文，目的是提高正文准确率
    html:网页html
    article:根据文本块密度获取的正文
    return:正文文本
'''
def extract_text_by_tag(html_str, article):
    lines = filter_tags(html_str, False)
    soup = BeautifulSoup(lines, 'lxml')
    p_list = soup.find_all('p')
    p_in_article = []
    for p in p_list:
        if p.text.strip() in article:
            p_in_article.append(p.parent)
    tuple = Counter(p_in_article).most_common(1)[0]
    article_soup = BeautifulSoup(str(tuple[0]), 'xml')
    return remove_space(article_soup.text)

'''
    移除字符串中的空白字符
'''
def remove_space(text):
    text = re.sub("[\t\r\n\f]", '', text)
    return text

'''
    抽取正文
    html_str:网页源代码
    return：正文文本
'''
def extract(url):
    html_str = get_html(url)
    article_temp = extract_text_by_block(html_str)
    try:
        article = extract_text_by_tag(html_str, article_temp)
    except:
        article = article_temp
    return article

if __name__ == '__main__':
    url = 'http://www.sohu.com/a/205718041_267106?code=26fdeda34ae31f3cc4a38793aeaa92fa&_f=index_chan08cpc_0_0'
    text  = extract(url)
    print(text)