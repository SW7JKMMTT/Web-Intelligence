using System;
using lecture1;

namespace miniproject
{
    public class Site
    {
        public Uri url;

        public string content;

        public DateTime lastVisited;

        public Host host;

        public Site(Uri url, string content, Host host)
        {
            this.url = url;
            this.content = content;
            this.lastVisited = DateTime.Now;
            host.lastVisited = DateTime.Now;
            this.host = host;
        }
    }
}