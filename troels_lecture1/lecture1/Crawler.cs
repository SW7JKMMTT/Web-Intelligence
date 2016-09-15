using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using miniproject;

namespace lecture1
{
    public class Crawler
    {
        //public Queue<string> Queue = new Queue<string>();
        public BackQueue BackQueue;

        public HttpClientHandler httpClientHandler;

        public HttpClient httpClient;

        public List<Host> hosts;

        public List<Site> SitesVisited = new List<Site>();

        public Crawler(IEnumerable<Uri> url, IEnumerable<Host> hosts, HttpClient httpClient)
        {
            this.hosts = hosts.ToList();

            this.httpClient = httpClient;

            BackQueue = new BackQueue();

            foreach (var u in url)
            {
                //var host = new Host(u, httpClient);
                var host = Host.GetOrCreate(u, this.hosts);
                BackQueue.AddToQueue(host, u);
            }
        }

        public bool Run()
        {
            var timeoutms = 1000;
            Stopwatch sw = Stopwatch.StartNew();
            while (BackQueue.GetBackQueueCount() > 0)
            {

                Uri uri = BackQueue.GetSite();
                var currentHost = Host.GetOrCreate(uri, hosts);

                if (!currentHost.robots.IsAllowed(uri))
                {
                    Console.WriteLine("Url (\"{0}\") not allowed on this host (\"{1}\")", uri, uri.Host);
                    continue;
                }

                if (DateTime.Now - currentHost.lastVisited < TimeSpan.FromMilliseconds(timeoutms))
                {
                    Console.WriteLine("Sleeping for " + (currentHost.lastVisited.AddMilliseconds(timeoutms) - DateTime.Now).TotalMilliseconds + " ms");
                    Thread.Sleep(currentHost.lastVisited.AddMilliseconds(timeoutms) - DateTime.Now);
                }

                currentHost.WaitForRobots(httpClient);
                Task<string> content = null;
                try
                {
                    content = httpClient.GetStringAsync(uri);
                    content.Wait();
                }
                catch (System.AggregateException)
                {
                    Console.WriteLine("Failed to get: {0}", uri);
                    currentHost.lastVisited = DateTime.Now;
                }

                if (content == null || content.Status != TaskStatus.RanToCompletion)
                    continue;

                var site = new Site(uri, content.Result, currentHost);
                Console.WriteLine("Visited site: {0}", site.url);
                SitesVisited.Add(site);

                IEnumerable<string> urls = null;
                try
                {
                    var doc = new HtmlAgilityPack.HtmlDocument();
                    doc.LoadHtml(site.content);

                    urls =
                        doc.DocumentNode.SelectNodes("//a")
                            .Where(x => x.Attributes["href"] != null)
                            .Select(x => x.Attributes["href"].Value);
                }
                catch (Exception ex)
                {
                    Debug.WriteLine(ex.Message);
                }

                int allowed = 0;
                int notAllowed = 0;
                int duplicates = 0;

                if(urls == null)
                    continue;

                foreach (var s in urls)
                {
                    string candiate = "";

                    if (s.StartsWith("http://") || s.StartsWith("https://"))
                        candiate = s;

                    if (s.StartsWith("//"))
                        candiate = uri.Scheme + ":" + s;

                    if (s.StartsWith("/") && !s.StartsWith("//"))
                        candiate = uri.Scheme + "://" + currentHost.hosturl.Host + s;

                    if (candiate == "")
                        continue;

                    Uri candidateUri = null;
                    try
                    {
                        candidateUri = new Uri(candiate);
                    }
                    catch (Exception exception)
                    {
                        Console.WriteLine("Candidate failed: " + candiate + "\n" +exception.Message);
                        continue;
                    }
                    

                    if (SitesVisited.Any(x => x.url.Equals(candidateUri)))
                        continue;

                    var chost = Host.GetOrCreate(candidateUri, hosts);


                    if (chost.robots.IsAllowed(candiate))
                    {
                        if (!candiate.Trim().Equals("") && !SitesVisited.Any(x => x.url.Equals(candidateUri)))
                        {
                            BackQueue.AddToQueue(chost, candidateUri);
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
                Console.WriteLine("{0} sites / {1} seconds = {2} sites pr. second", SitesVisited.Count, sw.Elapsed.Seconds, (double)(SitesVisited.Count / sw.Elapsed.TotalSeconds));
                Console.WriteLine("Visited {0} sites, {1} to-go, added {2} to queue, and {3} was not allowed. ({4} duplicates)\n", SitesVisited.Count, BackQueue.GetBackQueueCount(), allowed, notAllowed, duplicates);
            }

            return true;
        }
    }
}