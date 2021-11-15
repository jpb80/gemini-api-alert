# Gemini Challenge - Alerting Script
## About
Script will be run periodically by a monitoring tool, being called directly, generating alerts as output that will feed into an alerting mechanism.

## Pre-requisites 
- Required: install python 3.4.X and pip
- Optional: use virutalenv to install dependencies.  `python -m venv venv` then active the virtualenv `. venv/bin/activate`.
- Required: install the requirements.txt dependecies.  `pip install -r requirements.txt`

## Run 
#### Example of running the Price Change alert
`python app.py --alert_type pricechange --deviation 0.05 --symbol btcusd`

#### Debug Mode
`python app.py --alert_type pricechange --deviation 0.05 --symbol btcusd --debug true`

#### Script inputs
- alert_type
    - pricechange
    - pricedev
    - voldev
    - all 
- deviation
    - Decimal: `0.05 == 5%`
    - Threshold at which the alert will be triggered for pricedev and voldev alert types. 
- symbol
    - Valid exchange currency symbols from the Gemini API symbols endpoint `https://api.gemini.com/v1/symbols`

## Known Issues
- Not using click to provide set options for alert types. 
- Missing unit tests. Ideally at the very least create tests for the calculation functions.
- Streamline the error handling - instead of various different ways to handle exceptions.

## Future Additions
- Create a Dockerfile to build container with the python version and dependencies. Use `ENTRYPOINT ['python','./app.py']` then pass arguments to the script when container is started such as `docker run -it --rm scriptimagename --alert_type pricechange --deviation 0.05 --symbol btcusd`.
- Break up the single python file. Use modules for the alerts. For example have an alerts/pricechange.py module that is imported into the app.py script. It would be cleaner approach to adding new alerts to the script.
- How would this run for multiple symbols?
    - Add an 'all' script argument for using all symbols.
    - Create a runner script or a loop that retrieves a list of all the symbols. Runner would incrementally call 'all' per symbol. One issue is hitting the API limitations.
- Create function that validates the symbols using the Gemini API endpoint that gets a list of symbols.  Possibly locally cache on disk that list of symbols with a timestamp. Regularly compare the timestamp to now, after a certain period of time then call the endpoint again to refresh the list. This would be ideal if all the alerts were run for every symbol.  To prevent exceeding the API rate limitations and save on time sending API calls.

## Misc
### Approach to solving
#### Price Deviation
1. Create functions to query the API.
2. Parse those results as json.
3. Get the current price from api response.
4. Get the average from the array of price changes from api response.
5. Get standard deviation of the array of price changes.
6. Use the ZScore to determine how many deviations a current price is from the sample mean of prices in the last 24 hours.
7. Alert when Zscore is +/-1 standard deviation from the mean.

### Issues during impmentation
- I wasn't entirely clear on the implementation of the Volume Deviation alert requirements based on the description.
- Understanding the volume data from the candles API.
### Time spent
- 4 HOURS
