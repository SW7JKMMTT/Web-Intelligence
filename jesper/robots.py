#!/bin/env python

import re
import os
from enum import Enum
import sys

class Permission(Enum):
    disallow=0
    allow=1

class Node():
    def __init__(self, depth, final):
        self._children = []
        self.depth = depth
        self.final = final

    def matches(self, txt):
        raise NotImplementedError()

    def getDepth(self):
        return self.depth

    def getPerm(self):
        raise NotImplementedError()

    def add(self, child):
        self._children.append(child)

    def get(self, i):
        return self._children[i]

    def find(self, path):
        for child in self._children:
            if child.txt == path:
                return child
        return None

    def __iter__(self):
        return self._children.__iter__()

class TextNode(Node):
    def __init__(self, depth, txt, perm, final):
        super().__init__(depth, final)
        self.txt = txt
        self.perm = perm

    def matches(self, txt):
        if self.txt == txt:
            return True
        return False

    def getPerm(self):
        return self.perm

class RootNode(Node):
    def __init__(self, perm, final):
        super().__init__(0, final)
        self.perm = perm

    def getPerm(self):
        return self.perm

class WildcardNode(Node):
    def __init__(self, depth, txt, perm, final):
        super().__init__(depth, final)
        self.perm = perm
        self.txt = txt

    def matches(self, txt):
        return True

    def getPerm(self):
        return self.perm

class GlobNode(Node):
    def __init__(self, depth, txt, perm, final):
        super().__init__(depth, final)
        self.perm = perm
        self.txt = txt
        self.regex = re.escape(txt).replace("\*", ".*")

    def matches(self, txt):
        return re.match(self.regex, txt)

    def getPerm(self):
        return self.perm


class Robots():
    def __init__(self, tree, delay):
        self.tree = tree
        self.delay = delay

    def getPermission(self, path):
        return self.tree.matches(path)

    def isAllowed(self, path):
        return self.tree.matches(path) == Permission.allow

class RobotTree():
    def __init__(self, default):
        self.default = default
        self.root = RootNode(Permission.allow, self.default)

    def addPath(self, path, state):
        curNode = self.root
        for part in _getParts(path):
            newNode = curNode.find(part)
            if newNode == None:
                if part == "*" or part == "": #path part is a complete wildcard
                    newNode = WildcardNode(curNode.getDepth()+1, part, self.default, False)
                elif "*" in part:
                    newNode = GlobNode(curNode.getDepth()+1, part, self.default, False)
                else:
                    newNode = TextNode(curNode.getDepth()+1, part, self.default, False)
                curNode.add(newNode)
            curNode = newNode
        curNode.perm = state
        curNode.final = True

    def matches(self, path):
        pp = _getParts(path)
        instance = [[]]
        newInst = []
        run = 0
        maxDepth = 0
        maxPerm = self.root.getPerm()
        while run < len(pp) and len(instance) > 0:
            for path in instance:
                curNode = self.root
                for p in path:
                    curNode = curNode.get(p)

                for k, c in enumerate(curNode):
                    if c.matches(pp[run]):
                        newPath = list(path)
                        newPath.append(k)
                        newInst.append(newPath)
                        if maxDepth <= c.depth and c.final:
                            maxDepth = c.depth
                            maxPerm = c.getPerm()
            run += 1
            instance = newInst
            newInst = []
        return maxPerm


def _getParts(s):
    head, tail = os.path.split(s)
    parts = []
    while tail != "" or head != "/" and head != "":
        parts.append(tail)
        head, tail = os.path.split(head)
    parts.reverse()
    return parts

def isMe(agent):
    if agent == "*":
        return True
    if agent == "DelusionalBot":
        return True
    return False

def compileRobots(s):
    tree = RobotTree(Permission.allow)
    doParse = False
    hasRules = True
    delay = -1
    for line in s.split("\n"):
        line = re.sub(r'#.*', "", line)
        line = line.strip(" ")

        if line == "":
            continue

        s = line.split(":", 1)
        if s[0].lower() == "allow":
            hasRules = True
            if doParse:
                tree.addPath(s[1].strip(" "), Permission.allow)
        elif s[0].lower() == "disallow":
            hasRules = True
            if doParse:
                tree.addPath(s[1].strip(" "), Permission.disallow)
        elif s[0].lower() == "crawl-delay":
            hasRules = True
            if doParse:
                delay = float(s[1].strip(" "))
        elif s[0].lower() == "user-agent":
            if isMe(s[1].strip(" ")):
                doParse = True
                hasRules = False
            elif  hasRules == True:
                doParse = False
                hasRules = False
    return Robots(tree, delay)

