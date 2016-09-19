using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Runtime.Serialization;
using System.Security.Cryptography;
using System.Text;
using NUglify;

namespace lecture1
{
    class Program
    {
        public static IEnumerable<string> nshingle(string input, int shingles)
        {
            input = input.Replace(".", "");
            input = input.Replace(",", "");

            var words = input.Split(' ');
            var shringleList = new List<string>();

            for (int i = 0; i <= words.Count() - shingles; i++)
            {
                StringBuilder stringBuilder = new StringBuilder();
                for (int j = 0; j < shingles; j++)
                {
                    stringBuilder.Append(words[i + j] + " ");
                }

                var str = stringBuilder.ToString();
                if (!shringleList.Contains(str))
                    shringleList.Add(str);
            }

            return shringleList;
        }

        public static double JaccardSimilarity<T>(IEnumerable<T> inputA, IEnumerable<T> inputB)
        {
            var union = inputA.ToList();
            union.AddRange(inputB.Where(s => !inputA.Contains(s)));

            var overlap = inputA.Where(inputB.Contains).ToList();

            return (double)overlap.Count / (double)union.Count;
        }

        public static IEnumerable<R> HashEnumerable<T, R>(IEnumerable<string> input, Func<string, R> Hash)
        {
            return input.Select(x => Hash(x));
        }

        public static bool MinHashCompare<T>(IEnumerable<T> inputA, IEnumerable<T> inputB)
        {
            return inputA.Min().Equals(inputB.Min());
        }

        public static int HashOne(string input)
        {
            return input.GetHashCode();
        }

        public static string HashTwo(string input)
        {
            using (SHA1Managed sha1 = new SHA1Managed())
            {
                var hash = sha1.ComputeHash(Encoding.UTF8.GetBytes(input));

                return string.Concat(Convert.ToBase64String(hash).ToCharArray().Where(x => char.IsLetterOrDigit(x)));
            }
        }

        public static string HashThree(string input)
        {
            using (MD5 md5Hash = MD5.Create())
            {
                byte[] data = md5Hash.ComputeHash(Encoding.UTF8.GetBytes(input));

                StringBuilder sBuilder = new StringBuilder();

                for (int i = 0; i < data.Length; i++)
                {
                    sBuilder.Append(i.ToString("x2"));
                }

                return sBuilder.ToString();
            }
        }

        public static void TestString<T, R>(string inputA, string inputB, Func<string, R> Hash, int shingles)
        {
            var test = nshingle(inputA, shingles);
            var test2 = nshingle(inputB, shingles);

            Console.WriteLine("String A:");
            foreach (var t in test)
            {
                Console.WriteLine(t);
                Console.WriteLine(Hash(t));
            }

            Console.WriteLine("String B:");
            foreach (var t in test2)
            {
                Console.WriteLine(t);
                Console.WriteLine(Hash(t));
            }


            Console.WriteLine(JaccardSimilarity(HashEnumerable<T, R>(test, Hash), HashEnumerable<T, R>(test2, Hash)));

            Console.WriteLine(MinHashCompare(HashEnumerable<T, R>(test, Hash), HashEnumerable<T, R>(test2, Hash)));
        }

        public static List<string> Sketch(string input, int shingles)
        {
            var res = new List<string>();
            var test = nshingle(input, shingles);

            res.Add(HashEnumerable<string, int>(test, HashOne).Min().ToString());
            res.Add(HashEnumerable<string, string>(test, HashTwo).Min());
            res.Add(HashEnumerable<string, string>(test, HashThree).Min());

            return res;
        }

        public static double CompareSketches(IEnumerable<string> inputA, IEnumerable<string> inputB)
        {
            var matches = 0;
            foreach (var s in inputA)
            {
                if (inputB.Contains(s))
                    matches++;
            }

            return (double)matches / (double)inputA.Count();
        }

