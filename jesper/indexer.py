import glob
import begin
import re
from bs4 import BeautifulSoup
import nltk
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer
from collections import Counter
from pprint import pprint

not_word_chars = re.compile(r'[^\w]')
lemma = WordNetLemmatizer()
inverted_index = dict()

def tokenize_string(string):
    string = re.sub(not_word_chars, ' ', string).lower()
    tokens = nltk.word_tokenize(string)
    tokens = [lemma.lemmatize(token) for token in tokens if token not in stopwords.words('english')]
    return tokens

def search(query):
    print(query)
    findings = list()
    for word in tokenize_string(query):
        print(word)
        if word in inverted_index.keys():
            found = set([page for page, _ in inverted_index[word]])
            print('Found:', len(found), 'for', word)
        else:
            found = set()
        findings.append(found)

    for page in set.intersection(*findings):
        print(page.path)

class Document(object):
    def __init__(self, path, content):
        self.path = path
        soup = BeautifulSoup(content, 'html.parser')
        for unwanted in soup(['script', 'style']):
            unwanted.extract()
        self.tokens = tokenize_string(soup.get_text(strip=True))
        for token, cnt in Counter(self.tokens).items():
            if not token in inverted_index.keys():
                inverted_index[token] = list()
            inverted_index[token].append((self, cnt))

@begin.start
def main(dir: 'Directory tree of hosts' = None):
    "Index stuff"
    print('Indexing...')
    cnt = 0
    for content_file in glob.iglob(dir + '/**/content', recursive=True):
        if cnt > 20:
            break
        with open(content_file, "r") as f:
            content = bytes(f.read(), 'utf-8')
            Document(content_file, content.decode('unicode_escape'))
        cnt += 1

    print('Done indexing!')
    while True:
        query = input('Enter search query: ')
        if len(query):
            search(query)
        else:
            break

