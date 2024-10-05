import json
import os
from datetime import datetime
from functools import lru_cache

import duckdb
import requests
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv

from utilities import Colors

load_dotenv()

DEBUG = False
GITHUB_TOKEN = os.getenv("github_token")


class PackageManager:
    def __init__(self, package_name):
        self.package_name = package_name


class NpmPackageManager(PackageManager):
    def get_first_publication_date(self):
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
    def get_first_release_date(self):
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
    def handle_maven_stats(self):
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
    def __init__(self, package_name):
        super().__init__(package_name)
        self.dotnet_package_name = self._transform_package_name(package_name)

    def _transform_package_name(self, package_name):
        parts = package_name.split("-")
        transformed_parts = [part.capitalize() for part in parts if part != "cdk"]
        transformed_name = ".".join(transformed_parts)
        return transformed_name

    def _convert_download_count(self, download_string):
        """Convert formatted download strings like '132.2K' to actual numbers."""
        if "K" in download_string:
            return int(float(download_string.replace("K", "")) * 1000)
        elif "M" in download_string:
            return int(float(download_string.replace("M", "")) * 1000000)
        else:
            return int(download_string)

    def get_earliest_date(self):
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
    def get_import_count(self):
        package_name = self.package_name.replace("-", "")
        if package_name.endswith("go"):
            package_name = package_name[:-2]
        module_url = f"https://pkg.go.dev/github.com/HsiehShuJeng/{self.package_name}/{package_name}/v2/jsii"
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
        go_import_count = self.get_import_count()
        total_clones, unique_clones = self.get_github_clone_count(
            github_owner, github_repo
        )

        return {
            "go_import_count": go_import_count,
            "total_clones": total_clones,
            "unique_clones": unique_clones,
        }


# Example usage:
npm_manager = NpmPackageManager("cdk-comprehend-s3olap")
npm_downloads = npm_manager.get_downloads()

pypi_manager = PyPiPackageManager("cdk-comprehend-s3olap")
pypi_downloads = pypi_manager.get_downloads()

java_manager = JavaPackageManager("cdk-comprehend-s3olap")
java_downloads = java_manager.get_downloads()

nuget_manager = NugetPackageManager("cdk-comprehend-s3olap")
nuget_downloads = nuget_manager.get_downloads()

go_manager = GoPackageManager("cdk-comprehend-s3olap-go")
go_stats = go_manager.get_module_stats("HsiehShuJeng", "cdk-comprehend-s3olap-go")
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
