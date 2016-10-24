using System.Collections.Generic;
using System.Collections.Specialized;

namespace miniproject_social
{
    public class User
    {
        public string name { get; set; }

        public Dictionary<User, bool> friends = new Dictionary<User, bool>();

        public string friendsraw { get; set; }


        public string summary { get; set; }

        public string review { get; set; }

        public User(string name, string friendsraw, string summary, string review)
        {
            this.name = name;
            this.friendsraw = friendsraw;
            this.summary = summary;
            this.review = review;
        }
    }
}