# Example SIEM API Client

The included example Python script can be used as a client for Cirrus Identity's SIEM API. The client is written in Python and can be run interactively from the command line, or launched periodically via Cron.

In its simplest form, the client can fetch all recent log entries from the SIEM API, writing the output on STDOUT in JSON format. By piping the output to a file and monitoring that file using your institution's SIEM solution (e.g. via an agent installed on the same machine running the client), logs can be collected and sent to your SIEM for further analysis.

## Prerequisites

The client requires an installed Python3 distribution. This is included with most modern Linux distributions, but may need to be installed manually if a stripped-down version of the OS distribution is being used. Use your distro's package manager (e.g. Yum, DNF, apt-get) to install python3

One Python library is required that is not present in the default install. To install it, run:
`pip install requests`

## Usage

The client can be run interactively or periodically from Cron. Use the client interactively to run targeted searches or to test connectivity. Run the client from Cron to fetch all of the most recent logs. Each time the client is run, it will fetch the most recent logs from where it left off.

Some command line options are common to both types of use. The following table summarizes common options:
| Parameter | Description | Format | Default |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | --------------------- |
| `--apikey` | The API Key assigned by Cirrus for your organization. If not specified, the client will look in the `API_KEY` Environment variable | String | |
| `--apisecret` | The API Secret for your API key. If not specified, the client will look in the `API_SECRET` Environment variable | String | |
| `--orgurl` | If your organization's API Key is authorized to access more than one Organization URL, provide a single Org URL to limit scope (searching across multiple Organizations is not supported) | URL | |
| `--apiurl` | (Optional) The URL of the Cirrus Identity SIEM API | URL | Cirrus Identity's Production SIEM API Service |
| `--limit` | (Optional) Limit how many results _per API query_ are returned. Combine with `-x` to limit the total number of results returned | Integer | 1000 |
| `-x` | (Optional) Only execute one API query, even if more results are available. Use this option to test your query, or to determine whether any results are available | flag | Off |
| `-v` | (Optional) Verbose. Write debugging information to STDERR | flag | Off |

### Interactive Usage

Run the client interactively to conduct targeted searches of log data. Use command line options to build a custom search.
The following command-line options are available to customize the search:

| Parameter | Description                                                                                                                                                                                                                                     | Format                                                                                       | Default               |
| --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | --------------------- |
| `--since` | Filters the lower time bound of the log events timestamp property                                                                                                                                                                               | The Internet Date/Time Format profile of ISO 8601, in UTC, for example: 2017-05-03T16:22:18Z | 7 days prior to until |
| `--until` | Filters the upper time bound of the log events timestamp property for bounded queries. If a time in the future is specified, it will be replaced with the current time                                                                          | The Internet Date/Time Format profile of ISO 8601, in UTC, for example: 2017-05-03T16:22:18Z | Current time          |
| `--query` | Specify additional comma-separated key=value search terms to further filter results. Only exact matches are returned. The following keys are supported: `tenant`, `service`, `metrictype`, `metricsubtype`, `clientip`, `correlationid`, `user` | String of key=value pairs                                                                    |

By default, the client will continually fetch from the SIEM API until all results matching the search have been returned. See the `-x` option to limit results to a single fetch

### Streaming Logs

Use the `-c` command line option to stream logs continuously. The first time the client is invoked, it will fetch the most recent 7 days of logs. When the client has downloaded the most recent log entry (the SIEM API returned fewer results than the specified `limit`), the client saves the position it left off at in `/tmp/example-client.run`. The next time it is invoked with the `-c` option, it reads its starting position from the same file and continues to fetch logs until the result set is smaller than the specified `limit`. This can be continued indefinitely. A `--since` parameter may optionally be specified on the first invocation to change how many days in the past of logs are fetched
