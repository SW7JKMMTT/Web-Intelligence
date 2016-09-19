using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using miniproject1.DataStructures;

namespace miniproject1.Crawler
{
    [Serializable]
    public class Crawler
    {
        public BackQueue BackQueue;

        [NonSerialized]
        public HttpClient HttpClient;

        public List<Host> Hosts;

        public Dictionary<Uri, Site> SitesVisited = new Dictionary<Uri, Site>();

        public int Limit;

        public int StartedWith = 0;

        public Crawler(IEnumerable<Uri> url, IEnumerable<Host> hosts, HttpClient httpClient, int limit)
        {
            Hosts = hosts.ToList();

            HttpClient = httpClient;

            if (BackQueue == null)
                BackQueue = new BackQueue();

            foreach (var u in url)
            {
                var host = Host.GetOrCreate(u, Hosts);
                BackQueue.AddToQueue(host, u);
            }

            Limit = limit;
        }

        public bool Run()
        {
            Stopwatch sw = Stopwatch.StartNew();
            while (BackQueue.GetBackQueueCount() > 0 && SitesVisited.Count < Limit)
            {

                Uri uri = BackQueue.GetSite();
                var currentHost = Host.GetOrCreate(uri, Hosts);

                if (!currentHost.Robots.IsAllowed(uri))
                {
                    Console.WriteLine("Url (\"{0}\") not allowed on this host (\"{1}\")", uri, uri.Host);
                    continue;
                }

                var earliestNextVisit = currentHost.LastVisited + currentHost.CrawlDelay;
                if (earliestNextVisit > DateTime.Now)
                {
                    Console.WriteLine("Sleeping for " + (earliestNextVisit - DateTime.Now) + " ms");
                    Thread.Sleep(earliestNextVisit - DateTime.Now);
                }

                currentHost.WaitForRobots(HttpClient);
                var t1 = sw.ElapsedMilliseconds;
                Task<string> content = null;
                try
                {
                    content = HttpClient.GetStringAsync(uri);
                    content.Wait();
                }
                catch (AggregateException)
                {
                    Console.WriteLine("Failed to get: {0}", uri);
                    currentHost.LastVisited = DateTime.Now;
                }

                if (content == null || content.Status != TaskStatus.RanToCompletion)
                    continue;

                var t2 = sw.ElapsedMilliseconds;

                var site = new Site(uri, content.Result, currentHost);
                Console.WriteLine("Visited site: {0}; {1} ms", site.Url, (t2 - t1));
                SitesVisited.Add(uri, site);
                currentHost.LastVisited = DateTime.Now;

                IEnumerable<string> urls = null;
                try
                {
                    var doc = new HtmlAgilityPack.HtmlDocument();
                    doc.LoadHtml(site.Content);

                    urls =
                        doc.DocumentNode.SelectNodes("//a")
                            .Where(x => x.Attributes["href"] != null)
                            .Select(x => x.Attributes["href"].Value);
                }
                catch (Exception ex)
                {
                    Console.WriteLine(ex.Message);
                }

                int allowed = 0;
                int notAllowed = 0;
                int duplicates = 0;

                if (urls == null)
                    continue;

                foreach (var s in urls)
                {
                    string candiate = "";

                    if (s.StartsWith("http://") || s.StartsWith("https://"))
                        candiate = s;

                    if (s.StartsWith("//"))
                        candiate = uri.Scheme + ":" + s;

                    if (s.StartsWith("/") && !s.StartsWith("//"))
                        candiate = uri.Scheme + "://" + currentHost.Hosturl.Host + s;

                    if (candiate == "")
                        continue;

                    Uri candidateUri;
                    try
                    {
                        candidateUri = new Uri(candiate);
                    }
                    catch (Exception exception)
                    {
                        Console.WriteLine("Candidate failed: " + candiate + "\n" + exception.Message);
                        continue;
                    }

                    if (SitesVisited.ContainsKey(candidateUri))
                        continue;

                    var chost = Host.GetOrCreate(candidateUri, Hosts);

                    if (chost.Robots.IsAllowed(candiate))
                    {
                        if (candiate.Trim().Equals(""))
                        {
                            duplicates++;
                        }
                        else
                        {
                            duplicates += BackQueue.AddToQueue(chost, candidateUri) ? 0 : 1;
                            allowed++;
                        }
                    }
                    else
                    {
                        notAllowed++;
                    }
                }
                Console.WriteLine("{0} sites / {1} seconds = {2} sites pr. second", SitesVisited.Count - StartedWith, sw.Elapsed.TotalSeconds, (SitesVisited.Count - StartedWith) / sw.Elapsed.TotalSeconds);
                Console.WriteLine("Visited {0} sites, {1} to-go, added {2} to queue, and {3} was not allowed. ({4} duplicates)\n", SitesVisited.Count, BackQueue.GetBackQueueCount(), allowed, notAllowed, duplicates);
            }

            return true;
        }
    }
}