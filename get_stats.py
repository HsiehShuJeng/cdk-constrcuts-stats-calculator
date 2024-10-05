"""
This module calculates download statistics for various packages across different platforms (NPM, PyPI, Java, NuGet, Go).

It defines classes for each package manager (NPM, PyPI, Java, NuGet, Go) to retrieve relevant statistics such as
first release dates and total downloads. Additionally, it includes functions to compute and format the total 
downloads for a list of constructs and generates a markdown table summarizing these statistics.

Classes:
    PackageManager: Base class for managing packages.
    NpmPackageManager: Class for handling NPM packages.
    PyPiPackageManager: Class for handling PyPI packages.
    JavaPackageManager: Class for handling Java Maven packages.
    NugetPackageManager: Class for handling NuGet packages.
    GoPackageManager: Class for handling Go modules.

Functions:
    calculate_total_downloads_for_table: Calculates total downloads for a given construct across multiple platforms.
    create_markdown_table: Generates a markdown table with download statistics for multiple constructs.
    main: Main function to calculate and display download statistics for a predefined set of constructs.

This module also supports the following features:
- Fetching and parsing data from various APIs such as NPM, PyPI, Maven, NuGet, and Go's package registry.
- Combining Go import statistics with GitHub clone statistics for a more complete view of Go module usage.
- Caching API responses for efficiency using functools.lru_cache.
"""

import json
import os
import time
from datetime import datetime
from functools import lru_cache

import duckdb
import pyperclip
import requests
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv

from utilities import Colors

load_dotenv()

DEBUG = False
GITHUB_TOKEN = os.getenv("github_token")


class PackageManager:
    """Base class for package managers.

    Args:
        package_name (str): The name of the package to manage.
    """

    def __init__(self, package_name):
        self.package_name = package_name


class NpmPackageManager(PackageManager):
    """Handles NPM package downloads and metadata retrieval.

    Args:
        package_name (str): The name of the NPM package to manage.
    """

    def __init__(self, package_name):
        super().__init__(package_name)
        if package_name == "projen-statemachine":
            self.package_name = "projen-statemachine-example"

    @lru_cache(maxsize=10)
    def get_first_publication_date(self):
        """Fetches the first publication date of the NPM package.

        Returns:
            str: The first publication date in 'YYYY-MM-DD' format, or '2000-01-01' if unavailable.
        """
        url = f"https://registry.npmjs.org/{self.package_name}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            first_published = data["time"]["created"]
            return first_published.split("T")[0]
        else:
            print(f"Error fetching first publication date: {response.status_code}")
            return "2000-01-01"

    @lru_cache(maxsize=10)
    def get_downloads(self):
        """Fetches the total download count of the NPM package.

        Returns:
            int: The total number of downloads.
        """
        start_date = self.get_first_publication_date()
        end_date = datetime.now().strftime("%Y-%m-%d")  # Current date
        url = f"https://api.npmjs.org/downloads/range/{start_date}:{end_date}/{self.package_name}"
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
                f"NPM Downloads: {total_downloads:,} for {days_between:,} days, from {Colors.BRIGHT_BLUE}{start_date}{Colors.RESET} to {Colors.BRIGHT_BLUE}{end_date}{Colors.RESET}."
            )
            return total_downloads
        else:
            print(f"Error fetching download data: {response.status_code}")
            return 0


