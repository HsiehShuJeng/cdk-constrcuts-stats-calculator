# cdk-constrcuts-stats-calculator
# Content Table
* [Brief](#brief)
* [Stats](#stats)
* [Notes for Download Count Mechanism](#notes-for-download-count-mechanism)
    * [Java](#java)
    * [NuGET](#nuget)
    * [Go](#go)
* [TO-DO](#to-do)

# Brief
This is a calculator to get donwload stats for all custom CDK constructs crafted by me. The following are current CDK Constrcuts I maintained:
1. [cdk-comprehend-s3olap](https://github.com/HsiehShuJeng/cdk-comprehend-s3olap)
2. [cdk-lambda-subminute](https://github.com/HsiehShuJeng/cdk-lambda-subminute)
3. [cdk-emrserverless-with-delta-lake](https://github.com/HsiehShuJeng/cdk-emrserverless-with-delta-lake)
4. [cdk-databrew-cicd](https://github.com/HsiehShuJeng/cdk-databrew-cicd)
5. [projen-statemachine](https://github.com/HsiehShuJeng/projen-simple)

Of course, you can also glance at the [Construct Hub](https://constructs.dev/search?q=scott.hsieh&offset=0). And this stats calculator is developed with assitance by [ChatGPT](https://openai.com/chatgpt/) and [Amazon Q Developer](https://aws.amazon.com/tw/q/developer/).


# Stats
| Construct                 | cdk-comprehend-s3olap | cdk-lambda-subminute | cdk-emrserverless-with-delta-lake | cdk-databrew-cicd | projen-statemachine | **Total** |
|---------------------------|-----------------------|-----------------------|-----------------------|-----------------------|-----------------------|---------|
| **NPM**               | 262,446 | 195,637 | 115,529 | 64,279 | 81,805 | 719,696 |
| **PyPI**               | 478,205 | 516,727 | 498,361 | 503,844 | 414,554 | 2,411,691 |
| **Java**               | 51,241 | 54,997 | 71,587 | 60,393 | 73,626 | 311,844 |
| **NuGet**               | 132,200 | 128,900 | 113,600 | 114,600 | 129,600 | 618,900 |
| **Go**               | 2 | 1 | 4 | 1 | 1 | 9 |
| **Total**                 | 924,094 | 896,262 | 799,081 | 743,117 | 699,586 | 4,062,140 |

# Notes for Download Count Mechanism
## Java
* [Now available: Central download statistics for OSS projects](https://www.sonatype.com/blog/2010/12/now-available-central-download-statistics-for-oss-projects)

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Currently, you can only log in to the Sonatype Nexus Repository and view related statistics for your packages on the ‘Central Statistics’ page. To export data, you need to download it in CSV format through the UI, as there is no API available for Java package download stats at this time.  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Though you can get a CSV file for the stats of a specific pacakge yet you only get the track of the last year. Therefore, all of the Java constructs are accumuluated by Oct. 1st, 2023. Records starting from `2023.10.01` will be stored on my side.  

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