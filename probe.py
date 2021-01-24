import json
import os
import sys
import urllib.parse as urlparse
from urllib.parse import parse_qs

import requests
from bs4 import BeautifulSoup as soup

try:
    os.makedirs('data')
except Exception:
    pass

# if chunk size is 742 some series are not working
# eg. my boo
CHUNK_SIZE = 400

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def save_likes_json(url):
    r = requests.get(url)
    html = soup(r.content, 'lxml')
    ul: soup = html.find('ul', {'id': '_listUl'})
    total = int(ul.find('li')['data-episode-no'])
    print(url, total)

    # https://stackoverflow.com/a/5075477/8608146
    parsed = urlparse.urlparse(url)
    qs = parse_qs(parsed.query)

    title_no = int(qs['title_no'][0])

    page = 1
    if 'page' in qs:
        page = int(qs['page'][0])

    # TODO remove page from the url if it has it to get the latest chapter

    # TODO remove sudden down spikes they are removed chapters
    # the correct way to do is to scrape the whole list of chapters
    # while paginating then querying those ids to avoid this
    # but that reqires complete re-write and is inefficient

    # TODO plots by date
    # But in that case we won't be able to get dates for paywalled episodes
    # TODO inspect network in webtoon mobile app

    # episodes behind paywall
    x_eps = html.find('div', {'class': 'detail_install_app'})
    extras = False
    new_total = total
    try:
        new_total += int(x_eps.em.text)
        extras = True
    except Exception:
        print("[INFO] No extra episodes")

    # https://stackoverflow.com/a/312464/8608146

    # if `every day` exists in extras warn user
    # batch get likes till the likecount reaches zero thus also get total
    # example noblesse
    # these are all behind paywall (every day one unlocked)
    data = []
    if x_eps is not None and 'every day' in x_eps.strong.text:
        x = 0
        print("[WARNING] Many chapters behind paywall")
        # loop of CHUNK_SIZE sized chunks
        while True:
            query = f"titleNo={title_no}"
            query += "&" + \
                "&".join([f"episodeNos={CHUNK_SIZE*(x+1)-i}" for i in range(CHUNK_SIZE)])
            r = requests.post(
                "https://www.webtoons.com/en/likeitCount",
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                data=query,
            )

            resp = r.json()
            if len(resp['likeItList']) == 0:
                print("[WARNING] Chunk size might be too large", CHUNK_SIZE)
            idx = -1
            for i, l in enumerate(resp['likeItList']):
                if l['likeItCount'] != 0:
                    # very first non zero index from the end
                    idx = i
                    break
            for ep in resp['likeItList'][:(idx-1):-1]:
                extra = False
                if ep['episodeNo'] > total:
                    extra = True
                data.append({
                    'i': ep['episodeNo'],
                    'c': ep['likeItCount'],
                    'e': extra,
                })
            try:
                # TODO check if last `N` are zero?
                # because some new episodes might not be available to public yet
                # but available from the api
                # or some not popular, not exposed episodes can have 0 likes
                # but this condition might not be possible because this is behind paywall
                # if last (form the end) is 0 we need not continue
                if resp['likeItList'][0]['likeItCount'] == 0:
                    break
            except IndexError:
                break

            x += 1
            if x > 9:
                print("[WARNING] Too many requests sent, stuck in a loop, breaking")
                # possibly infite loop because too many chapters
                # > CHUNK_SIZE0 -> not likely
                break
    else:
        # 742 is a query's limit (tested on bluechair)
        # eg. try for blue chair
        resps = []
        for chunk in chunks(list(range(new_total)), CHUNK_SIZE):
            query = f"titleNo={title_no}"
            query += "&" + \
                "&".join([f"episodeNos={new_total-i}" for i in chunk])

            # must include header https://stackoverflow.com/a/39615067/8608146
            # but curl infers it
            r = requests.post(
                "https://www.webtoons.com/en/likeitCount",
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                data=query,
            )

            resp = r.json()
            resps.append(resp)

        for resp in resps[::-1]:
            for ep in resp['likeItList'][::-1]:
                extra = False
                if ep['episodeNo'] > total:
                    extra = True
                    # print('🌟extra', end=' ')
                data.append({
                    'i': ep['episodeNo'],
                    'c': ep['likeItCount'],
                    'e': extra,
                })
                # print(ep['episodeNo'], ep['likeItCount'])
                if ep['likeItCount'] == 0:
                    print('Possibly non-existent chapter',
                          ep['episodeNo'], title_no)

    with open(f"data/{title_no}.json", 'w+') as f:
        json.dump(data, f)


if __name__ == '__main__':
    urls = sys.argv[1:]
    for url in urls:
        save_likes_json(url)
