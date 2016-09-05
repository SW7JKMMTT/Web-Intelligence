using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Cryptography;
using System.Text;

namespace lecture1
{
    class Program
    {
        public static IEnumerable<string> nshingle(string input, int shingles)
        {
            input = input.Replace(".", "");
            input = input.Replace(",", "");

            var words = input.Split(' ');
            var shringleList = new List<string>();

            for (int i = 0; i <= words.Count() - shingles; i++)
            {
                StringBuilder stringBuilder = new StringBuilder();
                for (int j = 0; j < shingles; j++)
                {
                    stringBuilder.Append(words[i + j] + " ");
                }

                var str = stringBuilder.ToString();
                if (!shringleList.Contains(str))
                    shringleList.Add(str);
            }

            return shringleList;
        }

        public static double JaccardSimilarity<T>(IEnumerable<T> inputA, IEnumerable<T> inputB)
        {
            var union = inputA.ToList();
            union.AddRange(inputB.Where(s => !inputA.Contains(s)));

            var overlap = inputA.Where(inputB.Contains).ToList();

            return (double)overlap.Count / (double)union.Count;
        }

        public static IEnumerable<R> HashEnumerable<T, R>(IEnumerable<string> input, Func<string, R> Hash)
        {
            return input.Select(x => Hash(x));
        }

        public static bool MinHashCompare<T>(IEnumerable<T> inputA, IEnumerable<T> inputB)
        {
            return inputA.Min().Equals(inputB.Min());
        }

        public static int HashOne(string input)
        {
            return input.GetHashCode();
        }

        public static string HashTwo(string input)
        {
            using (SHA1Managed sha1 = new SHA1Managed())
            {
                var hash = sha1.ComputeHash(Encoding.UTF8.GetBytes(input));

                return string.Concat(Convert.ToBase64String(hash).ToCharArray().Where(x => char.IsLetterOrDigit(x)));
            }
        }

        public static string HashThree(string input)
        {
            using (MD5 md5Hash = MD5.Create())
            {
                byte[] data = md5Hash.ComputeHash(Encoding.UTF8.GetBytes(input));

                StringBuilder sBuilder = new StringBuilder();

                for (int i = 0; i < data.Length; i++)
                {
                    sBuilder.Append(data[i].ToString("x2"));
                }

                return sBuilder.ToString();
            }
        }

        public static void TestString<T, R>(string inputA, string inputB, Func<string, R> Hash, int shingles)
        {
            var test = nshingle(inputA, shingles);
            var test2 = nshingle(inputB, shingles);

            Console.WriteLine("String A:");
            foreach (var t in test)
            {
                Console.WriteLine(t);
                Console.WriteLine(Hash(t));
            }

            Console.WriteLine("String B:");
            foreach (var t in test2)
            {
                Console.WriteLine(t);
                Console.WriteLine(Hash(t));
            }


            Console.WriteLine(JaccardSimilarity(HashEnumerable<T, R>(test, Hash), HashEnumerable<T, R>(test2, Hash)));

            Console.WriteLine(MinHashCompare(HashEnumerable<T, R>(test, Hash), HashEnumerable<T, R>(test2, Hash)));
        }

        public static List<string> Sketch(string input, int shingles)
        {
            var res = new List<string>();
            var test = nshingle(input, shingles);

            res.Add(HashEnumerable<string, int>(test, HashOne).Min().ToString());
            res.Add(HashEnumerable<string, string>(test, HashTwo).Min());
            res.Add(HashEnumerable<string, string>(test, HashThree).Min());

            return res;
        }

        public static double CompareSketches(IEnumerable<string> inputA, IEnumerable<string> inputB)
        {
            var matches = 0;
            foreach (var s in inputA)
            {
                if (inputB.Contains(s))
                    matches++;
            }

            return (double)matches / (double)inputA.Count();
        }

        static void Main(string[] args)
        {
            //TestString<string,    int>("do not worry about your difficulties in mathematics", "i would not worry about your dificulties, you can easily learn what is needed.", HashOne, 3);
            //TestString<string, string>("do not worry about your difficulties in mathematics", "i would not worry about your difficulties, you can easily learn what is needed.", HashTwo, 3);
            //TestString<string, string>("do not worry about your difficulties in mathematics", "i would not worry about your difficulties, you can easily learn what is needed.", HashThree, 3);

            var sketchA = Sketch("do not worry about your difficulties in mathematics", 3);
            var sketchB = Sketch("i would not worry about your dificulties, you can easily learn what is needed.", 3);

            foreach (var s in sketchA)
            {
                Console.WriteLine(s);
            }

            foreach (var s in sketchB)
            {
                Console.WriteLine(s);
            }

            Console.WriteLine(CompareSketches(sketchA, sketchB));
        }
    }
}
