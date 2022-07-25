from requests import get, exceptions
import os
import json
import subprocess

# =============================================================================
# You need to specify path to ffmpeg if you're using windows, # path to ffmpeg bin -> FFMPEG_PATH = r'C:\ffmpeg\bin\ffmpeg'
# If you're using linux, you can use the following line: sudo apt update, sudo apt install ffmpeg
# =============================================================================

AVAILABLE_RESOLUTIONS = [1080, 720, 480, 360, 240, 140, 120, '2_4_M', '1_2_M']

CURRENT_DIR_PATH = os.path.dirname(os.path.realpath(__file__))


def check_file_exists(file_path):
    if os.path.exists(file_path):
        print('File already exists')
        return True
    else:
        return False


def get_user_agent():
    return 'Mozilla/5.0 (Windows NT 6.0) AppleWebKit/5360 (KHTML, like Gecko) Chrome/39.0.872.0 Mobile Safari/5360'


def highest_res_url(media_id):
    all_working_urls = []
    print('looking for the best quality available for this media')
    for res in AVAILABLE_RESOLUTIONS:
        request = get(
            f'https://v.redd.it/{media_id}/DASH_{res}.mp4?source=fallback',
            headers={'User-agent': get_user_agent()}
        )
        if 'error' in request.text:
            if request.status_code == 404:
                print('Post not found', 'error')
        elif 'Access Denied' in request.text:
            print(f'{res} not found', 'error')
        else:
            print(f'{res} found', 'success')
            return f'https://v.redd.it/{media_id}/DASH_{res}.mp4?source=fallback'

    # return all_working_urls[0]


def downlaod_media(url, output):
    download_task = ['curl', '-o', f'{output}', f'{url}']
    subprocess.run(download_task)


def stitch_video(video_input, audio_input, output):
    stitch_video_task = ['ffmpeg',
                         '-i', f'{video_input}',
                         '-i', f'{audio_input}',
                         '-c:v', 'copy',
                         '-c:a', 'aac',
                         '-strict', 'experimental',
                         output]
    subprocess.run(stitch_video_task)


def get_video_url(json_data):
    video_url = False
    try:  # checks if post contains video
        video_url = json_data['secure_media']['reddit_video']['fallback_url']
        media_id = video_url.replace('https://v.redd.it/', '').split('/')[0]
        video_url = highest_res_url(media_id)
    except TypeError:
        print('Only posts with videos are supported', 'error')

    return video_url


def get_audio_url(json_data):
    audio_url = False
    try:
        audio_url = json_data['secure_media']['reddit_video']['hls_url'].split('HLS')[
            0]
        audio_url += 'HLS_AUDIO_160_K.aac'
    except TypeError:
        print('No audio found.', 'error')

    return audio_url


def reddit_downloader(url):
    try:  # checks if link is valid
        request = get(
            url + '.json',
            headers={'User-agent': get_user_agent()}
        )
    except exceptions.MissingSchema:
        print('Please provide a valid URL', 'error')
        quit()

    if 'error' in request.text:
        if request.status_code == 404:
            print('Post not found', 'error')
        quit()

    try:
        json_data = json.loads(request.text)[0]['data']['children'][0]['data']
        title = f'{json_data["title"]}.mp4'
        print('Post Found!')
        print(f'Title: {title}')
        print(f'In sub-reddit: {json_data["subreddit_name_prefixed"]}')
        print(f'Posted by: {json_data["author"]}')
    except json.decoder.JSONDecodeError:
        print('Post not found', 'error')
        quit()

    file_path = os.path.join(
        CURRENT_DIR_PATH, 'reddit_downloads', title)
    if check_file_exists(file_path):
        return file_path
    downlaod_media(get_video_url(json_data), 'video.mp4')
    downlaod_media(get_audio_url(json_data), 'audio.aac')
    print('output file path', file_path)

    stitch_video('video.mp4', 'audio.aac', file_path)
    # cleaning temp files
    print('cleaning temp files')
    os.remove(f'video.mp4')
    os.remove(f'audio.aac')

    return file_path


if __name__ == '__main__':
    # change this url to the post's url
    post_url = "https://www.reddit.com/r/blog/comments/rbqu7c/reddit_recap_2021/"
    reddit_downloader(post_url)
