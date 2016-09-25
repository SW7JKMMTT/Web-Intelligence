using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using HtmlAgilityPack;
using miniproject1.DataStructures;
using NUglify.Helpers;

namespace miniproject1.Crawler
{
    [Serializable]
    public class Crawler
    {
        public ConcurrentDictionary<string, Host> Hosts = new ConcurrentDictionary<string, Host>();

        public BackQueue BackQueue;

        public ConcurrentDictionary<Uri, Site> SitesVisited = new ConcurrentDictionary<Uri, Site>();

        public int Limit;

        public int StartedWith = 0;

        public int QueueMaxSize = 10000;

        public Crawler(IEnumerable<Uri> url, IEnumerable<Host> initialHosts, int limit)
        {
            initialHosts.ForEach(x => Host.GetOrCreate(x.Hosturl, Hosts));

            if (BackQueue == null)
                BackQueue = new BackQueue();

            foreach (var u in url)
            {
                var host = Host.GetOrCreate(u, Hosts);
                BackQueue.AddToQueue(host, u);
            }

            Limit = limit;
        }

        public async Task<Site> GetFromQueue()
        {
            var uri = BackQueue.GetSite();
            var currentHost = Host.GetOrCreate(uri, Hosts);
            currentHost.GetMutex();
            var sw = new Stopwatch();
            sw.Start();

            if (!currentHost.Robots.IsAllowed(uri))
            {
                Console.WriteLine("Url (\"{0}\") not allowed on this host (\"{1}\")", uri, uri.Host);
                return null;
            }

            var earliestNextVisit = currentHost.LastVisited + currentHost.CrawlDelay;
            if (earliestNextVisit > DateTime.Now)
            {
                Console.WriteLine("Sleeping for " + (earliestNextVisit - DateTime.Now) + " ms");
                Thread.Sleep(earliestNextVisit - DateTime.Now);
            }

            var client = GetDownloader();

            currentHost.WaitForRobots(client);
            var t1 = sw.ElapsedMilliseconds;
            Task<string> contentTask = null;
            try
            {
                contentTask = client.GetStringAsync(uri);
                contentTask.Wait();
            }
            catch (AggregateException)
            {
                Console.WriteLine("Failed to get: {0}", uri);
                currentHost.LastVisited = DateTime.Now;
                currentHost.ReleaseMutex();
                return null;
            }
            catch (TaskCanceledException ex)
            {
                currentHost.ReleaseMutex();
                return null;
            }
            catch (Exception ex)
            {
                currentHost.ReleaseMutex();
                return null;
            }

            var content = contentTask.Result;

            currentHost.ReleaseMutex();

            if (String.IsNullOrEmpty(content))
                return null;

            var t2 = sw.ElapsedMilliseconds;

            var site = new Site(uri, content, currentHost);
            Console.WriteLine("Visited site: {0}; {1} ms", site.Url, (t2 - t1));
            SitesVisited.TryAdd(uri, site);
            currentHost.LastVisited = DateTime.Now;

            return site;
        }

        public async void AddNewUrlsToQueue(Site site)
        {
            if(SitesVisited.Count + QueueMaxSize < BackQueue.GetBackQueueCount())
                return;

            var uri = site.Url;
            var currentHost = site.Host;

            IEnumerable<string> urls = null;
            try
            {
                var doc = new HtmlDocument();
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

            var allowed = 0;
            var notAllowed = 0;
            var duplicates = 0;

            if (urls == null)
                return;

            foreach (var s in urls)
            {
                var candiate = "";

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

            //Console.WriteLine("Visited {0} sites, {1} to-go, added {2} to queue, and {3} was not allowed. ({4} duplicates)\n", SitesVisited.Count, BackQueue.GetBackQueueCount(), allowed, notAllowed, duplicates);
        }

        public async Task CrawlTask()
        {
            var site = await GetFromQueue();
            if (site == null)
                return;

            await Task.Run(() => AddNewUrlsToQueue(site));
        }

        public async Task StartRunner(int i)
        {
            while (BackQueue.GetBackQueueCount() > 0 && SitesVisited.Count < Limit && Hosts.Count >= i)
            {
                Console.WriteLine(i + " started");
                await CrawlTask();
                Console.WriteLine(i + " ended");
            }
        }

        public async void Run()
        {
            int threads = 4;
            Task.Run(() => PrintStatus());
            while (BackQueue.GetBackQueueCount() > 0 && SitesVisited.Count < Limit)
            {
                Console.WriteLine("Starting new tasks!");
                Task.WhenAll(Enumerable.Range(SitesVisited.Count, SitesVisited.Count + Math.Min(threads, Hosts.Count)).Select(i => CrawlTask())).GetAwaiter().GetResult();
            }

        }

        public async void PrintStatus()
        {
            var sw = Stopwatch.StartNew();
            while (true)
            {
                Console.WriteLine("{0} sites / {1} seconds = {2} sites pr. second", SitesVisited.Count - StartedWith,
                sw.Elapsed.TotalSeconds, (SitesVisited.Count - StartedWith)/sw.Elapsed.TotalSeconds);
                Thread.Sleep(1000);
            }
        }

        public HttpClient GetDownloader()
        {
            var httpClientHandler = new HttpClientHandler()
            {
                AllowAutoRedirect = true,
                MaxAutomaticRedirections = 100,
                CookieContainer = new CookieContainer()
            };

            var httpClient = new HttpClient(httpClientHandler) { Timeout = new TimeSpan(0, 0, 1) };
            httpClient.DefaultRequestHeaders.Add("user-agent", "Mozilla/5.0 SataiCrawler");


            return httpClient;
        }
    }
}