#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Author: blahgeek
# @Date:   2017-02-13
# @Last modified by:   siboehm
# @Last modified time: 2023-03-23


import re
import os
import sqlite3
import logging
import shutil
import argparse
from bs4 import BeautifulSoup


def remove_navbar(soup):
    for id_ in (
        "site-nav",
        "resize-nav",
    ):
        try:
            soup.find(id=id_).extract()
        except AttributeError:
            pass

    try:
        soup.find("nav", class_="wy-nav-side").extract()
    except AttributeError:
        pass

    nav = soup.find("section", class_="wy-nav-content-wrap")
    if nav is not None:
        # Add a custom class to the 'wy-nav-side' element
        nav["class"].append("hide-navbar")

        # Add a style tag to the head of the document with the custom CSS
        style_tag = soup.new_tag("style")
        style_tag.string = """
        .hide-navbar {
            margin-left: 0 !important;
        }

        .wy-nav-content-wrap {
            margin-left: 0 !important;
        }
        """
        soup.head.append(style_tag)


def extract_sectionlink(soup):
    for link in soup.find_all("div", class_="section-link"):
        if not link.a.string:
            continue
        if re.match(r"^([0-9]+\.)+\s*$", link.a.string, re.M):
            continue
        yield link.a.string, "Guide", link.a["href"]


def extract_modern_module(soup, module_name):
    navigation_menu = soup.find(
        "div", role="navigation", class_="wy-menu wy-menu-vertical"
    )
    if not navigation_menu:
        return

    for link in navigation_menu.find_all("a", class_="reference internal"):
        # remove the leading numbering (like 1. or 2.2.1)
        desc = re.sub(r"^(\d+\.)+", "", " ".join(link.strings)).strip()
        if desc.endswith("()"):
            desc = desc[:-2]
            link_type = "Function"
        elif desc.endswith("_t"):
            link_type = "Type"
        else:
            link_type = "Guide"
        # get member pointed to by relative link
        if len(link["href"].split("#")) == 2:
            rel_link = link["href"].split("#")[1]
            member = soup.find(id=rel_link)
            # insert dash tag after link: <a name="//apple_ref/cpp/Entry Type/Entry Name" class="dashAnchor"></a>
            dash_tag = soup.new_tag("a")
            dash_tag["name"] = (
                "//apple_ref/cpp/" + link_type + "/" + " ".join(link.strings)
            )
            dash_tag["class"] = "dashAnchor"
            if member:
                member.insert_before(dash_tag)
        yield desc, link_type, link["href"]


def extract_cppmodule(soup):
    module = soup.find("div", class_="cppModule")
    if not module:
        return

    # Enumerations
    section = soup.find(class_="sectiontitle", text="Enumerations")
    if section:
        for item in section.parent.dl.find_all("dt", recursive=False):
            text = " ".join(item.stripped_strings)
            link = item.a["name"]
            yield text.replace("enum ", "").split()[0], "Enum", link
            for member in item.find_next_sibling("dd").find_all(
                class_="enum-member-name-def"
            ):
                text = "".join(member.stripped_strings)
                yield text.partition("=")[0], "Value", link

    # Functions
    section = soup.find(class_="fake_sectiontitle", text="Functions")
    if section:
        members = section.find_next_sibling(class_="members")
        for item in members.find_all(class_="member_name"):
            yield item.a.string, "Function", item.a["href"]
        for item in members.find_all(class_="member_name_long_type"):
            yield item.a.string, "Function", item.a["href"]

    # Typedefs
    section = soup.find(class_="fake_sectiontitle", text="Typedefs")
    if section:
        members = section.find_next_sibling(class_="members")
        for item in members.find_all(class_="member_name"):
            yield item.a.string, "Type", item.a["href"]


def make_docset_layout(path):
    shutil.rmtree(path, ignore_errors=True)
    doc_dir = os.path.join(path, "Contents/Resources/Documents")
    os.makedirs(doc_dir)
    shutil.copy(os.path.join(os.path.dirname(__file__), "icon.png"), path)
    shutil.copy(os.path.join(os.path.dirname(__file__), "icon@2x.png"), path)
    with open(os.path.join(path, "Contents/Info.plist"), "w") as plist:
        plist.write(
            """<?xml version="1.0" encoding="UTF-8"?>
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
    <key>DashDocSetFamily</key>
    <string>dashtoc</string>
</dict>
</plist>"""
        )
    return doc_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CUDA Docset generator")
    parser.add_argument(
        "-s",
        "--source",
        help="Source HTML doc folder",
        default="docs.nvidia.com",
    )
    parser.add_argument(
        "-d", "--dest", help="Destination .docset folder", default="./CUDA.docset"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    doc_dir = make_docset_layout(args.dest)
    db = sqlite3.connect(os.path.join(doc_dir, "../docSet.dsidx"))
    cur = db.cursor()

    cur.execute(
        """CREATE TABLE searchIndex(id INTEGER PRIMARY KEY, name TEXT,
                type TEXT, path TEXT);"""
    )

    for dirpath, dirnames, filenames in os.walk(args.source):
        relpath = os.path.relpath(dirpath, args.source)
        os.makedirs(os.path.join(doc_dir, relpath), exist_ok=True)
        for filename in filenames:
            filepath = os.path.join(args.source, relpath, filename)
            dstpath = os.path.join(doc_dir, relpath, filename)
            logging.info("Processing file {}".format(filepath))

            indexs = list()
            try:
                assert filepath.endswith(".html")
                with open(filepath, "rb") as src:
                    soup = BeautifulSoup(src.read().decode("utf8"), "lxml")
                    if filepath.endswith("index.html"):
                        for index in extract_modern_module(
                            soup, filepath.split("/")[-2]
                        ):
                            indexs.append(index)
                    else:
                        for index in extract_cppmodule(soup):
                            indexs.append(index)
                    remove_navbar(soup)
                    with open(dstpath, "wb") as dst:
                        dst.write(soup.encode("utf8"))
            except AssertionError:
                # except:
                shutil.copy(filepath, dstpath)

            for name, typ, pos in indexs:
                # print(name, typ, pos)
                name = re.sub("\s+", " ", name)
                pos = re.sub(filename, "", pos)
                assert "\n" not in name
                if "#" in pos[1:] or "/" in pos:
                    continue
                if not pos.startswith("#"):
                    pos = "#" + pos
                pos = os.path.join(relpath, filename) + pos
                # print(name, typ, pos)
                cur.execute(
                    "INSERT OR IGNORE INTO searchIndex(name,type,path) "
                    "VALUES (?, ?, ?);",
                    (name, typ, pos),
                )

    cur.execute("CREATE UNIQUE INDEX anchor ON searchIndex (name,type,path);")
    db.commit()
    db.close()