def main():
    rob = """
    User-agent: *
    Disallow: /search
    Allow: /search/about
    Disallow: /sdch
    Disallow: /groups
    Disallow: /index.html?
    Disallow: /?
    Allow: /?hl=
    Disallow: /?hl=*&
    Allow: /?hl=*&gws_rd=ssl$
    Disallow: /?hl=*&*&gws_rd=ssl
    Allow: /?gws_rd=ssl$
    Allow: /?pt1=true$
    Disallow: /imgres
    Disallow: /u/
    Disallow: /preferences
    Disallow: /setprefs
    Disallow: /default
    Disallow: /m?
    Disallow: /m/
    Allow:    /m/finance
    Disallow: /wml?
    Disallow: /wml/?
    Disallow: /wml/search?
    Disallow: /xhtml?
    Disallow: /xhtml/?
    Disallow: /xhtml/search?
    Disallow: /xml?
    Disallow: /imode?
    Disallow: /imode/?
    Disallow: /imode/search?
    Disallow: /jsky?
    Disallow: /jsky/?
    Disallow: /jsky/search?
    Disallow: /pda?
    Disallow: /pda/?
    Disallow: /pda/search?
    Disallow: /sprint_xhtml
    Disallow: /sprint_wml
    Disallow: /pqa
    Disallow: /palm
    Disallow: /gwt/
    Disallow: /purchases
    Disallow: /local?
    Disallow: /local_url
    Disallow: /shihui?
    Disallow: /shihui/
    Disallow: /products?
    Disallow: /product_
    Disallow: /products_
    Disallow: /products;
    Disallow: /print
    Disallow: /books/
    Disallow: /bkshp?*q=*
    Disallow: /books?*q=*
    Disallow: /books?*output=*
    Disallow: /books?*pg=*
    Disallow: /books?*jtp=*
    Disallow: /books?*jscmd=*
    Disallow: /books?*buy=*
    Disallow: /books?*zoom=*
    Allow: /books?*q=related:*
    Allow: /books?*q=editions:*
    Allow: /books?*q=subject:*
    Allow: /books/about
    Allow: /booksrightsholders
    Allow: /books?*zoom=1*
    Allow: /books?*zoom=5*
    Disallow: /ebooks/
    Disallow: /ebooks?*q=*
    Disallow: /ebooks?*output=*
    Disallow: /ebooks?*pg=*
    Disallow: /ebooks?*jscmd=*
    Disallow: /ebooks?*buy=*
    Disallow: /ebooks?*zoom=*
    Allow: /ebooks?*q=related:*
    Allow: /ebooks?*q=editions:*
    Allow: /ebooks?*q=subject:*
    Allow: /ebooks?*zoom=1*
    Allow: /ebooks?*zoom=5*
    Disallow: /patents?
    Disallow: /patents/download/
    Disallow: /patents/pdf/
    Disallow: /patents/related/
    Disallow: /scholar
    Disallow: /citations?
    Allow: /citations?user=
    Disallow: /citations?*cstart=
    Allow: /citations?view_op=new_profile
    Allow: /citations?view_op=top_venues
    Allow: /scholar_share
    Disallow: /s?
    Allow: /maps?*output=classic*
    Allow: /maps?*file=
    Allow: /maps/api/js?
    Allow: /maps/d/
    Disallow: /maps?
    Disallow: /mapstt?
    Disallow: /mapslt?
    Disallow: /maps/stk/
    Disallow: /maps/br?
    Disallow: /mapabcpoi?
    Disallow: /maphp?
    Disallow: /mapprint?
    Disallow: /maps/api/js/
    Disallow: /maps/api/staticmap?
    Disallow: /maps/api/streetview
    Disallow: /mld?
    Disallow: /staticmap?
    Disallow: /maps/preview
    Disallow: /maps/place
    Disallow: /help/maps/streetview/partners/welcome/
    Disallow: /help/maps/indoormaps/partners/
    Disallow: /lochp?
    Disallow: /center
    Disallow: /ie?
    Disallow: /blogsearch/
    Disallow: /blogsearch_feeds
    Disallow: /advanced_blog_search
    Disallow: /uds/
    Disallow: /chart?
    Disallow: /transit?
    Disallow: /extern_js/
    Disallow: /xjs/
    Disallow: /calendar/feeds/
    Disallow: /calendar/ical/
    Disallow: /cl2/feeds/
    Disallow: /cl2/ical/
    Disallow: /coop/directory
    Disallow: /coop/manage
    Disallow: /trends?
    Disallow: /trends/music?
    Disallow: /trends/hottrends?
    Disallow: /trends/viz?
    Disallow: /trends/embed.js?
    Disallow: /trends/fetchComponent?
    Disallow: /trends/beta
    Disallow: /musica
    Disallow: /musicad
    Disallow: /musicas
    Disallow: /musicl
    Disallow: /musics
    Disallow: /musicsearch
    Disallow: /musicsp
    Disallow: /musiclp
    Disallow: /urchin_test/
    Disallow: /movies?
    Disallow: /wapsearch?
    Allow: /safebrowsing/diagnostic
    Allow: /safebrowsing/report_badware/
    Allow: /safebrowsing/report_error/
    Allow: /safebrowsing/report_phish/
    Disallow: /reviews/search?
    Disallow: /orkut/albums
    Disallow: /cbk
    Allow: /cbk?output=tile&cb_client=maps_sv
    Disallow: /maps/api/js/AuthenticationService.Authenticate
    Disallow: /maps/api/js/QuotaService.RecordEvent
    Disallow: /recharge/dashboard/car
    Disallow: /recharge/dashboard/static/
    Disallow: /profiles/me
    Allow: /profiles
    Disallow: /s2/profiles/me
    Allow: /s2/profiles
    Allow: /s2/oz
    Allow: /s2/photos
    Allow: /s2/search/social
    Allow: /s2/static
    Disallow: /s2
    Disallow: /transconsole/portal/
    Disallow: /gcc/
    Disallow: /aclk
    Disallow: /cse?
    Disallow: /cse/home
    Disallow: /cse/panel
    Disallow: /cse/manage
    Disallow: /tbproxy/
    Disallow: /imesync/
    Disallow: /shenghuo/search?
    Disallow: /support/forum/search?
    Disallow: /reviews/polls/
    Disallow: /hosted/images/
    Disallow: /ppob/?
    Disallow: /ppob?
    Disallow: /accounts/ClientLogin
    Disallow: /accounts/ClientAuth
    Disallow: /accounts/o8
    Allow: /accounts/o8/id
    Disallow: /topicsearch?q=
    Disallow: /xfx7/
    Disallow: /squared/api
    Disallow: /squared/search
    Disallow: /squared/table
    Disallow: /qnasearch?
    Disallow: /app/updates
    Disallow: /sidewiki/entry/
    Disallow: /quality_form?
    Disallow: /labs/popgadget/search
    Disallow: /buzz/post
    Disallow: /compressiontest/
    Disallow: /analytics/reporting/
    Disallow: /analytics/admin/
    Disallow: /analytics/web/
    Disallow: /analytics/feeds/
    Disallow: /analytics/settings/
    Disallow: /analytics/portal/
    Disallow: /analytics/uploads/
    Allow: /alerts/manage
    Allow: /alerts/remove
    Disallow: /alerts/
    Allow: /alerts/$
    Disallow: /ads/search?
    Disallow: /ads/plan/action_plan?
    Disallow: /ads/plan/api/
    Disallow: /ads/hotels/partners
    Disallow: /phone/compare/?
    Disallow: /travel/clk
    Disallow: /hotelfinder/rpc
    Disallow: /hotels/rpc
    Disallow: /flights/rpc
    Disallow: /commercesearch/services/
    Disallow: /evaluation/
    Disallow: /chrome/browser/mobile/tour
    Disallow: /compare/*/apply*
    Disallow: /forms/perks/
    Disallow: /shopping/suppliers/search
    Disallow: /ct/
    Disallow: /edu/cs4hs/
    Disallow: /trustedstores/s/
    Disallow: /trustedstores/tm2
    Disallow: /trustedstores/verify
    Disallow: /adwords/proposal
    Disallow: /shopping/product/
    Disallow: /shopping/seller
    Disallow: /shopping/reviewer
    Disallow: /about/careers/apply/
    Disallow: /about/careers/applications/
    Disallow: /landing/signout.html
    Disallow: /webmasters/sitemaps/ping?
    Disallow: /ping?
    Disallow: /gallery/
    Disallow: /landing/now/ontap/
    Allow: /searchhistory/

    # Certain social media sites are whitelisted to allow crawlers to access page markup when links to google.com/imgres* are shared. To learn more, please contact images-robots-whitelist@google.com.
    User-agent: Twitterbot
    Allow: /imgres

    User-agent: facebookexternalhit
    Allow: /imgres

    Sitemap: http://www.gstatic.com/culturalinstitute/sitemaps/www_google_com_culturalinstitute/sitemap-index.xml
    Sitemap: http://www.gstatic.com/earth/gallery/sitemaps/sitemap.xml
    Sitemap: http://www.gstatic.com/s2/sitemaps/profiles-sitemap.xml
    Sitemap: https://www.google.com/sitemap.xml
    """
    robot = compileRobots(rob)
    print(robot.getPermission(sys.argv[1]))

if __name__ == "__main__":
    main()
