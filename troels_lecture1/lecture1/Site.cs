using System;

namespace miniproject
{
    public class Site
    {
        public string url;

        public string content;

        public DateTime lastVisited;

        public Host host;

        public Site(string url, string content, Host host)
        {
            this.url = url;
            this.content = content;
            this.lastVisited = DateTime.Now;
            host.lastVisited = DateTime.Now;
            this.host = host;
        }
    }
}