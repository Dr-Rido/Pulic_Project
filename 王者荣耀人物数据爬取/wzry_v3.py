"""爬取王者荣耀数据"""
import requests
from fake_useragent import UserAgent
from queue import Queue
from threading import Thread
import re
import json
import execjs
from parsel import Selector
import os
from bs4 import BeautifulSoup


def spider():
    # 准备构建参数的str（添加为局部变量增加访问效率）
    burl_str = "//game.gtimg.cn/images/yxzj/img201606/skin/hero-info/"
    while not url_que.empty():
        # 获取url
        url = url_que.get()
        # 发送请求
        html = send_request(url)
        # 解析数据
        selector = Selector(html)
        # 英雄的所有的皮肤的名称
        skin_list = parsel_skin_info(html)
        # 英雄名称
        hero_name = selector.css('h2.cover-name::text').get()
        # 英雄代号
        code = hero_json.get(hero_name)
        # js逆向参数构建
        burl = f'{burl_str}/{code}/{code}'
        # 英雄所有皮肤大图链接
        bgskin_list = js_func(len(skin_list), burl)
        # 解析基本数据
        data = parsel_base_info(html)
        save_data(hero_name, data)
        # 下载所有皮肤
        for skin_url, skin_name in zip(bgskin_list, skin_list):
            skin_name = re.sub('&\d*', '', skin_name)
            contents = requests.get(skin_url).content
            save_bg(hero_name, skin_name, contents)
        print(f'{hero_name}皮肤下载完成！')


def js_func(skin_length, burl):
    """
    js逆向获取皮肤大图链接
    """
    with open('skin_js.js', encoding='utf-8')as f:
        js_read = f.read()
    js_code = execjs.compile(js_read)
    bgskin_list = js_code.call('wrap', skin_length, burl)
    return bgskin_list


def send_request(url):
    headers = {
        'User-Agent': UserAgent().chrome
    }
    resp = requests.get(url=url, headers=headers)
    # 网页编码是gbk
    resp.encoding = 'gbk'
    html = resp.text
    return html


def save_bg(hero_name, skin_name,  content, file_name='皮肤'):
    """保存图片"""
    if not os.path.exists(f'英雄资料/{hero_name}/{file_name}'):
        os.makedirs(f'英雄资料/{hero_name}/{file_name}')
    with open(f'英雄资料/{hero_name}/{file_name}/{skin_name}.jpg', 'wb')as f:
        f.write(content)


def save_data(hero_name, content, file_name='技能'):
    """
    保存详情信息
    """
    content = {hero_name: content}
    if not os.path.exists(f'英雄资料/{hero_name}/{file_name}'):
        os.makedirs(f'英雄资料/{hero_name}/{file_name}')
    with open(f'英雄资料/{hero_name}/{file_name}/Skills.json', 'w', encoding='utf-8')as f:
        f.write(str(content).replace('\'', '\"'))
    print(f'{hero_name}{file_name}下载完成！')


def parsel_base_info(html):
    selector = Selector(html)
    # 技能介绍
    skills = selector.css('div.skill.ls.fl')
    # 技能名称
    skill_name = skills.css('p>b:not(p.no5)::text').getall()
    # 技能描述
    skill_describe = skills.css('p.skill-desc::text').getall()
    return dict(zip(skill_name, skill_describe))


def all_hero_code():
    """获取英雄-代码json数据"""
    code_url = 'https://game.gtimg.cn/images/yxzj/web201706/js/heroid.js'
    hero_code_html = send_request(code_url)
    # 格式化
    html_fomart = hero_code_html.replace('\'', '\"').replace(' ', '').replace('\t', '')
    html_str = re.findall('varmodule_exports=({[\s\S]*?});\n', html_fomart)[0].replace('\n', '')
    # 加载为字典
    hero_dict = json.loads(html_str)
    hero_dict_format = dict((value, key) for key, value in hero_dict.items())
    return hero_dict_format


def parsel_skin_info(html):
    """解析英雄皮肤数据"""
    selector = Selector(html)
    # skins = selector.css('div.pic-pf ul li').getall()
    skin_str = selector.css('div.pic-pf ul::attr(data-imgname)').get()
    skin_list = skin_str.split('|')
    return skin_list


if __name__ == '__main__':
    url_que = Queue()
    hero_json = all_hero_code()
    # 初始化url
    for id in hero_json.values():
        url = f'https://pvp.qq.com/web201605/herodetail/{id}.shtml'
        url_que.put(url)
    # 创建多线程
    for i in range(10):     # 十个线程
        t = Thread(target=spider)
        t.start()   # 启动线程
