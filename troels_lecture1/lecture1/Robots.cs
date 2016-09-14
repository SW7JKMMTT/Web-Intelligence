using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Policy;
using System.Text;
using System.Text.RegularExpressions;

namespace miniproject
{
    public class Robots
    {
        private string rawRobotstxt;

        public List<string> AllowedList = new List<string>();

        public List<string> DisallowedList = new List<string>();

        public bool IsAllowed(string url)
        {


            if (url == "")
                url = "/";

            if (DisallowedList.Any(url.StartsWith) || DisallowedList.Exists(x => x.Trim().Equals("/")))
            {
                return false;
            }

            if (AllowedList.Any(url.StartsWith))
            {
                return true;
            }

            return true;
        }

        public bool IsAllowed(Uri uri)
        {
            var host = uri.Host;
            var abs = uri.AbsolutePath;
            var index = abs.IndexOf(host);
            if (index == -1)
                return IsAllowed(abs);

            var url = abs.Substring(index);
            return IsAllowed(url);
        }

        public Robots()
        {
            rawRobotstxt = "";
        }

        public Robots(string robotsTxt)
        {
            rawRobotstxt = robotsTxt;

            var removedComments = new StringBuilder();

            foreach (var removedComment in rawRobotstxt.Split('\n'))
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

                    if (s.StartsWith("Disallow:"))
                    {
                        DisallowedList.Add(s.Trim().Split(' ').Last());
                    }
                }
            }

            Console.WriteLine("Added " + (AllowedList.Count + DisallowedList.Count) + " rules!");
        }
    }
}