        static void Main(string[] args)
        {
            //TestString<string, int>("do not worry about your difficulties in mathematics", "i would not worry about your difficulties, you can easily learn what is needed.", HashOne, 3);
            //TestString<string, string>("do not worry about your difficulties in mathematics", "i would not worry about your difficulties, you can easily learn what is needed.", HashTwo, 3);
            //TestString<string, string>("do not worry about your difficulties in mathematics", "i would not worry about your difficulties, you can easily learn what is needed.", HashThree, 3);

            //var sketchA = Sketch("do not worry about your difficulties in mathematics", 3);
            //var sketchB = Sketch("i would not worry about your dificulties, you can easily learn what is needed.", 3);

            //foreach (var s in sketchA)
            //{
            //    Console.WriteLine(s);
            //}

            //foreach (var s in sketchB)
            //{
            //    Console.WriteLine(s);
            //}

            // Console.WriteLine(CompareSketches(sketchA, sketchB));

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

            //var hosts = websiteUrls.Select(websiteUrl => new Host(websiteUrl, httpClient)).ToList();

            //Console.WriteLine(hosts.First(x => x.hosturl.Contains("google.dk")).robots.IsAllowed("/derp"));

            var seedUrl = new List<Uri> { new Uri("http://dr.dk") };
            var crawler = RestoreCrawler(seedUrl, new List<Host>(), httpClient, 100);

            Console.CancelKeyPress += delegate
            {
                SaveCrawler(crawler);
            };

            crawler.Run();
            SaveCrawler(crawler);

            var tokenizor = RestoreTokenizor();

            foreach (var site in crawler.SitesVisited.Values)
            {
                tokenizor.MakeTokens(site);
            }

            SaveTokenizor(tokenizor);

            foreach (var token in tokenizor.Tokens.OrderByDescending(x => x.Value.Uris.Sum(y => y.Value)).Take(100))
            {
                Console.WriteLine(token.Key + ": " + token.Value.Uris.Sum(x => x.Value));
            }
        }

        public static Crawler RestoreCrawler(List<Uri> seedUris, List<Host> hosts, HttpClient httpClient, int limit)
        {
            var crawlerSerialser = new DataContractSerializer(typeof(Crawler), null, 1000000, false, true, null);

            Stream crawlerStream = new FileStream("crawler.bin", FileMode.OpenOrCreate, FileAccess.Read, FileShare.None);

            if (crawlerStream.Length != 0) { 
                var crawler = (Crawler) crawlerSerialser.ReadObject(crawlerStream);
                crawlerStream.Close();
                crawler.httpClient = httpClient;
                crawler.startedWith = crawler.SitesVisited.Count;
                crawler.limit = limit;
                Console.WriteLine("Restore crawler state: {0} sites, {1} hosts", crawler.SitesVisited.Count, crawler.hosts.Count);
                return crawler;
            }
            
            return new Crawler(seedUris, hosts, httpClient, limit);
        }

        public static void SaveCrawler(Crawler crawler)
        {
            var crawlerSerialser = new DataContractSerializer(typeof(Crawler), null, 1000000, false, true, null);
            Stream crawlerStream = new FileStream("crawler.bin", FileMode.Create, FileAccess.Write, FileShare.None);

            crawlerSerialser.WriteObject(crawlerStream, crawler);
            crawlerStream.Close();
            Console.WriteLine("Saved crawler state: {0} sites, {1} hosts", crawler.SitesVisited.Count, crawler.hosts.Count);
        }

        public static Tokenizor RestoreTokenizor()
        {
            var tokenizorSerialser = new DataContractSerializer(typeof(Tokenizor), null, 1024 * 1024 * 1024, false, true, null);
            var tokenizorStream = new FileStream("tokens.bin", FileMode.OpenOrCreate, FileAccess.Read, FileShare.None);

            if (tokenizorStream.Length != 0)
            {
                var tokenizor = (Tokenizor) tokenizorSerialser.ReadObject(tokenizorStream);
                tokenizorStream.Close();
                Console.WriteLine("Restored Tokenizor state: {0} tokens", tokenizor.Tokens.Count);
                return tokenizor;
            }

            return new Tokenizor();
        }

        public static void SaveTokenizor(Tokenizor tokenizor)
        {
            var tokenizorSerialser = new DataContractSerializer(typeof(Tokenizor), null, 1024 * 1024 * 1024, false, true, null);
            var tokenizorStream = new FileStream("tokens.bin", FileMode.Create, FileAccess.Write, FileShare.None);
            
            tokenizorSerialser.WriteObject(tokenizorStream, tokenizor);
            tokenizorStream.Close();
        }
    }
}