class PyPiPackageManager(PackageManager):
    """Handles PyPi package downloads and metadata retrieval.

    Args:
        package_name (str): The name of the PyPi package to manage.
    """

    def __init__(self, package_name):
        super().__init__(package_name)
        if package_name == "projen-statemachine":
            self.package_name = f"scotthsieh-{package_name}"

    @lru_cache(maxsize=10)
    def get_first_release_date(self):
        """Fetches the first release date of the PyPi package.

        Returns:
            str: The first release date in 'YYYY-MM-DD' format, or '2000-01-01' if unavailable.
        """
        url = f"https://pypi.org/pypi/{self.package_name}/json"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            releases = data["releases"]
            release_dates = [
                datetime.strptime(release_info[0]["upload_time"], "%Y-%m-%dT%H:%M:%S")
                for version, release_info in releases.items()
                if release_info
            ]
            if release_dates:
                first_release_date = min(release_dates)
                return first_release_date.strftime("%Y-%m-%d")
            else:
                print("No release dates found for the package.")
                return "2000-01-01"
        else:
            print(f"Error fetching first release date: {response.status_code}")
            return "2000-01-01"

    def get_downloads(self):
        """Fetches the total download count of the PyPi package.

        Returns:
            int: The total number of downloads.
        """
        start_date = self.get_first_release_date()
        end_date = datetime.now().strftime("%Y-%m-%d")  # Current date

        # Use pepy.tech to get total downloads
        url = f"https://pepy.tech/api/v2/projects/{self.package_name}"
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
                f"PyPI Downloads: {total_downloads:,} for {days_between:,} days, from {Colors.BRIGHT_BLUE}{start_date}{Colors.RESET} to {Colors.BRIGHT_BLUE}{end_date}{Colors.RESET}."
            )
            return total_downloads
        else:
            print(f"Error fetching download data: {response.status_code}")
            return 0


class JavaPackageManager(PackageManager):
    """Handles Java Maven package downloads and metadata retrieval.

    Args:
        package_name (str): The name of the Java Maven package to manage.
    """

    def handle_maven_stats(self):
        """Processes and updates Maven statistics for the Java package."""
        csv_file = f"maven-stats-source/{self.package_name}.csv"
        parquet_file = f"maven-stats-source/accumulation/{self.package_name}.parquet"
        transformed_table = "updated_stats"
        parquet_table = "existing_stats"
        export_date = datetime.now()
        start_month = export_date - relativedelta(years=1)
        start_month_str = start_month.strftime("%Y-%m-%d")
        conn = duckdb.connect(database=":memory:")

        conn.sql(
            f"""
            CREATE TABLE {transformed_table} AS 
            SELECT column0 AS downloads, 
                   strftime(DATE '{start_month_str}' + INTERVAL (ROW_NUMBER() OVER () - 1) MONTH, '%Y-%m') AS year_month
            FROM read_csv_auto('{csv_file}', header=False);
        """
        )
        if DEBUG:
            conn.sql(f"SELECT * FROM {transformed_table}").show()

        if os.path.exists(parquet_file):
            conn.sql(
                f"CREATE TABLE {parquet_table} AS SELECT * FROM read_parquet('{parquet_file}')"
            )
            conn.sql(
                f"DELETE FROM {parquet_table} WHERE year_month IN (SELECT year_month FROM {transformed_table})"
            )
            conn.sql(f"INSERT INTO {parquet_table} SELECT * FROM {transformed_table}")
            conn.sql(
                f"COPY (SELECT * FROM {parquet_table}) TO '{parquet_file}' (FORMAT 'PARQUET', CODEC 'ZSTD')"
            )
        else:
            conn.sql(
                f"COPY (SELECT * FROM {transformed_table}) TO '{parquet_file}' (FORMAT 'PARQUET', CODEC 'ZSTD')"
            )

    def get_downloads(self):
        """Fetches the total download count of the Java Maven package.

        Returns:
            int: The total number of downloads.
        """
        self.handle_maven_stats()
        parquet_file = f"maven-stats-source/accumulation/{self.package_name}.parquet"
        if not os.path.exists(parquet_file):
            print(f"Parquet file for {self.package_name} not found.")
            return 0

        conn = duckdb.connect(database=":memory:")
        try:
            result = conn.sql(
                f"SELECT SUM(downloads) AS total_downloads, MIN(year_month) AS start_date FROM read_parquet('{parquet_file}')"
            ).fetchone()
            total_downloads, start_date = result if result else (0, None)
            if start_date is None:
                print("No valid start date found.")
                return 0
            end_date = datetime.now().strftime("%Y-%m-%d")
            days_between = (
                datetime.strptime(end_date, "%Y-%m-%d")
                - datetime.strptime(start_date, "%Y-%m")
            ).days
            print(
                f"Java Construct Downloads: {total_downloads:,} for {days_between:,} days, from {Colors.BRIGHT_BLUE}{start_date}{Colors.RESET} to {Colors.BRIGHT_BLUE}{end_date}{Colors.RESET}."
            )
            return total_downloads
        except Exception as e:
            print(f"Error while fetching Java construct downloads: {e}")
            return 0


