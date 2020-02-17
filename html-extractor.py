# -*- encoding: utf-8 -*-
import re
import requests
from collections import Counter
from bs4 import BeautifulSoup


def get_html(url):
    """ 获取html """
    # obj = requests.get(url)
    # return obj.text

    try:
        obj = requests.get(url)
        code = obj.status_code
        if code == 200:
            # 防止中文正文乱码
            html = obj.content
            html_doc = str(html, 'utf-8')
            return html_doc
        return None
    except:
        return None


def filter_tags(html_str, flag):
    """ 过滤各类标签
    :param html_str: html字符串
    :param flag: 是否移除所有标签
    :return: 过滤标签后的html字符串
    """
    html_str = re.sub('(?is)<!DOCTYPE.*?>', '', html_str)
    html_str = re.sub('(?is)<!--.*?-->', '', html_str)  # remove html comment
    html_str = re.sub('(?is)<script.*?>.*?</script>', '', html_str)  # remove javascript
    html_str = re.sub('(?is)<style.*?>.*?</style>', '', html_str)  # remove css
    html_str = re.sub('(?is)<a[\t|\n|\r|\f].*?>.*?</a>', '', html_str)  # remove a
    html_str = re.sub('(?is)<li[^nk].*?>.*?</li>', '', html_str)  # remove li
    # html_str = re.sub('&.{2,5};|&#.{2,5};', '', html_str) #remove special char
    if flag:
        html_str = re.sub('(?is)<.*?>', '', html_str)  # remove tag
    return html_str


def extract_text_by_block(html_str):
    """ 根据文本块密度获取正文
    :param html_str: 网页源代码
    :return: 正文文本
    """
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


def extract_text_by_tag(html_str, article):
    """ 全网页查找根据文本块密度获取的正文的位置，获取文本父级标签内的正文，目的是提高正文准确率
    :param html: 网页html
    :param article: 根据文本块密度获取的正文
    :return: 正文文本
    """
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


def remove_space(text):
    """ 移除字符串中的空白字符 """
    text = re.sub("[\t\r\n\f]", '', text)
    return text


def extract(url):
    """ 抽取正文
    :param url: 网页链接
    :return：正文文本
    """
    html_str = get_html(url)
    if html_str == None:
        return None
    article_temp = extract_text_by_block(html_str)
    try:
        article = extract_text_by_tag(html_str, article_temp)
    except:
        article = article_temp
    return article


if __name__ == '__main__':
    url = 'http://www.eeo.com.cn/2020/0215/376405.shtml'
    text = extract(url)
    print(text)
