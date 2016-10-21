import glob
import begin
import re
from bs4 import BeautifulSoup
import nltk
import lxml
from lxml.html.clean import Cleaner
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.stem.snowball import SnowballStemmer
from collections import Counter
from pprint import pprint

not_word_chars = re.compile(r'\s+|[^\w]|\s+[^\w]*|[^A-Za-z]')
lemma = WordNetLemmatizer()
stemmer = SnowballStemmer('english')
cleaner = Cleaner(scripts=True, javascript=True, comments=True, style=True, embedded=True, forms=True, annoying_tags=True)
inverted_index = dict()

def extract_text(html, method='lxml'):
        text = ''
        if method == 'lxml':
            text = lxml.html.fromstring(cleaner.clean_html(html)).text_content()
        else:
            soup = BeautifulSoup(content, 'html.parser')
            for unwanted in soup(['script', 'style']):
                unwanted.extract()
            text = soup.get_text(strip=True)
        return re.sub(not_word_chars, " ", text).lower()


def tokenize_string(string):
    tokens = nltk.word_tokenize(string)
    tokens = [stemmer.stem(token) for token in tokens if token not in stopwords.words('english')]
    return tokens

def search(query):
    findings = list()
    for word in tokenize_string(query):
        print(word)
        if word in inverted_index.keys():
            found = set([page for page, _ in inverted_index[word]])
            print('Found:', len(found), 'for', word)
        else:
            found = set()
            print('Nothing found for', word)
        findings.append(found)

    for page in set.intersection(*findings):
        print(page.path)


class Document(object):
    def __init__(self, path, content):
        self.path = path
        clean_text = extract_text(content)
        self.tokens = tokenize_string(clean_text)
        for token, cnt in Counter(self.tokens).items():
            if not token in inverted_index.keys():
                inverted_index[token] = list()
            inverted_index[token].append((self, cnt))

@begin.start
def main(dir: 'Directory tree of hosts'):
    "Index stuff"
    print('Indexing...')
    for content_file in glob.iglob(dir + '/**/content', recursive=True):
        with open(content_file, "r") as f:
            content = bytes(f.read(), 'utf-8')
            Document(content_file, content.decode('unicode_escape'))
        print('Indexed', content_file)

    print('Done indexing!')
    while True:
        query = input('Enter search query: ')
        if len(query):
            search(query)
        else:
            break

