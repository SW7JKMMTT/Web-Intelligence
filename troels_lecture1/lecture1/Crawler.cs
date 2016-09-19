using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;

namespace lecture1
{
    [Serializable]
    public class Crawler
    {
        public BackQueue BackQueue;

        [NonSerialized]
        public HttpClient httpClient;

        public List<Host> hosts;

        public Dictionary<Uri, Site> SitesVisited = new Dictionary<Uri, Site>();

        public int limit = 0;

        public int startedWith = 0;

        public Crawler(IEnumerable<Uri> url, IEnumerable<Host> hosts, HttpClient httpClient, int limit)
        {
            this.hosts = hosts.ToList();

            this.httpClient = httpClient;

            //InitFromDisk();

            if(BackQueue == null)
                BackQueue = new BackQueue();
            
            foreach (var u in url)
            {
                //var host = new Host(u, httpClient);
                var host = Host.GetOrCreate(u, this.hosts);
                BackQueue.AddToQueue(host, u);
            }

            this.limit = limit;
        }

        //public void WriteToDisk()
        //{
        //    var formatter = new BinaryFormatter();

        //    var hostSerialiser = new DataContractSerializer(typeof(List<Host>), null, 1000000, false, true, null);
        //    var sitesSerialiser = new DataContractSerializer(typeof(List<Site>), null, 1000000, false, true, null);
        //    var backQueueSerialiser = new DataContractSerializer(typeof(BackQueue), null, 1000000, false, true, null);



        //    Stream hostsStream = new FileStream("hosts.bin", FileMode.Create, FileAccess.Write, FileShare.None);
        //    Stream sitesStream = new FileStream("sites.bin", FileMode.Create, FileAccess.Write, FileShare.None);
        //    Stream backQueueStream = new FileStream("backQueue.bin", FileMode.Create, FileAccess.Write, FileShare.None);

        //    //formatter.Serialize(hostsStream, hosts);
        //    //formatter.Serialize(sitesStream, SitesVisited);
        //    //formatter.Serialize(backQueueStream, BackQueue);
        //    hostSerialiser.WriteObject(hostsStream, hosts);
        //    sitesSerialiser.WriteObject(sitesStream, SitesVisited);
        //    backQueueSerialiser.WriteObject(backQueueStream, BackQueue);

            
        //    hostsStream.Close();
        //    sitesStream.Close();
        //    backQueueStream.Close();
        //}

        //public void InitFromDisk()
        //{
        //    var hostSerialiser = new DataContractSerializer(typeof(List<Host>), null, 1000000, false, true, null);
        //    var sitesSerialiser = new DataContractSerializer(typeof(List<Site>), null, 1000000, false, true, null);
        //    var backQueueSerialiser = new DataContractSerializer(typeof(BackQueue), null, 1000000, false, true, null);


        //    Stream hostsStream = new FileStream("hosts.bin", FileMode.OpenOrCreate, FileAccess.Read, FileShare.None);
        //    Stream sitesStream = new FileStream("sites.bin", FileMode.OpenOrCreate, FileAccess.Read, FileShare.None);
        //    Stream backQueueStream = new FileStream("backQueue.bin", FileMode.OpenOrCreate, FileAccess.Read, FileShare.None);

        //    if (hostsStream.Length == 0 || sitesStream.Length == 0 || backQueueStream.Length == 0)
        //    {
        //        Console.WriteLine("Some data on disk was empty, starting over! ");
        //    }
        //    else
        //    {
        //        hosts = (List<Host>)hostSerialiser.ReadObject(hostsStream);
        //        SitesVisited = (List<Site>) sitesSerialiser.ReadObject(sitesStream);
        //        BackQueue = (BackQueue) backQueueSerialiser.ReadObject(backQueueStream);
        //        Console.WriteLine("{0} hosts loaded!!", hosts.Count);
        //        Console.WriteLine("{0} sites loaded!!", SitesVisited.Count);
        //        Console.WriteLine("{0} urls added to backqueue!!", BackQueue.GetBackQueueCount());
        //    }
            
        //    hostsStream.Close();
        //    sitesStream.Close();
        //    backQueueStream.Close();
        //}

        public bool Run()
        {
            Stopwatch sw = Stopwatch.StartNew();
            while (BackQueue.GetBackQueueCount() > 0 && SitesVisited.Count < limit)
            {

                Uri uri = BackQueue.GetSite();
                var currentHost = Host.GetOrCreate(uri, hosts);

                if (!currentHost.robots.IsAllowed(uri))
                {
                    Console.WriteLine("Url (\"{0}\") not allowed on this host (\"{1}\")", uri, uri.Host);
                    continue;
                }

                var earliestNextVisit = currentHost.lastVisited + currentHost.crawlDelay;
                if (earliestNextVisit > DateTime.Now)
                {
                    Console.WriteLine("Sleeping for " + (earliestNextVisit - DateTime.Now) + " ms");
                    Thread.Sleep(earliestNextVisit - DateTime.Now);
                }

                currentHost.WaitForRobots(httpClient);
                var t1 = sw.ElapsedMilliseconds;
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

                var t2 = sw.ElapsedMilliseconds;

                var site = new Site(uri, content.Result, currentHost);
                Console.WriteLine("Visited site: {0}; {1} ms", site.url, (t2 - t1));
                SitesVisited.Add(uri, site);
                currentHost.lastVisited = DateTime.Now;

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
                    

                    //if (SitesVisited.Any(x => x.url.Equals(candidateUri)))
                    //    continue;

                    if (SitesVisited.ContainsKey(candidateUri))
                    {
                        continue;
                    }

                    var chost = Host.GetOrCreate(candidateUri, hosts);


                    if (chost.robots.IsAllowed(candiate))
                    {
                        if (!candiate.Trim().Equals(""))
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
                Console.WriteLine("{0} sites / {1} seconds = {2} sites pr. second", SitesVisited.Count - startedWith, sw.Elapsed.TotalSeconds, (double)((SitesVisited.Count - startedWith) / sw.Elapsed.TotalSeconds));
                Console.WriteLine("Visited {0} sites, {1} to-go, added {2} to queue, and {3} was not allowed. ({4} duplicates)\n", SitesVisited.Count, BackQueue.GetBackQueueCount(), allowed, notAllowed, duplicates);
            }

            return true;
        }
    }
}