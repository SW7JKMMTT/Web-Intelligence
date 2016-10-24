using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Security.Cryptography.X509Certificates;
using System.Threading;
using System.Threading.Tasks;
using Nito.AsyncEx;

namespace miniproject1.DataStructures
{
    [Serializable]
    public class Host : IComparable<Host>
    {

        [NonSerialized]
        private volatile Mutex _hostMutex = new Mutex();

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
            _hostMutex.WaitOne();
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
            _hostMutex.ReleaseMutex();
        }

        public static Host GetOrCreate(Uri url, ConcurrentDictionary<string, Host> hosts)
        {
            //var host = hosts.FirstOrDefault(x => x.Hosturl.Host == url.Host);
            //var host = hosts[url.Host];
            Host host;
            if (!hosts.TryGetValue(url.Host, out host))
            {
                var hosturi = new Uri(url.Scheme + "://" + url.Host);
                host = new Host(hosturi);
                hosts[url.Host] = host;
                host.Id = hosts.Count;
            }

            return host;
        }

        public static int Count(ConcurrentDictionary<string, Host> hosts)
        {
            return hosts.Count;
        }

        public int CompareTo(Host other)
        {
            return Id - other.Id;
        }

        public bool IsReady()
        {
            return DateTime.Now > LastVisited + CrawlDelay;
        }

        public void GetMutex()
        {
            _hostMutex.WaitOne();
        }

        public void ReleaseMutex()
        {
            _hostMutex.ReleaseMutex();
            LastVisited = DateTime.Now;
        }

        public void CreateMutex()
        {
            _hostMutex = new Mutex();
        }
    }
}