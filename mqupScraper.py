import requests
from bs4 import BeautifulSoup
import sys
import os
import pandas

targetURL = "http://www.mqup.ca/browse-books-pages-46.php"

values = {
    "actions" : "updateProductFilters",
    "filters" : """a:1:{i:1;s:4:"3333";}""",
    "options" : """a:12:{s:9:"queryFunc";s:25:"getProductsForListingPage";s:11:"enableCache";b:0;s:5:"limit";i:200;s:6:"offset";i:0;s:10:"searchTerm";s:0:"";s:6:"pageID";s:2:"46";s:14:"contributor_id";s:0:"";s:10:"pageOffset";i:0;s:13:"resultsPerRow";i:4;s:14:"resultsPerPage";i:200;s:9:"className";s:0:"";s:8:"currency";s:3:"CAD";}""",
}

outputDir = "MQUP_Output"

def main():
    r = requests.post(targetURL, data = values)
    soup = BeautifulSoup(r.content, "html.parser")

    # make a list
    book_urls = []
    # get titles and links
    for link in soup.find_all("a"):
        if "products" in link.get("href") and len(link.text) > 1:
            book_urls.append(link.get("href"))
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
    for url in book_urls:
        print("Getting: {}".format(url))
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
