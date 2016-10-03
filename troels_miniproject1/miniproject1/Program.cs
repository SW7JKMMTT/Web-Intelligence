using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using miniproject1.DataStructures;
using miniproject1.Indexer;
using miniproject1.Persistence;
using miniproject1.Searcher;

namespace miniproject1
{
    class Program
    {
        static void Main(string[] args)
        {
            var websiteUrls = new List<Uri>();
            //websiteUrls.Add(@"https://en.wikipedia.org");
            //websiteUrls.Add(@"https://www.satai.dk");
            //websiteUrls.Add(@"https://www.google.dk");
            //websiteUrls.Add(@"http://stackoverflow.com");
            //websiteUrls.Add(@"https://news.ycombinator.com");
            //websiteUrls.Add(@"https://twitter.com");
            //websiteUrls.Add(@"http://www.mmo-champion.com");
            //websiteUrls.Add(@"http://www.imdb.com");
            //websiteUrls.Add(@"https://www.instagram.com");
            //websiteUrls.Add(@"https://www.youtube.com");



            var seedUrl = new List<Uri>
            {
                new Uri("http://dr.dk"),
                new Uri("https://en.wikipedia.org"),
                new Uri("https://news.ycombinator.com"),
                new Uri("http://www.mmo-champion.com"),
                new Uri("https://msdn.microsoft.com")
            };

            var crawler = SerializationHelper.RestoreCrawler(seedUrl, new List<Host>(), 1000);

            

            if (crawler.Limit >= crawler.SitesVisited.Count)
            {
                Task.Run(() => crawler.Run()).GetAwaiter().GetResult();
                SerializationHelper.SaveCrawler(crawler);
            }

            var indexer = new Index();

            var sw = Stopwatch.StartNew();
            foreach (var site in crawler.SitesVisited.Values)
            {
                Tokenizor.AddTokensToTokenList(site, indexer.Tokens);
            }
            Console.WriteLine("Indexing {0} documents took {1} ms ({2} pr. sec)", crawler.SitesVisited.Count, sw.ElapsedMilliseconds, (double)crawler.SitesVisited.Count / (sw.ElapsedMilliseconds / 1000));

            //SerializationHelper.SaveIndex(indexer);


            //TestTFIDF(indexer);
            //TestBooleanSearcher(indexer);
            //TestTokenSearcher(indexer);

            string s;

            do
            {
                Console.Write("Enter search Query: ");
                s = Console.ReadLine();
                if (s == null)
                    continue;

                TestTokenSearcher(indexer, s, crawler.SitesVisited.Count);

            } while (s != "");

            //Console.Write("Enter search Query: ");
            //while ((s = Console.ReadLine()) != "")
            //{
            //    if(s == null)
            //        continue;

            //    TestTokenSearcher(indexer, s);
            //    Console.Write("Enter search Query: ");
            //}
        }

        public static void TestTokenSearcher(Index indexer, string searchstring, int documents)
        {
            var ts = new TokenSearcher(indexer);

            var tokens = Tokenizor.StringToToken(searchstring, indexer.Tokens).ToList();

            var searchres = ts.OrderByScore(tokens, ts.And(tokens), documents).OrderByDescending(x => x.Item1);

            Console.WriteLine("Found {0} results for \"{1}\":", searchres.Count(), searchstring);

            foreach (var t in searchres.Take(50))
            {
                Console.WriteLine("{0,10:N7}: {1}", t.Item1, t.Item2.Url);
            }
        }

        public static void TestTFIDF(Index indexer)
        {
            var n = 100;

            var tokens = indexer.Tokens.Where(x => Regex.IsMatch(x.Key, @"^[a-zA-ZæøåÆØÅ-]+$")).Take(n);

            Console.WriteLine(" {0,20} | {1,20} | {2,20} | {3,20} | {4,20}",
                "Token:",
                "CollectionFreq",
                "DocumentFreq",
                "InvDocumentFreq",
                "LogInvDocumentFreq");

            Console.WriteLine("{0}|{0}|{0}|{0}|{0}|{0}", new string('-', 22));
            foreach (var token in tokens.OrderByDescending(x => x.Value.InverseDocumentFrequency(n)).Select(x => x.Value))
            {
                Console.WriteLine(" {0,20} | {1,20} | {2,20} | {3,20:N3} | {4,20:N5}",
                    token.TokenText,
                    token.CollectionFrequency(),
                    token.DocumentFrequency(),
                    token.InverseDocumentFrequency(n),
                    token.LogInverseDocumentFrequency(n, Math.E));
            }
        }

        public static void TestIndex(Index indexer)
        {
            //// Find "weird" tokens
            //foreach (var token in indexer.Tokens
            //    .OrderByDescending(x => x.Value.Uris.Sum(y => y.Value))
            //    .Where(x => !Regex.IsMatch(x.Key, @"^[a-zA-Z0-9æøåÆØÅ-]+$"))
            //    .Take(100))
            //{
            //    Console.WriteLine(token.Key + ": " + token.Value.Uris.Sum(x => x.Value));
            //}

            Console.WriteLine("Text only tokens: " + indexer.Tokens.Count(x => Regex.IsMatch(x.Key, @"^[a-zA-Z]+$")));
            Console.WriteLine("Text/Number only tokens: " + indexer.Tokens.Count(x => Regex.IsMatch(x.Key, @"^[a-zA-Z0-9]+$")));
            Console.WriteLine("Text/Number/dash only tokens: " + indexer.Tokens.Count(x => Regex.IsMatch(x.Key, @"^[a-zA-Z0-9-]+$")));
            Console.WriteLine("Total tokens: " + indexer.Tokens.Count);
        }

        public static void TestBooleanSearcher(Index indexer)
        {
            var bs = new BooleanSearcher(indexer);

            foreach (var res in bs.And("dr", bs.Or("p3", "p4")))
            {
                Console.WriteLine(res);
            }
        }
    }
}
