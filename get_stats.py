import json
from datetime import datetime

import requests

DEBUG = False


def get_first_publication_date(package_name):
    url = f"https://registry.npmjs.org/{package_name}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        first_published = data["time"]["created"]
        return first_published.split("T")[0]
    else:
        print(f"Error fetching first publication date: {response.status_code}")
        return "2000-01-01"


# npm package download stats
def get_npm_downloads(package_name):
    start_date = get_first_publication_date(package_name)
    end_date = datetime.now().strftime("%Y-%m-%d")  # Current date
    url = (
        f"https://api.npmjs.org/downloads/range/{start_date}:{end_date}/{package_name}"
    )
    response = requests.get(url)

    if DEBUG:
        print(json.dumps(response.json(), indent=2))

    if response.status_code == 200:
        data = response.json()
        total_downloads = sum(day["downloads"] for day in data["downloads"])
        days_between = (
            datetime.strptime(end_date, "%Y-%m-%d")
            - datetime.strptime(start_date, "%Y-%m-%d")
        ).days
        print(
            f"NPM Downloads: {total_downloads:,} for {days_between:,} days, from {start_date} to {end_date}."
        )
        return total_downloads
    else:
        print(f"Error fetching download data: {response.status_code}")
        return 0


def get_first_pypi_release_date(package_name):
    url = f"https://pypi.org/pypi/{package_name}/json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        releases = data["releases"]
        release_dates = []
        for version, release_info in releases.items():
            if release_info:  # Check if the release_info is not empty
                release_date = release_info[0].get("upload_time")
                if release_date:
                    release_dates.append(
                        datetime.strptime(release_date, "%Y-%m-%dT%H:%M:%S")
                    )
        if release_dates:
            first_release_date = min(release_dates)
            return first_release_date.strftime("%Y-%m-%d")
        else:
            print("No release dates found for the package.")
            return "2000-01-01"
    else:
        print(f"Error fetching first release date: {response.status_code}")
        return "2000-01-01"


# PyPI total downloads using pepy.tech
def get_pypi_downloads(package_name):
    start_date = get_first_pypi_release_date(package_name)
    end_date = datetime.now().strftime("%Y-%m-%d")  # Current date

    # Use pepy.tech to get total downloads
    url = f"https://pepy.tech/api/v2/projects/{package_name}"
    response = requests.get(url)

    if DEBUG:
        print(json.dumps(response.json(), indent=2))

    if response.status_code == 200:
        data = response.json()
        total_downloads = data["total_downloads"]
        days_between = (
            datetime.strptime(end_date, "%Y-%m-%d")
            - datetime.strptime(start_date, "%Y-%m-%d")
        ).days
        print(
            f"PyPI Downloads: {total_downloads:,} for {days_between:,} days, from {start_date} to {end_date}."
        )
        return total_downloads
    else:
        print(f"Error fetching download data: {response.status_code}")
        return 0


# GitHub release download stats
def get_github_downloads(repo_owner, repo_name):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases"
    response = requests.get(url)
    if response.status_code == 200:
        releases = response.json()
        print()
        download_count = sum(
            asset["download_count"]
            for release in releases
            for asset in release["assets"]
        )
        return download_count
    return 0


npm_downloads = get_npm_downloads("cdk-comprehend-s3olap")
pypi_downloads = get_pypi_downloads("cdk-comprehend-s3olap")
github_downloads = get_github_downloads("HsiehShuJeng", "cdk-comprehend-s3olap-go")

print(f"NPM Downloads: {npm_downloads}")
print(f"PyPI Downloads: {pypi_downloads}")
print(f"GitHub Downloads: {github_downloads}")
