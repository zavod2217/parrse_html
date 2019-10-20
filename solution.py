from bs4 import BeautifulSoup
import re
import os
import networkx as nx


# Вспомогательная функция, её наличие не обязательно и не будет проверяться
def build_tree(path: str)->dict:
    files = dict.fromkeys(os.listdir(path))  # Словарь вида {"filename1": None, "filename2": None, ...}
    for name, value in files.items():
        link = search_link(path + "/" + name)
        add_parents(name, link, files)
    return files


# Вспомогательная функция, её наличие не обязательно и не будет проверяться
def build_bridge(start: str, end: str, path: str)->list:
    files = build_tree(path)
    bridge = search_way(files, start, end)
    return bridge


def parse(start: str, end: str, path: str):
    bridge = build_bridge(start, end, path)  # Искать список страниц можно как угодно, даже так: bridge = [end, start]

    # Когда есть список страниц, из них нужно вытащить данные и вернуть их
    out = {}
    for file in bridge:
        with open("{}{}".format(path, file), encoding='u8') as data:
            soup = BeautifulSoup(data, "lxml")

        body = soup.find(id="bodyContent")
        imgs = count_img(body)
        headers = count_h_tag(body)
        linkslen = CountATag(body).result
        lists = CountList(body).result

        out[file] = [imgs, headers, linkslen, lists]

    return out


# поиск всех ссылок на странице
def search_link(file_path: str)-> list:
    with open(file_path, encoding='utf-8') as fp:
        soup = BeautifulSoup(fp, 'lxml')
        link = soup.find_all('a', href=True)
    return link


# функция заполняет словарь в котором каждому ключу (в виде имени файла) будут соответствовать ссылки на него ведущие
# {filename1: [filename12, filename32...]}
def add_parents(name: str, link: list, files: dict)-> None:
    files[name] = set()
    for i in link:
        temp = re.findall(r"(?<=/wiki/)[\w()]+", i['href'])
        if bool(temp):
            if temp[0] in files.keys():
                files[name].add(temp[0])


def search_way(files: dict, start: str, end: str)->list:
    DG = nx.DiGraph()
    for i, v in files.items():
        for e in v:
            DG.add_edge(i, e, weight=1)
    return nx.shortest_path(DG, start, end)


def count_img(body):
    temp = body.findAll('img')
    result = []
    for img in temp:
        if 'width' in img.attrs:
            if int(img['width']) >= 200:
                result.append(img)
    return len(result)


def count_h_tag(body):
    temp = body.findAll(re.compile('h\d'))
    temp = [list(map(lambda x: x.string, x)) for x in temp]  # if str(x.string)[0] in ['E','T','C']]
    result = []
    for value_list in temp:
        for value in value_list:
            if bool(value):
                result.append(value)
    result = [i for i in result if i[0] in ['E', 'T', 'C']]
    return len(result)


class CountATag:
    def __init__(self, body = None):
        self.tag_chain = 0
        self.result = 0
        self.parent = None
        if isinstance(self, object):
            self.count(body)

    def count(self, soup_object):
        if soup_object.name is not None:
            if soup_object.name == 'a' and self.parent == soup_object.parent:
                self.tag_chain += 1
            if soup_object.name == 'a' and self.parent != soup_object.parent:
                if self.tag_chain > self.result:
                    self.result = self.tag_chain
                self.parent = soup_object.parent
                self.tag_chain = 1

        if 'contents' in soup_object.__dict__:
            for obj in soup_object.contents:
                self.count(self.next_tag(obj))

    @staticmethod
    def next_tag(object):
        return object.next


class CountList(CountATag):
    def __init__(self, body):
        super().__init__()
        self.count(body)

    def count(self, soup_object):
        if soup_object is not None:
            if soup_object.name in ['ol', 'ul'] and not bool(soup_object.find_parents('ol')) \
                    and not bool(soup_object.find_parents('ul')):
                self.result += 1

            if 'contents' in soup_object.__dict__:
                for i in soup_object.contents:
                    self.count(self.next_tag(i))
