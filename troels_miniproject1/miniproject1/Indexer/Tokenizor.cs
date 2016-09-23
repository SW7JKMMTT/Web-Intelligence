﻿using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using miniproject1.DataStructures;
using NUglify;

namespace miniproject1.Indexer
{
    public static class Tokenizor
    {
        public static List<string> StopList = new List<string>
        {
            "af", "alle", "andet", "andre", "at", "begge", "da", "de", "den", "denne", "der", "deres",
            "det", "dette", "dig", "din", "dog", "du", "ej", "eller", "en", "end", "ene", "eneste", "enhver",
            "et", "fem", "fire", "flere", "fleste", "for", "fordi", "forrige", "fra", "få", "før", "god", "han",
            "hans", "har", "hendes", "her", "hun", "hvad", "hvem", "hver", "hvilken", "hvis", "hvor", "hvordan",
            "hvorfor", "hvornår", "i", "ikke", "ind", "ingen", "intet", "jeg", "jeres", "kan", "kom", "kommer",
            "lav", "lidt", "lille", "man", "mand", "mange", "med", "meget", "men", "mens", "mere", "mig", "ned",
            "ni", "nogen", "noget", "ny", "nyt", "nær", "næste", "næsten", "og", "op", "otte", "over", "på", "se",
            "seks", "ses", "som", "stor", "store", "syv", "ti", "til", "to", "tre", "ud", "var", "er", 
            "'", "-", "_", ":", ".", "!", "\\", "&", "(", ")", ",", "’", "?", ".."

        };

        public static void AddTokensToTokenList(Site site, Dictionary<string, Token> tokens)
        {
            var html = Uglify.HtmlToText(site.Content).ToString();
            var pattern = @"\b";
            var pattern2 = @"[^\w]+";
            var rgx = new Regex(pattern);
            var rgx2 = new Regex(pattern2);
            var filter = rgx.Replace(html, " ").ToLowerInvariant();
            filter = rgx2.Replace(filter, " ");
            var content = filter.Split(' ').Where(x => x.Trim() != "" && !StopList.Contains(x)).Select(x => x.Trim()).OrderBy(x => x);

            foreach (var c in content.GroupBy(x => x))
            {
                Token.AddOrCreate(c.Key, site, c.Count(), tokens);
            }
        }
    }
}