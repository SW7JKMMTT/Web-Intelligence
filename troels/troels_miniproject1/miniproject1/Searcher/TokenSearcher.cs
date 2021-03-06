﻿using System;
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
               
            res = list.Skip(1).Aggregate(res, (current, token) => current.Union(token.Uris.Keys).ToList());

            return res;
        }

        public List<Tuple<double, TokenUrl>> OrderByScore(IList<Token> tokens, IEnumerable<TokenUrl> tokenUrls, int documents)
        {
            var res = new List<Tuple<double, TokenUrl>>();

            var tokenCount = tokens.Count();

            foreach (var tokenUrl in tokenUrls)
            {
                var score = tokens.Sum(x => x.NormalisedWeight(tokenUrl, documents) * x.NormalisedWeight(tokenCount, documents));
                res.Add(new Tuple<double, TokenUrl>(score, tokenUrl));
            }

            return res;
        }
    }
}