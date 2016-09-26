import glob
import begin
from bs4 import BeautifulSoup

@begin.start
def main(dir: 'Directory tree of hosts' = None):
    "Index stuff"
    print(dir)
    pass

@begin.subcommand
def test_doc(path):
    with open(path, "r") as f:
        Document(path, f.read())

class Document:
    @begin.subcommand
    def __init__(self, path, content):
        self.path = path
        self.content = content
        soup = BeautifulSoup(self.content, 'html.parser')
        for unwanted in soup(['script', 'style']):
            unwanted.extract()        
        self.clean_content = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        self.clean_content = '\n'.join(chunk for chunk in chunks if chunk)

        print(self.clean_content)
