using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text.RegularExpressions;
using miniproject1.DataStructures;
using miniproject1.Indexer;
using miniproject1.Persistence;

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

            var httpClientHandler = new HttpClientHandler()
            {
                AllowAutoRedirect = true,
                MaxAutomaticRedirections = 100,
                CookieContainer = new CookieContainer()
            };

            var httpClient = new HttpClient(httpClientHandler) { Timeout = new TimeSpan(0, 0, 5) };
            httpClient.DefaultRequestHeaders.Add("user-agent", "Mozilla/5.0 SataiCrawler");

            var seedUrl = new List<Uri> { new Uri("http://dr.dk") };
            var crawler = SerializationHelper.RestoreCrawler(seedUrl, new List<Host>(), httpClient, 100);

            Console.CancelKeyPress += delegate
            {
                SerializationHelper.SaveCrawler(crawler);
            };

            crawler.Run();
            SerializationHelper.SaveCrawler(crawler);

            var indexer = new Index();

            foreach (var site in crawler.SitesVisited.Values)
            {
                Tokenizor.AddTokensToTokenList(site, indexer.Tokens);
            }

            SerializationHelper.SaveIndex(indexer);

            // Find "weird" tokens
            foreach (var token in indexer.Tokens
                .OrderByDescending(x => x.Value.Uris.Sum(y => y.Value))
                .Where(x => !Regex.IsMatch(x.Key, @"^[a-zA-Z0-9æøåÆØÅ-]+$"))
                .Take(100))
            {
                Console.WriteLine(token.Key + ": " + token.Value.Uris.Sum(x => x.Value));
            }

            Console.WriteLine("Text only tokens: " + indexer.Tokens.Count(x => Regex.IsMatch(x.Key, @"^[a-zA-Z]+$")));
            Console.WriteLine("Text/Number only tokens: " + indexer.Tokens.Count(x => Regex.IsMatch(x.Key, @"^[a-zA-Z0-9]+$")));
            Console.WriteLine("Text/Number/dash only tokens: " + indexer.Tokens.Count(x => Regex.IsMatch(x.Key, @"^[a-zA-Z0-9-]+$")));
            Console.WriteLine("Total tokens: " + indexer.Tokens.Count);
        }
    }
}
