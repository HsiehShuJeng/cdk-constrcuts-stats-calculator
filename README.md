# cdk-constrcuts-stats-calculator
# Brief
This is a calculator to get donwload stats for all custom CDK constructs crafted by me. The following are current CDK Constrcuts I maintained:
1. [cdk-comprehend-s3olap](https://github.com/HsiehShuJeng/cdk-comprehend-s3olap)
2. [cdk-lambda-subminute](https://github.com/HsiehShuJeng/cdk-lambda-subminute)
3. [cdk-emrserverless-with-delta-lake](https://github.com/HsiehShuJeng/cdk-emrserverless-with-delta-lake)
4. [cdk-databrew-cicd](https://github.com/HsiehShuJeng/cdk-databrew-cicd)
5. [projen-statemachine](https://github.com/HsiehShuJeng/projen-simple)

Of course, you can glance at the [Construct Hub](https://constructs.dev/search?q=scott.hsieh&offset=0) also.

# Notes for Download Count Mechanism
## Java
* [Now available: Central download statistics for OSS projects](https://www.sonatype.com/blog/2010/12/now-available-central-download-statistics-for-oss-projects)

Currently, you can only log in to the Sonatype Nexus Repository and view related statistics for your packages on the ‘Central Statistics’ page. To export data, you need to download it in CSV format through the UI, as there is no API available for Java package download stats at this time.  
> In other words, to get the latest download stats, I still need to download all of CSV files into proper place under this directory before executing `python get_stats.py`.

## NuGET
* [NuGet Server API](https://learn.microsoft.com/en-us/nuget/api/overview)
* [Pacakge metadata](https://learn.microsoft.com/en-us/nuget/api/registration-base-url-resource)
* [Sonatype repository manager](https://s01.oss.sonatype.org/)

## Go
* [Github: Can I see the number of downloads for a repo?](https://stackoverflow.com/questions/4338358/github-can-i-see-the-number-of-downloads-for-a-repo)
* [About pkgsite](https://pkg.go.dev/about#best-practices)

More accurate method to collect download stats might exist.

# TO-DO
Further investigation is needed on the implementation of the [maven_stats.py](./maven_stats.py) script. The main objective of this script is to automate the process of downloading a CSV file that contains statistics for a specific package via the Sonatype Nexus Repository’s web interface.

There are some click actions in the script that still need to be verified and fine-tuned to work smoothly in Selenium. These click interactions, particularly for buttons and form fields, might need adjustments such as using alternative methods like JavaScript-triggered clicks or more robust waiting mechanisms.

Once these improvements are implemented, the automation process should run more efficiently, allowing the seamless extraction of package stats in CSV format without manual intervention.