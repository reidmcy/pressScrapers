import requests
from bs4 import BeautifulSoup
import sys
import os
import pandas
import re

targetURL = "http://www.ubcpress.ca/search/subject_list.asp?SubjID=45"

bookLinks = "http://www.ubcpress.ca/search/"

outputDir = "UBC_Output"


def main():
    r = requests.get(targetURL)
    soup = BeautifulSoup(r.content, "html.parser")
    # make a list
    book_urls = []
    # get titles and links
    for link in soup.find_all("a"):
        if "title_book.asp" in link.get("href"):
            book_urls.append(bookLinks + link.get("href"))
    if not os.path.isdir(outputDir):
        os.mkdir(outputDir)
    os.chdir(outputDir)
    booksDict = {
        "title" : [],
        "authors" : [],
        "summary" : [],
        "subjects" : [],
        "authorBio" : [],
        "date" : [],
        "ISBN" : [],
    }
    print("Found {} urls".format(len(book_urls)))
    for i, url in enumerate(book_urls):
        print("On url index {}".format(i))
        r = requests.get(url)
        soup = BeautifulSoup(r.content, "html.parser")
        print("Getting: {}".format(url))
        title = soup.find("span", {"class" : "booktitle"}).text
        print("Found: '{}'".format(title))
        print("Writing '{}/{}.html'".format(outputDir, title))
        with open("{}.html".format(title.replace('/','')), 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        booksDict['title'].append(title)
        booksDict['authors'].append([a.text.strip() for a in soup.find_all("a", {"href" : "#author"})])
        mainBodyText = soup.find("td", {"width" : "545", "colspan":"3"}).find("span" , {"class" : "regtext"})
        regex = re.match(r"""(.*)About the Author\(s\)(.*)Table of Contents""", mainBodyText.text, flags = re.DOTALL)
        if regex is None:
            regex = re.match(r"""(.*)About the Author\(s\)(.*)""", mainBodyText.text, flags = re.DOTALL)
        booksDict['summary'].append(regex.group(1).strip())
        booksDict["authorBio"].append(regex.group(2).strip().split('\n '))
        booksDict["authorBio"][-1] = [s.strip() for s in booksDict["authorBio"][-1]]
        subjectsLst = []
        for sub in mainBodyText.find_all("a"):
            try:
                if "subject_list.asp?SubjID=" in sub.get("href"):
                    subjectsLst.append(sub.text)
            except TypeError:
                pass
        booksDict["subjects"].append(subjectsLst)
        newstext = soup.find("span", {"class" : "newstext"}).text
        regex = re.search(r"Release Date: (.*)(ISBN: \d*)", newstext)
        try:
            booksDict['date'].append(regex.group(1))
            booksDict['ISBN'].append(regex.group(2))
        except AttributeError:
            booksDict['date'].append(None)
            booksDict['ISBN'].append(None)
    os.chdir('..')
    pandas.DataFrame(booksDict).to_csv("UBCscrape.csv")

if __name__ == "__main__":
    main()
