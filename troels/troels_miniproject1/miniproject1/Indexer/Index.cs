using System.Collections.Generic;

namespace miniproject1.Indexer
{
    public class Index
    {
        public Dictionary<string, Token> Tokens;

        public Index()
        {
            Tokens = new Dictionary<string, Token>();

        }
    }
}