class NugetPackageManager(PackageManager):
    """Handles NuGet package downloads and metadata retrieval.

    Args:
        package_name (str): The name of the NuGet package to manage.
    """

    def __init__(self, package_name):
        super().__init__(package_name)
        self.dotnet_package_name = self._transform_package_name(package_name)

    def _transform_package_name(self, package_name):
        """Transforms package name into a dot-separated .NET format.

        Args:
            package_name (str): The original package name with hyphens.

        Returns:
            str: The transformed package name in .NET convention.
        """
        parts = package_name.split("-")
        transformed_parts = [part.capitalize() for part in parts if part != "cdk"]
        transformed_name = ".".join(transformed_parts)
        return transformed_name

    def _convert_download_count(self, download_string):
        """Converts a formatted download count string (e.g., '132.2K') into an integer.

        Args:
            download_string (str): The download count string from NuGet.

        Returns:
            int: The converted download count as an integer.
        """
        """Convert formatted download strings like '132.2K' to actual numbers."""
        if "K" in download_string:
            return int(float(download_string.replace("K", "")) * 1000)
        elif "M" in download_string:
            return int(float(download_string.replace("M", "")) * 1000000)
        else:
            return int(download_string)

    @lru_cache(maxsize=10)
    def get_earliest_date(self):
        """Retrieves the earliest release date of the NuGet package.

        Returns:
            str: The earliest release date in 'YYYY-MM-DD' format, or None if not found.
        """
        url = f"https://www.nuget.org/packages/{self.dotnet_package_name}/0.0.0"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            sidebar_sections = soup.find_all("div", class_="sidebar-section")

            for section in sidebar_sections:
                header = section.find("div", class_="sidebar-headers")
                if header and "About" in header.get_text():
                    date_tag = section.find("span", {"data-datetime": True})
                    if date_tag:
                        earliest_upload = date_tag["data-datetime"]
                        return earliest_upload.split("T")[
                            0
                        ]  # Return only the date part
                    else:
                        print("Could not find a span with 'data-datetime' attribute.")
                        return None

            print("'About' section not found in any 'sidebar-section'.")
            return None
        else:
            print(f"Error fetching NuGet package page: {response.status_code}")
            return None

    def get_downloads(self):
        """Fetches the total download count of the NuGet package.

        Returns:
            int: The total number of downloads, or 0 if an error occurs.
        """
        start_date = self.get_earliest_date()
        if not start_date:
            return 0

        url = f"https://www.nuget.org/packages/{self.dotnet_package_name}/"
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            total_downloads = soup.find(
                "span", class_="download-info-content"
            ).text.strip()
            total_downloads = self._convert_download_count(total_downloads)
            end_date = datetime.now().strftime("%Y-%m-%d")
            days_between = (
                datetime.strptime(end_date, "%Y-%m-%d")
                - datetime.strptime(start_date, "%Y-%m-%d")
            ).days
            print(
                f"NuGet Downloads: {total_downloads:,} for {days_between:,} days, from {Colors.BRIGHT_BLUE}{start_date}{Colors.RESET} to {Colors.BRIGHT_BLUE}{end_date}{Colors.RESET}."
            )
            return total_downloads
        else:
            print(f"Error fetching NuGet data: {response.status_code}")
            return 0


