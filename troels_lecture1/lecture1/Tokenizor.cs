using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.Serialization.Formatters.Binary;
using System.Security.Cryptography.X509Certificates;
using System.Security.Policy;
using lecture1;
using NUglify;
using NUglify.Helpers;

namespace lecture1
{
    [Serializable]
    public class Tokenizor
    {
        public Dictionary<string, Token> Tokens;

        public static List<string> StopList = new List<string>()
        {
            "af", "alle", "andet", "andre", "at", "begge", "da", "de", "den", "denne", "der", "deres", 
            "det", "dette", "dig", "din", "dog", "du", "ej", "eller", "en", "end", "ene", "eneste", "enhver", 
            "et", "fem", "fire", "flere", "fleste", "for", "fordi", "forrige", "fra", "få", "før", "god", "han", 
            "hans", "har", "hendes", "her", "hun", "hvad", "hvem", "hver", "hvilken", "hvis", "hvor", "hvordan", 
            "hvorfor", "hvornår", "i", "ikke", "ind", "ingen", "intet", "jeg", "jeres", "kan", "kom", "kommer", 
            "lav", "lidt", "lille", "man", "mand", "mange", "med", "meget", "men", "mens", "mere", "mig", "ned", 
            "ni", "nogen", "noget", "ny", "nyt", "nær", "næste", "næsten", "og", "op", "otte", "over", "på", "se", 
            "seks", "ses", "som", "stor", "store", "syv", "ti", "til", "to", "tre", "ud", "var", "er"
        };

        public void MakeTokens(Site site)
        {
            var html = Uglify.HtmlToText(site.content).ToString();
            var filter = html.Replace('.', ' ').Replace(':', ' ').Replace(',', ' ').Replace('\'', ' ').ToLowerInvariant();
            var content = filter.Split(' ').Where(x => x.Trim() != "" && !StopList.Contains(x)).Select(x => x.Trim()).OrderBy(x => x);

            foreach (var c in content.GroupBy(x => x))
            {
                Token.AddOrCreate(c.Key, site, c.Count(), Tokens);
            }
        }

        public Tokenizor()
        {
            Tokens = new Dictionary<string, Token>();
        }
    }
}