# Gemini Challenge - Alerting Script

## Pre-requisites 
- Required: Python3 and pip installed
- Optional: use virutalenv to install dependencies.  `python -m venv venv` then active the virtualenv `. venv/bin/activate`.
- Required: install the requirments.txt dependecies.  `pip install -r requirements.txt`

## Run 
- `python app.py --help` to view the possible arguments
- Example of running the Price Change alert: `python app.py --alert_type pricechange --deviation 0.05 --symbol btcusd`
- Alert Types
    - pricechange
    - pricedev
    - voldev
    - all 
- Deviations are in float for percentages. `5% == 0.05`

## Improvements
- Not using click to provide set options for alert types. 
- Missing unit tests. Ideally at the very least create tests for the calculation functions.
- Streamline the error handling - instead of various different ways to handle exceptions.

## Future Additions
- Break up the single python file. Use modules for the alerts. For example have an alerts/pricechange.py module that is imported into the app.py script. It would be cleaner approach to adding new alerts to the script.
- Implement the currency argument to pass to the API endpoints. 
- Implement unit testing using.
- How would this run for multiple symbols?
    - Add an 'all' script argument for using all symbols.
    - Create a runner script or a loop that retrieves a list of all the symbols. Runner would incrementally call 'all' per symbol. One issue is hitting the API limitations.
- Create function that validates the symbols using the Gemini API endpoint that gets a list of symbols.  Possibly locally cache on disk that list of symbols with a timestamp. Regularly compare the timestamp to now, after a certain period of time then call the endpoint again to refresh the list. This would be ideal if all the alerts were run for every symbol.  To prevent exceeding the API rate limitations and save on time sending API calls.

## Misc
### Approach to solving
### Issues during impmentation
- I wasn't entirely clear on the implementation of the Volume Deviation alert requirements based on the description.
- Understanding the volume data from the candles API.
### Time spent
- 4 HOURS
