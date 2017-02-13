#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Author: blahgeek
# @Date:   2017-02-13
# @Last modified by:   blahgeek
# @Last modified time: 2017-02-13


import os
import sqlite3
import logging
import shutil
import argparse
from bs4 import BeautifulSoup


def remove_navbar(soup):
    for id_ in ('site-nav', 'resize-nav', ):
        try:
            soup.find(id=id_).extract()
        except AttributeError:
            pass


def extract_sectionlink(soup):
    for link in soup.find_all('div', class_='section-link'):
        yield link.a.string, 'Guide', link.a['href']


def extract_cppmodule(soup):
    module = soup.find('div', class_='cppModule')
    if not module:
        return

    # Enumerations
    section = soup.find(class_='sectiontitle', text='Enumerations')
    if section:
        for item in section.parent.dl.find_all('dt', recursive=False):
            text = ' '.join(item.stripped_strings)
            link = item.a['name']
            yield text.replace('enum ', '').split()[0], 'Enum', link
            for member in item.find_next_sibling('dd')\
                    .find_all(class_='enum-member-name-def'):
                text = ''.join(member.stripped_strings)
                yield text.partition('=')[0], 'Value', link

    # Functions
    section = soup.find(class_='fake_sectiontitle', text='Functions')
    if section:
        members = section.find_next_sibling(class_='members')
        for item in members.find_all(class_='member_name'):
            yield item.a.string, 'Function', item.a['href']
        for item in members.find_all(class_='member_name_long_type'):
            yield item.a.string, 'Function', item.a['href']

    # Typedefs
    section = soup.find(class_='fake_sectiontitle', text='Typedefs')
    if section:
        members = section.find_next_sibling(class_='members')
        for item in members.find_all(class_='member_name'):
            yield item.a.string, 'Type', item.a['href']


def make_docset_layout(path):
    shutil.rmtree(path, ignore_errors=True)
    doc_dir = os.path.join(path, 'Contents/Resources/Documents')
    os.makedirs(doc_dir)
    shutil.copy(os.path.join(os.path.dirname(__file__), 'icon.png'), path)
    with open(os.path.join(path, 'Contents/Info.plist'), 'w') as plist:
        plist.write('''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleIdentifier</key>
    <string>CUDA</string>
    <key>CFBundleName</key>
    <string>CUDA</string>
    <key>DocSetPlatformFamily</key>
    <string>CUDA</string>
    <key>isDashDocset</key>
    <true/>
    <key>isJavaScriptEnabled</key>
    <false/>
    <key>dashIndexFilePath</key>
    <string>index.html</string>
</dict>
</plist>''')
    return doc_dir


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CUDA Docset generator')
    parser.add_argument('-s', '--source', help='Source HTML doc folder',
                        default='/opt/cuda/doc/html/')
    parser.add_argument('-d', '--dest', help='Destination .docset folder',
                        default='./CUDA.docset')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    doc_dir = make_docset_layout(args.dest)
    db = sqlite3.connect(os.path.join(doc_dir, '../docSet.dsidx'))
    cur = db.cursor()

    cur.execute('''CREATE TABLE searchIndex(id INTEGER PRIMATY KEY, name TEXT,
                type TEXT, path TEXT);''')
    cur.execute('CREATE UNIQUE INDEX anchor ON searchIndex (name,type,path);')

    for dirpath, dirnames, filenames in os.walk(args.source):
        relpath = os.path.relpath(dirpath, args.source)
        os.makedirs(os.path.join(doc_dir, relpath), exist_ok=True)
        for filename in filenames:
            filepath = os.path.join(args.source, relpath, filename)
            dstpath = os.path.join(doc_dir, relpath, filename)
            logging.info('Processing file {}'.format(filepath))

            indexs = list()
            try:
                assert filepath.endswith('.html')
                soup = BeautifulSoup(open(filepath), 'lxml')
                for index in extract_cppmodule(soup):
                    indexs.append(index)
                for index in extract_sectionlink(soup):
                    indexs.append(index)
                remove_navbar(soup)
                open(dstpath, 'w').write(str(soup))
            except AssertionError:
                # except:
                shutil.copy(filepath, dstpath)

            for name, typ, pos in indexs:
                if '#' in pos[1:] or '/' in pos:
                    continue
                # print(name, typ, pos)
                # assert('#' not in pos[1:])
                if not pos.startswith('#'):
                    pos = '#' + pos
                pos = os.path.join(relpath, filename) + pos
                cur.execute('INSERT OR IGNORE INTO searchIndex(name,type,path)'
                            'VALUES (?, ?, ?);', (name, typ, pos))

    db.commit()
    db.close()
