using System;
using System.Collections.Generic;
using System.Linq;
using miniproject1.Indexer;
using miniproject1.DataStructures;

namespace miniproject1.Searcher
{
    public class BooleanSearcher
    {
        private readonly Index _index;

        public BooleanSearcher(Index index)
        {
            _index = index;
        }

        private IEnumerable<string> GetTermsAndExec(string term1, string term2, Func<Token, Token, IEnumerable<string>> method)
        {
            var token1 = Token.GetToken(term1, _index.Tokens);
            var token2 = Token.GetToken(term2, _index.Tokens);

            if (token1 == null || token2 == null)
                return new List<string>();

            return method(token1, token2);
        }

        #region And
        private IEnumerable<string> And(Token term1, Token term2)
        {
            return And(term1.Uris.Keys.Select(x => x.Url), term2.Uris.Keys.Select(x => x.Url));
        }

        public IEnumerable<string> And(IEnumerable<string> term1, string term2)
        {
            var term2Token = Token.GetToken(term2, _index.Tokens);
            if(term2Token == null)
                return new List<string>();

            return And(term1, term2Token.Uris.Keys.Select(x => x.Url));
        }

        public IEnumerable<string> And(string term1, IEnumerable<string> term2)
        {
            return And(term2, term1);
        }

        public IEnumerable<string> And(IEnumerable<string> term1, IEnumerable<string> term2)
        {
            return term1.Intersect(term2);
        }

        public IEnumerable<string> And(string term1, string term2)
        {
            return GetTermsAndExec(term1, term2, And);
        }
        #endregion

        private IEnumerable<string> or(Token term1, Token term2)
        {
            return term1.Uris.Keys.Union(term2.Uris.Keys).Select(x => x.Url);
        }


        public IEnumerable<string> Or(string term1, string term2)
        {
            return GetTermsAndExec(term1, term2, or);
        }
    }
}