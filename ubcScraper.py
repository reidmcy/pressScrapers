import requests
from bs4 import BeautifulSoup
import sys
import os
import pandas

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
        "blurb" : [],
        "summary" : [],
        "subjects" : [],
        "authorBio" : [],
        "date" : [],
        "ISBN" : [],
    }
    print("Found {} urls".format(len(book_urls)))
    for url in book_urls[:2]:
        print("Getting: {}".format(url))
        with open("{}.html".format(url.replace('/','')), 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        r = requests.get(url)
        soup = BeautifulSoup(r.content, "html.parser")
        title = soup.find("h4").text
        print("Found: '{}'".format(title))
        print("Writing '{}/{}.html'".format(outputDir, title))
        with open("{}.html".format(title.replace('/','')), 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        booksDict['title'].append(title)
        booksDict['authors'].append([a.text for a in soup.find("div", {"class" : "author"}).find_all("a", {"class": "greenOver"})])
        try:
            booksDict["authorBio"].append(soup.find('div', {"id" : "tabs-2"}).text.lstrip()[:-1])
        except AttributeError:
            booksDict["authorBio"].append(None)
        overViewRaw = soup.find("div", {"class" : "tabDataHolder", "id" : "tabs--1"})
        try:
            booksDict['blurb'].append(overViewRaw.h3.text)
        except AttributeError:
            booksDict['blurb'].append(None)
        booksDict['summary'].append(overViewRaw.div.text)
        booksDict['subjects'].append([sub.text for sub in soup.find_all("div", {"class" : "iconGrid"})])
        print("Subjects are : {}".format(', '.join(booksDict['subjects'][-1])))
        details = soup.find("div", {"class": "overviewDetails overviewDetailsRight"})
        foundISBN = False
        for val in details.find_all('p'):
            if foundISBN:
                booksDict['date'].append(val.text)
                break
            elif val.text[:5] == "ISBN ":
                booksDict['ISBN'].append(val.text)
                foundISBN = True
    os.chdir('..')
    pandas.DataFrame(booksDict).to_csv("MQUPscrape.csv")

if __name__ == "__main__":
    main()
