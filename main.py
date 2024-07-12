# -*- coding: utf-8 -*-
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

import os
import glob

from TiktokUser import TiktokUser, get_target_info


def start_sending(file_path, proxies, finger_print, target_id, target_nickname, target_secUid):
    try:
        if os.path.isfile(file_path):  # Проверка, что это файл, а не каталог
            with open(file_path, 'r', encoding='utf-8') as file:
                try:
                    TiktokUser(target_url, target_secUid, target_id, target_nickname, proxies, file.read(),
                               finger_print, '9002').send_report()
                    return True
                except Exception as A:
                    print(f'Error AccountReporter {A}')
    except Exception as A:
        print(f'Error file:{file_path} {A}')
    return False


def start_reading(directory_path, num_threads, target_id, target_nickname, target_secUid):
    files = glob.glob(os.path.join(directory_path, '*'))
    random.shuffle(files)
    with open('fingerprints.txt') as F:
        fingerprints = F.read().split('\n')
        fingerprints_len = len(fingerprints)
        print(f'fingerprints_len : {fingerprints_len}')
    with open('proxies.txt') as F:
        proxies = F.read().split('\n')
        random.shuffle(proxies)
        proxies_len = len(proxies)
        print(f'proxies_len : {proxies_len}')

    # global all_cookies_count
    # all_cookies_count=len(files)

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(start_sending,
                                   file,
                                   proxies[i % proxies_len],
                                   fingerprints[i % fingerprints_len],
                                   target_id, target_nickname, target_secUid) for i, file in enumerate(files)]
        for future in as_completed(futures):
            try:
                result = future.result()
            except Exception as e:
                print(f"An error occurred: {e}")


if __name__ == '__main__':
    target_unick = input('Hello! Input target unique nick/id https://www.tiktok.com/@')

    target_url = f'https://www.tiktok.com/@{target_unick}'
    proxies_to_check = 'log:pass@ip:port'
    finger_print_to_check = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    target_id, target_nickname, target_secUid = get_target_info(target_url, proxies_to_check, finger_print_to_check)

    if target_nickname is None:
        print('Account not found!')
        exit()
    print(f'Target: {target_nickname} TargetId: {target_id} TargetSecUid: {target_secUid}')
    start_reading('TikTok Cookies', 10, target_id, target_nickname, target_secUid)
