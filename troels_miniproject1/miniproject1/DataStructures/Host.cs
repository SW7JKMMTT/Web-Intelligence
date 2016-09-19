using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Threading.Tasks;

namespace miniproject1.DataStructures
{
    [Serializable]
    public class Host : IComparable<Host>
    {
        public Uri Hosturl;

        public Robots Robots;

        [NonSerialized]
        public Task<string> RobotstextTask;

        public DateTime LastVisited;

        public int Id = -1;

        public TimeSpan CrawlDelay = new TimeSpan(0, 0, 1);

        public Host(Uri url)
        {
            //Console.WriteLine("Added host: {0}", url);
            Hosturl = url;
            Robots = new Robots();
            LastVisited = DateTime.Now;
        }

        public void WaitForRobots(HttpClient httpClient)
        {
            if (RobotstextTask != null && RobotstextTask.IsCompleted)
                return;

            RobotstextTask = httpClient.GetStringAsync(Hosturl.Scheme + "://" + Hosturl.Host + "/robots.txt");

            try
            {
                RobotstextTask.Wait();
            }
            catch (Exception)
            {
                Console.WriteLine("Failed to get robots.txt from {0}", Hosturl.Host);
            }

            Robots = RobotstextTask.Status != TaskStatus.RanToCompletion ? new Robots() : new Robots(RobotstextTask.Result, this);
        }

        public static Host GetOrCreate(Uri url, List<Host> hosts)
        {
            var host = hosts.FirstOrDefault(x => x.Hosturl.Host == url.Host);
            if (host == null)
            {
                var hosturi = new Uri(url.Scheme + "://" + url.Host);
                host = new Host(hosturi);
                hosts.Add(host);
                host.Id = hosts.Count;
            }

            return host;
        }

        public int CompareTo(Host other)
        {
            return Id - other.Id;
        }

        public bool IsReady()
        {
            return DateTime.Now > LastVisited + CrawlDelay;
        }


    }
}