using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using miniproject1.DataStructures;

namespace miniproject1.Crawler
{
    [Serializable]
    public class BackQueue
    {
        public readonly SortedDictionary<Host, Queue<Uri>> BackQueueMap;

        public ConcurrentDictionary<Uri, bool> SitesSeen = new ConcurrentDictionary<Uri, bool>();

        [NonSerialized]
        public Mutex DequeueMutex = new Mutex();

        [NonSerialized]
        public Mutex EnqueueMutex = new Mutex();

        [NonSerialized] 
        public Mutex cntMutex = new Mutex();

        private int BackQueueSize;

        public BackQueue()
        {
            BackQueueSize = 0;
            BackQueueMap = new SortedDictionary<Host, Queue<Uri>>();
        }

        public bool AddToQueue(Host host, Uri uri)
        {
            EnqueueMutex.WaitOne();
            var containsKey = BackQueueMap.ContainsKey(host);

            if (!containsKey)
            {
                if (BackQueueMap.Any(x => x.Key.Hosturl.Host == host.Hosturl.Host))
                    Console.WriteLine("WTF wat");

                BackQueueMap.Add(host, new Queue<Uri>());
            }

            // This call is _HOT_, might replace with something else? A HashMap/dict perhaps. 
            //if (BackQueueMap[host].Contains(uri))
            //{
            //    EnqueueMutex.ReleaseMutex();
            //    return false;
            //}

            if (SitesSeen.ContainsKey(uri))
            {
                EnqueueMutex.ReleaseMutex();
                return false;
            }
            
            SitesSeen.TryAdd(uri, true);
            
            BackQueueMap[host].Enqueue(uri);
            EnqueueMutex.ReleaseMutex();

            cntMutex.WaitOne();
            BackQueueSize += 1;
            cntMutex.ReleaseMutex();
            return true;
        }

        public Uri GetSite()
        {
            DequeueMutex.WaitOne();
            var candidate = BackQueueMap.Where(x => x.Key.IsReady() && x.Value.Count > 0);

            if (candidate.FirstOrDefault().Value == null)
            {
                return BackQueueMap.FirstOrDefault(x => x.Value.Count > 0).Value.Dequeue();
            }

            var ret = candidate.FirstOrDefault().Value.Dequeue();
            
            DequeueMutex.ReleaseMutex();

            cntMutex.WaitOne();
            if(BackQueueSize > 0)
                BackQueueSize -= 1;
            cntMutex.ReleaseMutex();

            return ret;

        }

        public int GetBackQueueCount()
        {
            cntMutex.WaitOne();
            var res = BackQueueSize;
            cntMutex.ReleaseMutex();
            return res;
        }
    }
}
