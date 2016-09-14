using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using System.Web;
using lecture1;

namespace miniproject
{
    public class Crawler
    {
        //public Queue<string> Queue = new Queue<string>();
        public BackQueue BackQueue;

        public HttpClientHandler httpClientHandler;

        public HttpClient httpClient;

        public List<Host> Hosts;

        public List<Site> SitesVisited = new List<Site>();

        public Crawler(IEnumerable<string> url, IEnumerable<Host> hosts, HttpClient httpClient)
        {
            foreach (var u in url)
            {
                Queue.Enqueue(u);
            }

            this.Hosts = hosts.ToList();

            this.httpClient = httpClient;
        }

        public bool Run()
        {
            var timeoutms = 1000;

            while (Queue.Count > 0)
            {
                String url = Queue.Dequeue();
                Uri uri = new Uri(url);
                var hosturl = uri.Host;
                Host currentHost = Hosts.FirstOrDefault(x => x.hosturl.Contains(hosturl));
                if (currentHost == null)
                {
                    currentHost = new Host(url.Substring(0, url.IndexOf(uri.Host)) + hosturl, httpClient);
                    Hosts.Add(currentHost);
                }

                if (!currentHost.robots.IsAllowed(uri))
                {
                    Console.WriteLine("Url (\"{1}\") not allowed on this host (\"{0}\")", uri, url);
                    continue;
                }

                if (DateTime.Now - currentHost.lastVisited < TimeSpan.FromMilliseconds(timeoutms))
                {
                    Console.WriteLine("Sleeping for " + (currentHost.lastVisited.AddMilliseconds(timeoutms) - DateTime.Now).TotalMilliseconds + " ms");
                    Thread.Sleep(currentHost.lastVisited.AddMilliseconds(timeoutms) - DateTime.Now);
                }


                var content = httpClient.GetStringAsync(uri);
                try
                {
                    content.Wait();
                }
                catch (System.AggregateException ex)
                {
                    Console.WriteLine("Failed to get: {0}", url);
                }

                if (content.Status == TaskStatus.Faulted)
                    continue;

                var site = new Site(url, content.Result, currentHost);
                Console.WriteLine("Visited site: {0}", site.url);
                SitesVisited.Add(site);

                var doc = new HtmlAgilityPack.HtmlDocument();
                doc.LoadHtml(site.content);

                int allowed = 0;
                int notAllowed = 0;
                int duplicates = 0;

                foreach (var s in doc.DocumentNode.SelectNodes("//a").Where(x => x.Attributes["href"] != null).Select(x => x.Attributes["href"].Value))
                {
                    string candiate = "";

                    if (s.StartsWith("http"))
                        candiate = s;

                    if (s.StartsWith("//"))
                        candiate = url.Substring(0, url.IndexOf("//")) + s;

                    if (s.StartsWith("/") && !s.StartsWith("//"))
                        candiate = url.Substring(0, url.IndexOf("//")) + "//" + hosturl + s;

                    if (candiate == "")
                        continue;

                    var candidateUri = new Uri(candiate);

                    if (SitesVisited.Any(x => x.Equals(candiate)))
                        continue;

                    var chost = Hosts.FirstOrDefault(x => candidateUri.Host.Contains(new Uri(x.hosturl).Host));
                    if (chost == null)
                    {
                        chost = new Host(candiate.Substring(0, candiate.IndexOf("//")) + "//" + candidateUri.Host, httpClient);
                        Hosts.Add(chost);
                    }

                    if (chost.robots.IsAllowed(candiate))
                    {
                        //Console.WriteLine("Added a link: \"{0}\"", candiate);
                        if (!candiate.Trim().Equals("") && !SitesVisited.Any(x => x.url.Equals(x.content)))
                        {
                            Queue.Enqueue(candiate);
                            allowed++;
                        }
                        else
                        {
                            duplicates++;
                        }


                    }
                    else
                    {
                        notAllowed++;
                        //Console.WriteLine("Obmitted a link: \"{0}\"", candiate);
                    }
                }

                Console.WriteLine("Visited {0} sites, {1} to-go, added {2} to queue, and {3} was not allowed. ({4} duplicates)", SitesVisited.Count, Queue.Count, allowed, notAllowed, duplicates);
            }

            return true;
        }
    }
}