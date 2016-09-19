using System;
using System.Collections.Generic;
using System.Linq;
using miniproject1.DataStructures;

namespace miniproject1.Crawler
{
    [Serializable]
    public class BackQueue
    {
        public readonly SortedDictionary<Host, Queue<Uri>> BackQueueMap;

        public BackQueue()
        {
            BackQueueMap = new SortedDictionary<Host, Queue<Uri>>();
        }

        public bool AddToQueue(Host host, Uri uri)
        {
            var containsKey = BackQueueMap.ContainsKey(host);

            if (!containsKey)
            {
                if (BackQueueMap.Any(x => x.Key.Hosturl.Host == host.Hosturl.Host))
                    Console.WriteLine("WTF wat");

                BackQueueMap.Add(host, new Queue<Uri>());
            }

            // This call is _HOT_, might replace with something else? A HashMap/dict perhaps. 
            if (BackQueueMap[host].Contains(uri))
                return false;

            BackQueueMap[host].Enqueue(uri);
            return true;
        }

        public Uri GetSite()
        {
            var candidate = BackQueueMap.Where(x => x.Key.IsReady() && x.Value.Count > 0);

            if (candidate.FirstOrDefault().Value == null)
            {
                return BackQueueMap.FirstOrDefault(x => x.Value.Count > 0).Value.Dequeue();
            }

            return candidate.FirstOrDefault().Value.Dequeue();
        }

        public int GetBackQueueCount()
        {
            return BackQueueMap.Sum(x => x.Value.Count);
        }
    }
}
