import json

import argparse

from ._api import YouTubeTranscriptApi
from .formatters import formats


class YouTubeTranscriptCli():
    def __init__(self, args):
        self._args = args

    def run(self):
        parsed_args = self._parse_args()

        if parsed_args.exclude_manually_created and parsed_args.exclude_generated:
            return ''

        proxies = None
        if parsed_args.http_proxy != '' or parsed_args.https_proxy != '':
            proxies = {"http": parsed_args.http_proxy, "https": parsed_args.https_proxy}

        cookies = parsed_args.cookies

        transcripts = []
        exceptions = []

        Formatter = formats.get_formatter(parsed_args.format)

        for video_id in parsed_args.video_ids:
            try:
                transcript = self._fetch_transcript(
                    parsed_args, proxies, cookies, video_id)
                transcripts.append(Formatter.format(transcript))
            except Exception as exception:
                exceptions.append(exception)

        return ''.join(
            [str(exception) for exception in exceptions]
            + ([Formatter.combine(transcripts)] if transcripts else [])
        )

    def _fetch_transcript(self, parsed_args, proxies, cookies, video_id):
        transcript_list = YouTubeTranscriptApi.list_transcripts(
                            video_id, proxies=proxies, cookies=cookies)

        if parsed_args.list_transcripts:
            return str(transcript_list)

        if parsed_args.exclude_manually_created:
            transcript = transcript_list.find_generated_transcript(parsed_args.languages)
        elif parsed_args.exclude_generated:
            transcript = transcript_list.find_manually_created_transcript(parsed_args.languages)
        else:
            transcript = transcript_list.find_transcript(parsed_args.languages)

        if parsed_args.translate:
            transcript = transcript.translate(parsed_args.translate)

        return transcript.fetch()

    def _parse_args(self):
        parser = argparse.ArgumentParser(
            description=(
                'This is an python API which allows you to get the transcripts/subtitles for a given YouTube video. '
                'It also works for automatically generated subtitles and it does not require a headless browser, like '
                'other selenium based solutions do!'
            )
        )
        parser.add_argument(
            '--list-transcripts',
            action='store_const',
            const=True,
            default=False,
            help='This will list the languages in which the given videos are available in.',
        )
        parser.add_argument('video_ids', nargs='+', type=str, help='List of YouTube video IDs.')
        parser.add_argument(
            '--languages',
            nargs='*',
            default=['en',],
            type=str,
            help=(
                'A list of language codes in a descending priority. For example, if this is set to "de en" it will '
                'first try to fetch the german transcript (de) and then fetch the english transcript (en) if it fails '
                'to do so. As I can\'t provide a complete list of all working language codes with full certainty, you '
                'may have to play around with the language codes a bit, to find the one which is working for you!'
            ),
        )
        parser.add_argument(
            '--exclude-generated',
            action='store_const',
            const=True,
            default=False,
            help='If this flag is set transcripts which have been generated by YouTube will not be retrieved.',
        )
        parser.add_argument(
            '--exclude-manually-created',
            action='store_const',
            const=True,
            default=False,
            help='If this flag is set transcripts which have been manually created will not be retrieved.',
        )
        parser.add_argument(
            '--format',
            default=None,
            help="Use this flag to set which parser format to use, default is 'json'",
        )
        parser.add_argument(
            '--translate',
            default='',
            help=(
                'The language code for the language you want this transcript to be translated to. Use the '
                '--list-transcripts feature to find out which languages are translatable and which translation '
                'languages are available.'
            )
        )
        parser.add_argument(
            '--http-proxy',
            default='',
            metavar='URL',
            help='Use the specified HTTP proxy.'
        )
        parser.add_argument(
            '--https-proxy',
            default='',
            metavar='URL',
            help='Use the specified HTTPS proxy.'
        )
        parser.add_argument(
            '--cookies',
            default=None,
            help='The cookie file that will be used for authorization with youtube.'
        )
            
        return parser.parse_args(self._args)
