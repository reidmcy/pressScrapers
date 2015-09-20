import requests
from bs4 import BeautifulSoup
import sys
import os
import pandas
import re

targetURL = "http://www.utppublishing.com/_search.php?mode=advanced&init=1&at_least=&title=&author=&isbn=&PubMonth=09&PubDay=19&PubYear=2015&category=6&series=&page="

productURL = "http://www.utppublishing.com/"

outputDir = "UT_Output"



def main():

    book_urls = []
    # get titles and links
    stillAgoodPage = True
    pageNum = 0
    while stillAgoodPage:
        pageNum += 1
        print("Getting page {}".format(pageNum))
        r = requests.get(targetURL + str(pageNum))
        soup = BeautifulSoup(r.content, "html.parser")
        if len(soup.find_all("a", {"class" : "product-title"})) > 1:
            for link in soup.find_all("a", {"class" : "product-title"}):
                if "http" in link.get("href"):
                    book_urls.append(link.get("href"))
                else:
                    book_urls.append(productURL + link.get("href"))
        else:
            stillAgoodPage = False
            print("Done")
        #if pageNum % 1 == 0:
        #    stillAgoodPage = False
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
        details = soup.find("td", {"class" : "details"})
        title = details.find('h1').text
        print("Found: '{}'".format(title))
        print("Writing '{}/{}.html'".format(outputDir, title))
        with open("{}.html".format(title.replace('/','')), 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        booksDict['title'].append(title)
        details = soup.find("td", {"class" : "property-value", "style" : "padding-top: 5px;", "colspan" : "2"}).find_all("div", {"class" : "fields-arr"})
        booksDict['ISBN'].append(details[0].text)
        booksDict['date'].append(' '.join(details[1].text.split(' ')[-2:]))
        booksDict['summary'].append(soup.find("div", {"class" : "ptab-cont tab-descr"}).text)
        authsLst = []
        authsBio = []

        for bio in soup.find_all("div", {"class": "ptab-cont extra_18"}):
            authsBio.append(bio.text.strip())
            try:
                authsLst.append(bio.find("strong").text)
            except AttributeError:
                try:
                    authsLst.append(bio.find("b").text)
                except AttributeError:
                    authsLst.append(soup.find("td", {"colspan" : "2", "class" :"property-value"}).text.replace("By ", '').replace("Edited by ", "").replace(" and ", ", ").split(', '))
        booksDict['authors'].append(authsLst)
        booksDict['authorBio'].append(authsBio)
        booksDict['subjects'].append(soup.find_all("a", {"class" : "bread-crumb"})[2].text)
    os.chdir('..')
    pandas.DataFrame(booksDict).to_csv("UBCscrape.csv")

if __name__ == "__main__":
    main()
