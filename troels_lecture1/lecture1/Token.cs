using System;
using System.Collections.Generic;
using System.Linq;

namespace lecture1
{
    [Serializable]
    public class Token
    {
        public string tokenText;

        public Dictionary<TokenUrl, int> Uris;

        public Token(string text, Site site, int count)
        {
            tokenText = text;
            Uris = new Dictionary<TokenUrl, int>();
            Uris.Add(site.TokenUrl, count);
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