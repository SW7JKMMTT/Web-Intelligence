using System;
using System.Collections.Generic;

namespace lecture1
{
    [Serializable]
    public class Site : IComparable<Uri>
    {
        public Uri url;

        public string content;

        public DateTime lastVisited;

        public Host host;

        public List<string> tokens;

        public TokenUrl TokenUrl;

        public Site(Uri url, string content, Host host)
        {
            this.url = url;
            this.content = content;
            this.lastVisited = DateTime.Now;
            host.lastVisited = DateTime.Now;
            this.host = host;
            this.TokenUrl = new TokenUrl(url);
        }

        public int CompareTo(Uri other)
        {
            return url.AbsoluteUri.CompareTo(other.AbsoluteUri);
        }
    }
}