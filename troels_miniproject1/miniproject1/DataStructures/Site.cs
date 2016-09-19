using System;
using System.Collections.Generic;
using miniproject1.Indexer;

namespace miniproject1.DataStructures
{
    [Serializable]
    public class Site : IComparable<Uri>
    {
        public Uri Url;

        public string Content;

        public DateTime LastVisited;

        public Host Host;

        public List<string> Tokens;

        public TokenUrl TokenUrl;

        public Site(Uri url, string content, Host host)
        {
            Url = url;
            Content = content;
            LastVisited = DateTime.Now;
            host.LastVisited = DateTime.Now;
            Host = host;
            TokenUrl = new TokenUrl(url);
        }

        public int CompareTo(Uri other)
        {
            return String.Compare(Url.AbsoluteUri, other.AbsoluteUri, StringComparison.Ordinal);
        }
    }
}