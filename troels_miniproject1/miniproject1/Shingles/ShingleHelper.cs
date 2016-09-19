using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Cryptography;
using System.Text;

namespace miniproject1.Shingles
{
    public static class ShingleHelper
    {
        public static void Tester()
        {
            TestString<string, int>("do not worry about your difficulties in mathematics", "i would not worry about your difficulties, you can easily learn what is needed.", HashOne, 3);
            TestString<string, string>("do not worry about your difficulties in mathematics", "i would not worry about your difficulties, you can easily learn what is needed.", HashTwo, 3);
            TestString<string, string>("do not worry about your difficulties in mathematics", "i would not worry about your difficulties, you can easily learn what is needed.", HashThree, 3);

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
        public static IEnumerable<string> Nshingle(string input, int shingles)
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

            return (double)overlap.Count / union.Count;
        }

        public static IEnumerable<TR> HashEnumerable<T, TR>(IEnumerable<string> input, Func<string, TR> hash)
        {
            return input.Select(hash);
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

                return string.Concat(Convert.ToBase64String(hash).ToCharArray().Where(char.IsLetterOrDigit));
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
                    sBuilder.Append(i.ToString("x2"));
                }

                return sBuilder.ToString();
            }
        }

        public static void TestString<T, TR>(string inputA, string inputB, Func<string, TR> hash, int shingles)
        {
            var test = Nshingle(inputA, shingles);
            var test2 = Nshingle(inputB, shingles);

            Console.WriteLine("String A:");
            foreach (var t in test)
            {
                Console.WriteLine(t);
                Console.WriteLine(hash(t));
            }

            Console.WriteLine("String B:");
            foreach (var t in test2)
            {
                Console.WriteLine(t);
                Console.WriteLine(hash(t));
            }


            Console.WriteLine(JaccardSimilarity(HashEnumerable<T, TR>(test, hash), HashEnumerable<T, TR>(test2, hash)));

            Console.WriteLine(MinHashCompare(HashEnumerable<T, TR>(test, hash), HashEnumerable<T, TR>(test2, hash)));
        }

        public static List<string> Sketch(string input, int shingles)
        {
            var res = new List<string>();
            var test = Nshingle(input, shingles);

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

            return (double)matches / inputA.Count();
        }
    }
}