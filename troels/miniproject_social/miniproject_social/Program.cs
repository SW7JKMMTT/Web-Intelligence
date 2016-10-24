using System;
using System.Collections.Generic;
using System.Data;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using QuickGraph;
using QuickGraph.Algorithms;
using QuickGraph.Algorithms.Observers;
using QuickGraph.Algorithms.ShortestPath;
using QuickGraph.Algorithms.Cliques;
using QuickGraph.Data;

namespace miniproject_social
{
    class Program
    {
        static void Main(string[] args)
        {
            var users = new Dictionary<string, User>();

            var input = File.ReadAllText("./friendships.txt");

            Regex rgx = new Regex("\n\n");
            Regex rgx2 = new Regex("\r");

            var d = rgx2.Replace(input, "");

            var splitonusers = rgx.Split(d, Int32.MaxValue);

            foreach (var splitonuser in splitonusers.Where(x => x != ""))
            {
                var usr = splitonuser.Split('\n').Select(x => x.Split(':').Select(y => y).ToList()).ToList();
                var usrobj = new User(usr[0][1].Trim(), usr[1][1].Trim(), usr[2][1].Trim(), usr[3][1].Trim());

                //Console.WriteLine("User: \"{0}\"", usrobj.name);

                users.Add(usrobj.name, usrobj);
            }

            ConnectFriends(users);

            foreach (var source in users.Values.OrderByDescending(x => x.friends.Count).Take(20))
            {
                Console.WriteLine("Name: {0}, friends: {1}", source.name, source.friends.Count);
            }

            FloydWarshall(users);

            Console.WriteLine("a");

            Console.ReadKey();
        }

        static void ConnectFriends(Dictionary<string, User> users)
        {
            foreach (var user in users)
            {
                var friends = user.Value.friendsraw.Split('\t');

                foreach (var friend in friends)
                {
                    user.Value.friends.Add(users[friend], true);
                }
            }
        }

        static AdjacencyGraph<string, Edge<string>> MakeGraph(Dictionary<string, User> users)
        {
            AdjacencyGraph<string, Edge<string>> graph = new AdjacencyGraph<string, Edge<string>>(true);
            foreach (var user in users)
            {
                graph.AddVertex(user.Key);
            }

            foreach (var user in users)
            {
                foreach (var friend in user.Value.friends.Keys)
                {
                    graph.AddEdge(new Edge<string>(user.Key, friend.name));
                }
            }

            return graph;
        }

        static Dictionary<Edge<string>, double> CalculateEdgecost(AdjacencyGraph<string, Edge<string>> graph)
        {
            Dictionary<Edge<string>, double> edgeCost = new Dictionary<Edge<string>, double>(graph.EdgeCount);

            foreach (var u in graph.Edges)
            {
                edgeCost.Add(u, 1);
            }

            return edgeCost;
        }

        static void FloydWarshall(Dictionary<string, User> users)
        {
            var distances = new Dictionary<Edge<string>, double>();
            var graph = MakeGraph(users);
            var edgeWeights = CalculateEdgecost(graph);
            var fw = new FloydWarshallAllShortestPathAlgorithm<string, Edge<string>>(graph, e => 1);
            var sw = new Stopwatch();
            sw.Start();
            fw.Compute();
            sw.Stop();
            Console.WriteLine("Ran for: " + sw.ElapsedMilliseconds + " ms");

            foreach (var i in graph.Vertices.Take(10))
            {
                foreach (var j in graph.Vertices)
                {
                    Console.Write("{0} -> {1}:", i, j);
                    IEnumerable<Edge<string>> path;
                    if (fw.TryGetPath(i, j, out path))
                    {
                        double cost = 0;
                        foreach (var edge in path)
                        {
                            Console.Write("{0}, ", edge.Source);
                            cost += distances[edge];
                        }
                        Console.Write("{0} --- {1}", j, cost);
                    }
                    Console.WriteLine();
                }
            }
        }

        static void DijkstraExample(Dictionary<string, User> users)
        {

            var graph = MakeGraph(users);
            var dijkstra = new DijkstraShortestPathAlgorithm<string, Edge<string>>(graph, e => 1);

            // Attach a Vertex Predecessor Recorder Observer to give us the paths
            var predecessorObserver = new VertexPredecessorRecorderObserver<string, Edge<string>>();
            using (predecessorObserver.Attach(dijkstra))
            {
                // Run the algorithm with A set to be the source
                dijkstra.Compute("abagael");
            }

            //foreach (KeyValuePair<string, Edge<string>> kvp in predecessorObserver.VertexPredecessors)
            //    Console.WriteLine("If you want to get to {0} you have to enter through the in edge {1}", kvp.Key, kvp.Value);

            foreach (string v in graph.Vertices)
            {
                double distance =
                    AlgorithmExtensions.ComputePredecessorCost(
                        predecessorObserver.VertexPredecessors,
                        CalculateEdgecost(graph), v);
                //Console.WriteLine("A -> {0}: {1}", v, distance);
            }
        }
    }
}
