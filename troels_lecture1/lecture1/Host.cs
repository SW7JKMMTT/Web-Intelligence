using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;

namespace miniproject
{
    public class Host
    {
        public string hosturl;

        public Robots robots;

        public DateTime lastVisited;

        public Host(string url, HttpClient httpClient)
        {
            Console.WriteLine("Added host: {0}", url);
            hosturl = url;
            var content = httpClient.GetStringAsync(url + "/robots.txt");

            try
            {
                content.Wait();
            }
            catch (Exception)
            {
                Console.WriteLine("Failed to get robots.txt from {0}", url);
            }

            robots = content.Status == TaskStatus.Faulted ? new Robots() : new Robots(content.Result);

            lastVisited = DateTime.Now;
        }

    }
}