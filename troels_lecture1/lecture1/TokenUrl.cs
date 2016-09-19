using System;

namespace lecture1
{
    [Serializable]
    public class TokenUrl
    {
        public string url;

        public TokenUrl(Uri uri)
        {
            url = uri.AbsoluteUri;
        }
    }
}