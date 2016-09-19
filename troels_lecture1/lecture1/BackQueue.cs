using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.Remoting.Messaging;
using System.Text;
using System.Threading.Tasks;
using NUglify.Helpers;

namespace lecture1
{
    [Serializable]
    public class BackQueue
    {
        public readonly SortedDictionary<Host, Queue<Uri>> _backQueueMap;

        public BackQueue()
        {
            _backQueueMap = new SortedDictionary<Host, Queue<Uri>>();
        }

        public bool AddToQueue(Host host, Uri uri)
        {
            var containsKey = _backQueueMap.ContainsKey(host);

            if (!containsKey)
            {
                if (_backQueueMap.Any(x => x.Key.hosturl.Host == host.hosturl.Host))
                    Console.WriteLine("WTF wat");

                _backQueueMap.Add(host, new Queue<Uri>());
            }

            if (_backQueueMap[host].Contains(uri))
                return false;

            _backQueueMap[host].Enqueue(uri);
            return true;
        }

        public Uri GetSite()
        {
            //foreach (var q in _backQueueMap.OrderBy(x => x.Key.hosturl.Host))
            //{
            //    Console.WriteLine("Host: {0}, Todo: {2}, LA: {1}", q.Key.hosturl.Host, q.Key.lastVisited, q.Value.Count);
            //}
            //return _backQueueMap.First(x => x.Value.Count > 0).Value.Dequeue();

            //return
            //    _backQueueMap.Where(x => x.Value.Count > 0)
            //        .OrderBy(x => x.Key.lastVisited)
            //        .FirstOrDefault()
            //        .Value.Dequeue();



            //var dl = _backQueueMap
            //    .Where(x => x.Value.Count > 0 && x.Key.lastVisited + x.Key.crawlDelay < DateTime.Now)
            //    .OrderBy(x => x.Key.id).ToList();

            //var d = dl.OrderBy(x => x.Key.lastVisited).FirstOrDefault();

            //if (!dl.Any())
            //{
            //    d = _backQueueMap.FirstOrDefault();
            //}

            //return d.Value.Dequeue();

            var candidate = _backQueueMap.Where(x => x.Key.IsReady() && x.Value.Count > 0);

            if (candidate.FirstOrDefault().Value == null)
            {
                return _backQueueMap.FirstOrDefault(x => x.Value.Count > 0).Value.Dequeue();
            }

            return candidate.FirstOrDefault().Value.Dequeue();
        }

        public int GetBackQueueCount()
        {
            return _backQueueMap.Sum(x => x.Value.Count);
        }
    }
}
