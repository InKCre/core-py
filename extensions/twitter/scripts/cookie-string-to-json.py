import json
import sys


def cookie_string_to_json(cookie_str):
    cookies = {}
    for cookie in cookie_str.split(";"):
        cookie = cookie.strip()
        if "=" in cookie:
            name, value = cookie.split("=", 1)
            cookies[name.strip()] = value.strip()
    return cookies


if __name__ == "__main__":
    # Read cookie string from stdin
    # cookie_str = sys.stdin.read().strip()
    cookie_str = '__cuid=b4495ecafcc94d8185d9e504e2fd1290; kdt=Hl8g3xWy08hmqdrSrNDnQ6pWA7K4iNiABP4yeYC0; g_state={"i_l":0,"i_ll":1763456008186}; dnt=1; personalization_id="v1_8VZAKpLzIVSWHySdRGAnPw=="; lang=en; ads_prefs="HBISAAA="; auth_multi="1776793704566788096:02b8614cb58407a7b76e672c661d2c300d29e804"; auth_token=7ef8cd694e381f4e0e4525a7eee8f277151aa718; guest_id_ads=v1%3A176552992430233095; guest_id_marketing=v1%3A176552992430233095; guest_id=v1%3A176552992430233095; twid=u%3D863624313299128320; ct0=2e8326c995331f38a6c69de892c8f440c04911275cbf086afbf342647a59f7ed3b444beab166cd09f7e7b03366062e9fdb0f6793af034a0ef8bbd54e2309af54307201eb0cfb3021ef84d66c60151db0; __cf_bm=3NDDabMUwE5R2FahqMn9EU0KEqlNoY_3fVYYR9dV29E-1765529936.4892244-1.0.1.1-X4__ETIoQGJyfSzxixUlshXAOTiJet.eR5SOe2L_nLZj5Sz4Uhwzy2YsNpa5FUk9qMWznHdADTF5dgM3zgTkJpj48RBCxPhBQRb4yqG8H_YIYFne4mrEWI4gcOZIWOVG'
    if not cookie_str:
        print("Error: No cookie string provided via stdin.", file=sys.stderr)
        sys.exit(1)

    cookies_dict = cookie_string_to_json(cookie_str)
    print(json.dumps(cookies_dict, indent=2))
