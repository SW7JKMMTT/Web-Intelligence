using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;

namespace miniproject1.DataStructures
{
    [Serializable]
    public class Robots
    {
        private string _rawRobotstxt;

        public List<string> AllowedList = new List<string>();

        public List<string> DisallowedList = new List<string>();

        public bool IsAllowed(string url)
        {
            if (url == "")
                url = "/";

            if (AllowedList.Any(url.StartsWith))
            {
                return true;
            }

            if (DisallowedList.Any(url.StartsWith) || DisallowedList.Exists(x => x.Trim().Equals("/")))
            {
                return false;
            }

            return true;
        }

        public bool IsAllowed(Uri uri)
        {
            var host = uri.Host;
            var abs = uri.AbsolutePath;
            var index = abs.IndexOf(host, StringComparison.Ordinal);
            if (index == -1)
                return IsAllowed(abs);

            var url = abs.Substring(index);
            return IsAllowed(url);
        }

        public Robots()
        {
            _rawRobotstxt = "";
        }

        public Robots(string robotsTxt, Host parentHost)
        {
            _rawRobotstxt = robotsTxt;

            var removedComments = new StringBuilder();

            foreach (var removedComment in _rawRobotstxt.Split('\n'))
            {
                if (!removedComment.StartsWith("#"))
                    removedComments.Append(removedComment + "\n");
            }

            var split = Regex.Split(removedComments.ToString(), "User-agent:", RegexOptions.Compiled);

            var firstOrDefault = split.FirstOrDefault(x => x.Trim().StartsWith("*") || x.Trim().ToLowerInvariant().StartsWith("user-agent: *"));
            if (firstOrDefault != null)
            {
                var wildcard = firstOrDefault.Split('\n');

                foreach (var s in wildcard)
                {
                    if (s.StartsWith("Allow:"))
                    {
                        AllowedList.Add(s.Trim().Split(' ').Last());
                    }
                    else if (s.StartsWith("Disallow:"))
                    {
                        DisallowedList.Add(s.Trim().Split(' ').Last());
                    }
                    else if (s.StartsWith("Crawl-delay:"))
                    {
                        var time = s.Trim().Split(' ').Last();
                        Console.WriteLine("Found Crawl-delay for: {0}: {1} sec", parentHost.Hosturl, time);
                        parentHost.CrawlDelay = TimeSpan.FromSeconds(int.Parse(time));
                    }
                }

                Console.WriteLine("{0}: Added {1} rules!", parentHost.Hosturl.Host, (AllowedList.Count + DisallowedList.Count));
            }
            else
            {
                Console.WriteLine("Couldn't find any rules for '*'");
            }
        }
    }
}