using System;
using System.Collections.Generic;
using System.Linq;
using miniproject1.Indexer;

namespace miniproject1.Searcher
{
    public class TokenSearcher
    {
        private Index index;

        public TokenSearcher(Index index)
        {
            this.index = index;
        }

        public IEnumerable<TokenUrl> And(IEnumerable<Token> list)
        {
            if (!list.Any() || list.Any(x => x == null))
            {
                return new List<TokenUrl>();
            }
            
            if (list.Count() == 1)
            {
                return list.FirstOrDefault().Uris.Keys;
            }

            var res = new List<TokenUrl>(list.FirstOrDefault().Uris.Keys);
               
            res = list.Skip(1).Aggregate(res, (current, token) => current.Intersect(token.Uris.Keys).ToList());

            return res;
        }

        public List<Tuple<double, TokenUrl>> OrderByScore(IEnumerable<Token> tokens, IEnumerable<TokenUrl> tokenUrls)
        {
            var res = new List<Tuple<double, TokenUrl>>();

            foreach (var tokenUrl in tokenUrls)
            {
                var score = tokens.Sum(x => x.NormalisedWeight(tokenUrl, 2));
                res.Add(new Tuple<double, TokenUrl>(score, tokenUrl));
            }

            return res;
        }
    }
}