class GoPackageManager(PackageManager):
    """Handles Go package statistics like imports and GitHub clones.

    Args:
        package_name (str): The name of the Go package to manage.
    """

    def __init__(self, package_name):
        super().__init__(package_name)
        self.module_name = package_name
        if package_name == "projen-statemachine-go":
            self.package_name = "projen-statemachine-example"
        self.package_name = self.package_name.replace("-", "")
        if self.package_name.endswith("go"):
            self.package_name = self.package_name[:-2]

    def get_import_count(self):
        """Retrieves the Go module import count from pkg.go.dev.

        Returns:
            int or None: The number of times the module has been imported, or None if not found.
        """
        module_url = f"https://pkg.go.dev/github.com/HsiehShuJeng/{self.module_name}/{self.package_name}/v2/jsii"
        if DEBUG:
            print(f"module_url: {module_url}")
        response = requests.get(module_url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            imported_by_span = soup.find(
                "span", {"data-test-id": "UnitHeader-importedby"}
            )

            if imported_by_span:
                imported_by_link = imported_by_span.find(
                    "a", {"aria-label": lambda x: x and "Imported By" in x}
                )

                if imported_by_link:
                    imported_by_count = (
                        imported_by_link["aria-label"].split(":")[1].strip()
                    )
                    return int(imported_by_count)
                else:
                    print("Could not find the 'Imported By' link on the page.")
                    return None
            else:
                print("Could not find the 'Imported By' section on the page.")
                return None
        else:
            print(f"Error fetching the page: {response.status_code}")
            return None

    def get_github_clone_count(self, github_owner, github_repo):
        """Fetches GitHub clone statistics for the Go package repository.

        Args:
            github_owner (str): GitHub repository owner.
            github_repo (str): GitHub repository name.

        Returns:
            tuple: A tuple containing total clone count and unique clone count.
        """
        url = (
            f"https://api.github.com/repos/{github_owner}/{github_repo}/traffic/clones"
        )
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            total_clones = data.get("count", 0)
            unique_clones = data.get("uniques", 0)
            return total_clones, unique_clones
        else:
            print(f"Error fetching GitHub clone data: {response.status_code}")
            return 0, 0

    def get_module_stats(self, github_owner, github_repo):
        """Combines Go import and GitHub clone statistics.

        Args:
            github_owner (str): GitHub repository owner.
            github_repo (str): GitHub repository name.

        Returns:
            dict: A dictionary containing Go import count, total GitHub clones, and unique GitHub clones.
        """
        go_import_count = self.get_import_count()
        total_clones, unique_clones = self.get_github_clone_count(
            github_owner, github_repo
        )
        if DEBUG:
            print(
                json.dumps(
                    {
                        "go_import_count": go_import_count,
                        "total_clones": total_clones,
                        "unique_clones": unique_clones,
                    },
                    indent=4,
                )
            )

        return {
            "go_import_count": go_import_count,
            "total_clones": total_clones,
            "unique_clones": unique_clones,
        }


def calculate_total_downloads_for_table(construct_name):
    """Calculates total downloads for a given construct across multiple platforms.

    This function fetches download statistics for NPM, PyPI, Java, NuGet, and Go platforms
    using their respective package managers, then computes the total downloads for each construct.

    Args:
        construct_name (str): The name of the construct whose download statistics need to be calculated.

    Returns:
        tuple: A dictionary containing total downloads and individual platform downloads,
               and the time taken for the calculation.
    """
    start_time = time.time()
    print(f"Checking {Colors.BRIGHT_BLUE}{construct_name}{Colors.RESET}...")

    # Initialize managers and fetch stats for each platform
    npm_manager = NpmPackageManager(construct_name)
    npm_downloads = npm_manager.get_downloads()

    pypi_manager = PyPiPackageManager(construct_name)
    pypi_downloads = pypi_manager.get_downloads()

    java_manager = JavaPackageManager(construct_name)
    java_downloads = java_manager.get_downloads()

    nuget_manager = NugetPackageManager(construct_name)
    nuget_downloads = nuget_manager.get_downloads()

    go_manager = GoPackageManager(f"{construct_name}-go")
    go_stats = go_manager.get_module_stats("HsiehShuJeng", f"{construct_name}-go")
    go_downloads = go_stats["go_import_count"] + go_stats["total_clones"]

    total_downloads = (
        npm_downloads + pypi_downloads + java_downloads + nuget_downloads + go_downloads
    )
    print(
        f"There are {Colors.GREEN}{total_downloads:,}{Colors.RESET} for {Colors.GREEN}{npm_manager.package_name}{Colors.RESET}, including 5 programming languages."
    )
    print(f"\tNPM downloads: {npm_downloads:,}")
    print(f"\tPyPI downloads: {pypi_downloads:,}")
    print(f"\tJava downloads: {java_downloads:,}")
    print(f"\tNuGet downloads: {nuget_downloads:,}")
    print(f"\tGo downloads (imports): {go_downloads:,}")
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Time taken for {construct_name}: {total_time:.2f} seconds")

    return {
        "total": total_downloads,
        "npm": npm_downloads,
        "pypi": pypi_downloads,
        "java": java_downloads,
        "nuget": nuget_downloads,
        "go": go_downloads,
    }, total_time


def create_markdown_table(constructs, total_downloads_data):
    """Generates a markdown table showing download statistics across different constructs.

    This function creates a markdown-formatted table displaying the downloads across
    five platforms (NPM, PyPI, Java, NuGet, Go) for each construct and calculates the totals.

    Args:
        constructs (list of str): The list of construct names.
        total_downloads_data (dict): The dictionary containing download data for each construct.

    Returns:
        None: Copies the generated markdown table to the clipboard.
    """
    # Generate table header
    markdown_table = (
        "| Construct                 | " + " | ".join(constructs) + " | **Total** |\n"
    )
    markdown_table += (
        "|---------------------------|"
        + "-----------------------|" * len(constructs)
        + "---------|\n"
    )

    # Extract and add downloads per platform, with a row-wise total formatted with commas
    platforms = ["NPM", "PyPI", "Java", "NuGet", "Go"]
    for platform in platforms:
        platform_row = [
            f"{total_downloads_data[c][platform.lower()]:,}" for c in constructs
        ]
        row_total = sum([total_downloads_data[c][platform.lower()] for c in constructs])
        markdown_table += (
            f"| **{platform}**               | "
            + " | ".join(platform_row)
            + f" | {row_total:,} |\n"
        )

    # Add total downloads row as the last row
    markdown_table += (
        "| **Total**                 | "
        + " | ".join([f"{total_downloads_data[c]['total']:,}" for c in constructs])
        + " | "
        + f"{sum([total_downloads_data[c]['total'] for c in constructs]):,}"
        + " |\n"
    )

    # Copy the markdown table to clipboard
    pyperclip.copy(markdown_table)
    print("The markdown table has been copied to the clipboard.")


def main():
    """Main function that calculates total downloads for each construct and generates a markdown table.

    This function iterates over a list of constructs, calculates the download statistics for each,
    and creates a markdown table showing the results. It also prints the total time taken for the operation.

    Returns:
        None
    """
    constructs = [
        "cdk-comprehend-s3olap",
        "cdk-lambda-subminute",
        "cdk-emrserverless-with-delta-lake",
        "cdk-databrew-cicd",
        "projen-statemachine",
    ]
    total_downloads_data = {}
    total_elapsed_time = 0
    for custom_construct in constructs:
        total_downloads_data[custom_construct], elapsed_time = (
            calculate_total_downloads_for_table(custom_construct)
        )
        total_elapsed_time += elapsed_time
    print(
        f"Total time taken for {len(constructs):,} constrcuts: {total_elapsed_time:.2f}."
    )
    total_downloads = sum(data["total"] for data in total_downloads_data.values())
    create_markdown_table(constructs, total_downloads_data)
    print(
        f"{Colors.BRIGHT_YELLOW}Total downloads{Colors.RESET} for {Colors.BRIGHT_YELLOW}{len(constructs):,}{Colors.RESET} constructs are {Colors.BRIGHT_YELLOW}{total_downloads:,}{Colors.RESET}."
    )


if __name__ == "__main__":
    main()
