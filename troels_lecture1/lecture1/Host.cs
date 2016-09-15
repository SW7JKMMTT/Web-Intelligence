using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Security.Policy;
using System.Threading.Tasks;
using miniproject;

namespace lecture1
{
    public class Host : IComparable<Host>
    {
        public Uri hosturl;

        public Robots robots;

        private Task<string> robotstextTask = null;

        public DateTime lastVisited;

        public int id = -1;

        public Host(Uri url)
        {
            //Console.WriteLine("Added host: {0}", url);
            hosturl = url;
            robots = new Robots();
            lastVisited = DateTime.Now;
        }

        public void WaitForRobots(HttpClient httpClient)
        {
            if (robotstextTask != null && robotstextTask.IsCompleted)
                return;

            robotstextTask = httpClient.GetStringAsync(hosturl.Scheme + "://" + hosturl.Host + "/robots.txt");

            try
            {
                robotstextTask.Wait();
            }
            catch (Exception)
            {
                Console.WriteLine("Failed to get robots.txt from {0}", hosturl.Host);
            }

            robots = robotstextTask.Status != TaskStatus.RanToCompletion ? new Robots() : new Robots(robotstextTask.Result);
        }

        public static Host GetOrCreate(Uri url, List<Host> hosts)
        {
            var host = hosts.FirstOrDefault(x => x.hosturl.Host == url.Host);
            if (host == null)
            {
                var hosturi = new Uri(url.Scheme + "://" + url.Host);
                host = new Host(hosturi);
                hosts.Add(host);
                host.id = hosts.Count;
            }
            
            return host;
        }

        public int CompareTo(Host other)
        {
            return this.lastVisited.CompareTo(other.lastVisited);
        }
    }
}