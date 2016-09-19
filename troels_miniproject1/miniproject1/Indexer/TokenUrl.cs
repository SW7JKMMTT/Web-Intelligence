using System;

namespace miniproject1.Indexer
{
    [Serializable]
    public class TokenUrl : IComparable<TokenUrl>
    {
        public string Url;

        public TokenUrl(Uri uri)
        {
            Url = uri.AbsoluteUri;
        }

        public int CompareTo(TokenUrl obj)
        {
            return String.Compare(Url, obj.Url, StringComparison.Ordinal);
        }
    }
}