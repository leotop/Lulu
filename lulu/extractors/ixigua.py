#!/usr/bin/env python

import re
import json
import base64
import random
import binascii
from urllib import parse

from lulu.common import (
    match1,
    url_info,
    print_info,
    get_content,
    download_urls,
)


__all__ = ['ixigua_download', 'ixigua_download_playlist']
site_info = '西瓜视频 ixigua.com'


def get_r():
    return str(random.random())[2:]


def right_shift(val, n):
    return val >> n if val >= 0 else (val + 0x100000000) >> n


def get_s(text):
    """get video info
    """
    _id = match1(text, r"videoId: '(.*?)'")
    p = get_r()
    url = 'http://i.snssdk.com/video/urls/v/1/toutiao/mp4/{}'.format(_id)
    n = '{}?r={}'.format(parse.urlparse(url).path, p)
    c = binascii.crc32(n.encode('utf-8'))
    s = right_shift(c, 0)
    title = ''.join(re.findall(r"title: '(.*?)',", text))
    v_url = '{}?r={}&s={}'.format(url, p, s)
    return v_url, title


def get_moment(url, user_id, base_url, video_list):
    """Recursively obtaining a video list
    """
    video_list_data = json.loads(get_content(url))
    if not video_list_data['next']['max_behot_time']:
        return video_list
    [video_list.append(i['display_url']) for i in video_list_data['data']]
    max_behot_time = video_list_data['next']['max_behot_time']
    _param = {
        'user_id': user_id,
        'base_url': base_url,
        'video_list': video_list,
        'url': base_url.format(user_id=user_id, max_behot_time=max_behot_time),
    }
    return get_moment(**_param)


def ixigua_download(url, output_dir='.', info_only=False, **kwargs):
    """Download a single video
    Sample URL: https://www.ixigua.com/a6487187567887254029/#mid=59051127876
    """
    if 'toutiao.com/group' in url:
        url = 'https://www.ixigua.com/a{}'.format(
            match1(url, r'.*?toutiao.com/group/(\d+)')
        )
    try:
        video_info_url, title = get_s(get_content(url))
        video_info = json.loads(get_content(video_info_url))
    except Exception:
        raise NotImplementedError(url)
    try:
        video_url = base64.b64decode(
            video_info['data']['video_list']['video_1']['main_url']
        ).decode()
    except Exception:
        raise NotImplementedError(url)
    filetype, ext, size = url_info(video_url)
    print_info(site_info, title, filetype, size)
    if not info_only:
        download_urls([video_url], title, ext, size, output_dir=output_dir)


def ixigua_download_playlist(url, output_dir='.', info_only=False, **kwargs):
    """Download all video from the user's video list
    Sample URL: https://www.ixigua.com/c/user/71141690831/
    """
    if 'user' not in url:
        raise NotImplementedError(url)
    user_id = url.split('/')[-2]
    max_behot_time = 0
    if not user_id:
        raise NotImplementedError(url)
    base_url = (
        'https://www.ixigua.com/c/user/article/?user_id={user_id}&'
        'max_behot_time={max_behot_time}&max_repin_time=0&count=20&page_type=0'
    )
    _param = {
        'user_id': user_id,
        'base_url': base_url,
        'video_list': [],
        'url': base_url.format(user_id=user_id, max_behot_time=max_behot_time),
    }
    for i in get_moment(**_param):
        ixigua_download(i, output_dir, info_only, **kwargs)


download = ixigua_download
download_playlist = ixigua_download_playlist
