import os
import time
import urllib.request

from urllib.error import URLError

from . import log


def download_log(job_id: (str, int), destination: str, retries: int = 3):
    """
    Downloads a Travis job log and stores it at destination.

    :param job_id: Travis job ID for which to download the log, as a string or integer.
    :param destination: Path where the log should be stored.
    :param retries: The number of times to retry the log download if it fails. Defaults to 3, in which case the network
                    will be accessed up to 4 (3 + 1) times.
    :raises ValueError:
    :raises FileExistsError: When a file at `destination` already exists.
    :return: True if the download succeeded.
    """
    if not job_id:
        raise ValueError
    if not destination:
        raise ValueError
    if os.path.isfile(destination) and os.path.getsize(destination) > 0:
        log.error('The log for job', job_id, 'already exists locally.')
        raise FileExistsError

    job_id = str(job_id)

    aws_log_link = 'https://s3.amazonaws.com/archive.travis-ci.org/jobs/{}/log.txt'.format(job_id)
    travis_log_link = 'https://api.travis-ci.org/jobs/{}/log.txt'.format(job_id)

    content = _get_log_from_url(aws_log_link, retries) or _get_log_from_url(travis_log_link, retries)

    if not content:
        return False

    with open(destination, 'wb') as f:
        f.write(content)
    return True


def _get_log_from_url(log_url: str, max_retries: int, retry_count: int = 0):
    sleep_duration = 3  # Seconds.
    try:
        with urllib.request.urlopen(log_url) as url:
            result = url.read()
            log.info('Downloaded log from {}.'.format(log_url))
            return result
    except URLError:
        log.error('Could not download log from {}.'.format(log_url))
        return None
    except ConnectionResetError:
        if retry_count == max_retries:
            log.error('Could not download log from', log_url, 'after retrying', max_retries, 'times.')
            return None
        log.warning('The server reset the connection. Retrying after', sleep_duration, 'seconds.')
        time.sleep(sleep_duration)
        _get_log_from_url(log_url, max_retries, retry_count + 1)
