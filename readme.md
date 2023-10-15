# Store Monitoring
## Problem statement
Loop monitors several restaurants in the US and needs to monitor if the store is online or not. All restaurants are supposed to be online during their business hours. Due to some unknown reasons, a store might go inactive for a few hours. Restaurant owners want to get a report of the how often this happened in the past.

## Data sources

This system as three data sources:

1. A CSV file that has 3 columns (store_id, timestamp_utc, status) where status is active or inactive. All timestamps are in UTC
2. A CSV where the business hours of all the stores are present - schema of this data is (store_id, dayOfWeek(0=Monday, 6=Sunday), start_time_local, end_time_local)
    
    - the given times are in local time
    - if the data for any store is missing, then that store is open 24 * 7
3. A CSV where all timezones for the stores are present - schema is (store_id, timezone_str)
    - if data for any store is missing, then it's local timezone is "America/Chicago"
    - this data can be used to compare the data from sources 1 and 2

## System requirement

- the given data is not static and will keep getting updated every hour
- the given data must be stored in a relevant database and API calls must be made to get the data

## Installation

Python 3.x - required

Install the dependent packages by running the following command in the project directory
```
    pip install -r requirements.txt
```

To start the server, run the follwing command in the project directory
```
    py .\src\main.py
```
The server will start running on http://localhost:8081/

## API Doc

This system exposes two endpoints:

1. /trigger_report

    - this endpoint takes no input
    - it returns a unique identifier string for the report being generated, say, the report_id
    - this "report_id" will be used by the second endpoint for polling the status of report completion

    - Request
            
            curl --location 'http://127.0.0.1:8081/trigger_report'


    - Response

            HTTP/1.1 OK
            {
                'status': "success",
                'report_id': report_id
            }


2. /get_report

    - this endpoint takes the report_id generated by the first endpoint as the input
    - if report generation is not complete, it return a status of "Running"
    - if report generation is complete, it returns a status of "Complete", along with the csv file of the report

    - Request 
                
            curl --location --request 
            GET 'http://127.001:8081/get_report' \
                --header 'Content-Type: application/json' \
                --data '{
                    "report_id":
    
                    "73267251-06ca-4a9f-9100
                    -22fa83c231d3"
                }'
    - Response

                HTTP/1.1 202 ACCEPTED
                {
                    'status': 'Running',
                }

                HTTP/1.1 200 OK
                {
                    'status': 'Complete',
                    'data': '...'
                }

                HTTP/1.1 404 Not Found
                {
                    'status': 'No such report Id!'
                }

## Solution statement

### Data persisting and refreshing

The schema.sql contains the schema for tables and the indexes used for speeding up the query execution

We persist the data if there is not data present.

We create a daemon thread that runs in the background as long as the server is up and running. This thread will refresh the data in the database every hour with the newly updated poll data.

### Observations
- Each store can have multiple segments of business hours in a single day.
Ex. 00:00:00 to 04:00:00, 09:00:00 to 18:30:00, etc
- Status polls for each hour in business hours are not necessarily available in the data source. Conversely, status polls for non-business hours are present.

### Logic
- We go through each store and find their business hours for each day and then we get the business hours in UTC time.

- We go through each segment of the business hours and keep track of the previous valid status and timestamp.

- For each business hours segment we find all the relevant poll data and go through each poll.

- The previous timestamp and the current poll timestamp make up one interval. With the help of previous status we store the time difference in the uptime or downtime.

- At the end of each business hours segment we are left with the last interval, which is between the last poll timestamp and the current business hours segment's end time. We store the time difference accordingly.

- We store all the uptime and downtime data and keep updating the same.

- When we calculate the last hour uptime and downtime. There can be a case where the business hours segment's end time is before the last hour's end time. Here we have to set the end time as the business hour segment's end time and ignore the last hour's end time.

### Others

- We get the timezones for each store and keep them in-memory for faster access.

- We created relevant indexes for retrieving data from the database in a faster way.