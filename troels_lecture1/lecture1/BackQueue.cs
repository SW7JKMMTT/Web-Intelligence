using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using miniproject;

namespace lecture1
{
    public class BackQueue
    {
        readonly SortedDictionary<Host, Queue<Site>> _backQueueMap;

        public BackQueue()
        {
            _backQueueMap = new SortedDictionary<Host, Queue<Site>>();
        }

        public bool AddToQueue(Host host, Site site)
        {
            var containsKey = _backQueueMap.ContainsKey(host);
            if (!containsKey)
                _backQueueMap.Add(host, new Queue<Site>());

            if (_backQueueMap[host].Contains(site)) 
                return false;

            _backQueueMap[host].Enqueue(site);
            return true;
        }

        public Site GetSite()
        {
            return _backQueueMap.First(x => x.Value.Count > 0).Value.Dequeue();
        }

        public int GetBackQueueCount()
        {
            return _backQueueMap.Sum(x => x.Value.Count);
        }
    }
}
