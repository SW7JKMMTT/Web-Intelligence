using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Runtime.Serialization;
using System.Threading;
using miniproject1.DataStructures;
using miniproject1.Indexer;
using NUglify.Helpers;

namespace miniproject1.Persistence
{
    public static class SerializationHelper
    {
        public static Crawler.Crawler RestoreCrawler(List<Uri> seedUris, List<Host> hosts, HttpClient httpClient, int limit)
        {
            var crawlerSerialser = new DataContractSerializer(typeof(Crawler.Crawler), null, 1024 * 1024 * 1024, false, true, null);

            Stream crawlerStream = new FileStream("crawler.bin", FileMode.OpenOrCreate, FileAccess.Read, FileShare.None);

            if (crawlerStream.Length > 100)
            {
                Crawler.Crawler crawler;
                try
                {
                    crawler = (Crawler.Crawler)crawlerSerialser.ReadObject(crawlerStream);
                }
                catch (Exception ex)
                {
                    Console.WriteLine(ex);
                    crawlerStream.Close();
                    return new Crawler.Crawler(seedUris, hosts, httpClient, limit);
                }
                crawler.HttpClient = httpClient;
                crawler.StartedWith = crawler.SitesVisited.Count;
                crawler.Limit = limit;
                crawler.BackQueue.DequeueMutex = new Mutex();
                crawler.BackQueue.EnqueueMutex = new Mutex();
                crawler.BackQueue.cntMutex = new Mutex();
                var now = DateTime.Now - TimeSpan.FromSeconds(1);
                crawler.BackQueue.BackQueueMap.ForEach(x => x.Key.LastVisited = now);
                crawler.BackQueue.BackQueueMap.ForEach(x => x.Key.CreateMutex());
                Console.WriteLine("Restore crawler state: {0} sites, {1} hosts, {2} URLs in back-queue", crawler.SitesVisited.Count, Host.Count(), crawler.BackQueue.GetBackQueueCount());
                crawlerStream.Close();
                return crawler;
            }

            crawlerStream.Close();
            return new Crawler.Crawler(seedUris, hosts, httpClient, limit);
        }

        public static void SaveCrawler(Crawler.Crawler crawler)
        {
            var crawlerSerialser = new DataContractSerializer(typeof(Crawler.Crawler), null, 1024 * 1024 * 1024, false, true, null);
            Stream crawlerStream = new FileStream("crawler.bin", FileMode.Create, FileAccess.Write, FileShare.None);

            crawlerSerialser.WriteObject(crawlerStream, crawler);
            crawlerStream.Close();
            Console.WriteLine("Saved crawler state: {0} sites, {1} hosts, {2} URLs in back-queue", crawler.SitesVisited.Count, Host.Count(), crawler.BackQueue.GetBackQueueCount());
        }

        public static Index RestoreIndex()
        {
            var indexSerialser = new DataContractSerializer(typeof(Index), null, 1024 * 1024 * 1024, false, true, null);
            var indexStream = new FileStream("index.bin", FileMode.OpenOrCreate, FileAccess.Read, FileShare.None);

            if (indexStream.Length != 0)
            {
                var indexer = (Index)indexSerialser.ReadObject(indexStream);
                indexStream.Close();
                Console.WriteLine("Restored indexer state: {0} tokens", indexer.Tokens.Count);
                return indexer;
            }

            indexStream.Close();
            return new Index();
        }

        public static void SaveIndex(Index index)
        {
            var indexSerialser = new DataContractSerializer(typeof(Index), null, 1024 * 1024 * 1024, false, true, null);
            var indexStream = new FileStream("tokens.bin", FileMode.Create, FileAccess.Write, FileShare.None);

            indexSerialser.WriteObject(indexStream, index);
            indexStream.Close();
        }
    }
}