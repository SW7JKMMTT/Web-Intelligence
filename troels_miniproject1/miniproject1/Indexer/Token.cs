using System;
using System.Collections.Generic;
using miniproject1.DataStructures;

namespace miniproject1.Indexer
{
    [Serializable]
    public class Token
    {
        public string TokenText;

        public SortedDictionary<TokenUrl, int> Uris;

        public Token(string text, Site site, int count)
        {
            TokenText = text;
            Uris = new SortedDictionary<TokenUrl, int> { { site.TokenUrl, count } };
        }

        public static Token AddOrCreate(string text, Site site, int count, Dictionary<string, Token> tokens)
        {
            var exists = tokens.ContainsKey(text);
            Token t;
            if (exists)
            {
                var url = site.TokenUrl;
                t = tokens[text];
                var ts = t.Uris.ContainsKey(url);
                if (ts)
                {
                    return t;
                }
                t.Uris.Add(url, count);

                return t;
            }

            t = new Token(text, site, count);

            tokens.Add(text, t);
            return t;

        }
    }
}