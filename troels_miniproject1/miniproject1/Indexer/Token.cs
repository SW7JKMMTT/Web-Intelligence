using System;
using System.Collections.Generic;
using System.Linq;
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
                site.TokenUrl.Tokens.Add(t);

                return t;
            }

            t = new Token(text, site, count);
            site.TokenUrl.Tokens.Add(t);

            tokens.Add(text, t);
            return t;
        }

        public static Token GetToken(string str, Dictionary<string, Token> tokens)
        {
            Token t = null;
            if (tokens.ContainsKey(str))
            {
                t = tokens[str];
            }
            else
            {
                Console.WriteLine("Term: \"{0}\" was not found in the index.", str);
            }

            return t;
        }

        public int DocumentFrequency()
        {
            return this.Uris.Count;
        }

        public double InverseDocumentFrequency(int n)
        {
            return (double)n / this.DocumentFrequency();
        }

        public double LogInverseDocumentFrequency(int n, double logbase)
        {
            return Math.Log(InverseDocumentFrequency(n), logbase);
        }

        public int CollectionFrequency()
        {
            return this.Uris.Sum(x => x.Value);
        }

        public int TermFrequency(TokenUrl tokenUrl)
        {
            int res = 0;
            Uris.TryGetValue(tokenUrl, out res);
            return res;
        }

        public double LogTermFrequency(TokenUrl tokenUrl, double logbase)
        {
            return 1.0 + Math.Log(TermFrequency(tokenUrl), logbase);
        }

        public double Weight(TokenUrl tokenUrl, int n)
        {
            // The weight is 0 if the url doesn't have the token
            if (!this.Uris.ContainsKey(tokenUrl))
                return 0;

            return LogTermFrequency(tokenUrl, 10) * InverseDocumentFrequency(n);
        }

        public double SqrtFactor(TokenUrl tokenUrl)
        {
            var sum = tokenUrl.Tokens.Sum(x => Math.Pow(x.LogTermFrequency(tokenUrl, 2), 2));

            return sum;
        }

        public double NormalisedWeight(TokenUrl tokenUrl, int n)
        {
            // The weight is 0 if the url doesn't have the token
            if (!this.Uris.ContainsKey(tokenUrl))
                return 0;

            return Weight(tokenUrl, n) / Math.Sqrt(SqrtFactor(tokenUrl));
        }

        public double Weight(int n)
        {
            return 1 * InverseDocumentFrequency(n);
        }

        public double SqrtFactor(int numTerms)
        {
            return Math.Pow(numTerms, 2) * numTerms;
        }

        public double NormalisedWeight(int numterms, int n)
        {
            return Weight(n) / Math.Sqrt(SqrtFactor(numterms));
        }
    }
}