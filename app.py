#!/usr/bin/env python
# coding=utf-8
import statistics as stats
import sys

import click
import logging
import requests


GEMINI_API_BASE_URL = "https://api.gemini.com"
API_VERSION = "v2"
DEBUG = 10
INFO = 20

log = logging.getLogger(__name__)


def setup_logging(debug):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    loglevel = INFO
    if debug:
        loglevel = DEBUG
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(level=loglevel, stream=sys.stdout,
                        format=logformat, datefmt="%Y-%m-%d %H:%M:%S")


def send_request(url):
    """
    Use the requests library to call the gemini public api.
    """
    try:
        log.info("Sending request to endpoint: %s.", url)
        response = requests.get(url)
        log.debug("Response from api: %s", response)
        response.raise_for_status()
    except requests.exceptions.RequestException as request_exception:
        log.exception("Requests exception: %s", request_exception)
    return response


def calculate_percentage_change(final, initial):
    """
    Formula: percentage change = ((final - initial)/inital) * 100
    """
    log.info("Calculate percentage change between final and inital value.")
    if final and initial:
        return ((final - initial)/initial) * 100
    log.exception("Missing values for final and intial.")
    raise ValueError


def calculate_zscore(past_values, current_price):
    """
    Use python statistics module to calculate the zscore.
    Which will be used to compare the current price against sample of prices
    and their variance. For example a zscore of 1 indicts the current
    price is 1 standard deviation from the sample mean.
    Formula: Z = (current_price - sample_mean) / sample_std_dev"
    """
    try:
        log.info("Calculate the Zscore to get # of std deviations current price is from mean.")
        sample_stdev = stats.stdev(data=past_values)
        log.debug("Past data stdev: %s", sample_stdev)
        sample_mean = stats.mean(data=past_values)
        zscore = (current_price - sample_mean)/sample_stdev
        log.debug("zscore of sample data: %s", zscore)
    except Exception as ex:
        log.exception("Failed to calculate standard deviation: %s", ex)
    return (zscore, sample_mean, sample_stdev)


def get_candles_url(symbol, time_range):
    return f'{GEMINI_API_BASE_URL}/{API_VERSION}/candles/{symbol}/{time_range}'


def get_tickerv2_url(symbol):
    """
    Get endpoint url for Gemini tickerv2 with symbol.
    """
    log.info("Get Gemini API tickerv2 endpoint.")
    return f'{GEMINI_API_BASE_URL}/{API_VERSION}/ticker/{symbol}'


def get_current_price(response):
    """
    Get current price string then parse as float.
    """
    log.info("Get current price from API json response.")
    if response.get('close'):
        return float(response['close'])
    log.exception("Current price cannot be None.")
    raise ValueError


def get_open_price(response):
    """
    Get open price string then parse as float.
    """
    log.info("Get open price from API json response.")
    if response.get('open'):
        return float(response['open'])
    log.exception("Open price cannot be None.")
    raise ValueError


def get_current_volume_1m_interval(response):
    """
    Type: Response is array of arrays.
    Descending order by time. The first in the array is the
    most recent entry. The end column of the row is the volume.
    """
    if response:
        past_1m = response[0]
        if past_1m:
            return past_1m[len(past_1m) - 1]
    log.exception("response cannot be empty")
    raise ValueError


def get_total_volume_past_24_hours(response):
    """
    Type: Response is array of arrays.
    Descending order by time. The first in the array is the
    most recent entry. The end column of the row is the volume.
    """
    results = []
    if response:
        past_24hours = response[0:24]
        log.debug("Past 24 hours volume: %s", past_24hours)
        if past_24hours:
            for hour in past_24hours:
                results.append(hour[len(hour) - 1])
            return stats.fsum(results)
    log.exception("response cannot be empty")
    raise ValueError


def get_hourly_past_24_hours(response):
    """
    Get current price strings then parse as floats.
    """
    prices_str= response.get('changes')
    return [float(x) for x in prices_str]


def get_price_deviation(symbol, stdev):
    """
    Get standard deviation of current price from the 24hr average.
    """
    url = get_tickerv2_url(symbol=symbol)
    try:
        log.info("Get price deviation for %s.", symbol)
        response = send_request(url=url)
        response_json = response.json()
        log.debug("Response json content: %s", response_json)
        current_price = get_current_price(response_json)
        past_prices = get_hourly_past_24_hours(response_json)
        log.debug("Current price: %s, past 24 hour prices: %s", current_price, past_prices)
        zscore, sample_mean, sample_stdev = calculate_zscore(past_values=past_prices, current_price=current_price)
        if zscore > stdev:
            log.error("Current price: %s is %s standard deviations above the mean: %s",
                      current_price, zscore, sample_mean)
        elif zscore < (stdev * -1.00):
            log.error("Current price: %s is %s standard deviations below the mean: %s",
                      current_price, zscore, sample_mean)
        else:
            log.info("""Current price (%s) is within 1 standard deivation (%s)
                        from the sample mean (%s).""",
                     current_price, sample_stdev, sample_mean)
    except Exception as ex:
        log.exception("Failed to get price deviation for: %s, message: %s",
                      symbol, ex)


def get_price_change(symbol, threshold):
    """
    Get price change of open 24 hr ago vs now.
    """
    try:
        log.info("Get price change between open and current for %s.", symbol)
        url = get_tickerv2_url(symbol=symbol)
        response = send_request(url=url)
        response_json = response.json()
        log.debug("Get price change response json: %s", response_json)

        current_price = get_current_price(response_json)
        open_price = get_open_price(response_json)
        percent_change = calculate_percentage_change(final=current_price,
                                                     initial=open_price)
        if abs(percent_change) > threshold:
            send_alert(alert_type="pricechange",
                       message=f"""Percentage change {percent_change} between current price
                                {current_price} and open price {open_price} is greater or
                                equal to threshold of {threshold}.""")
        else:
            send_info(alert_type="pricechange",
                      message=f"""Percentage change {percent_change} between current price
                               {current_price} and open price {open_price} is less than
                               threshold of {threshold}.""")
    except Exception as ex:
        log.exception("Failed to get price change for: %s, message: %s",
                      symbol, ex)


def get_volume_deviation(symbol, threshold):
    """
    Use Gemini API candles endpoint to get volume for past 24hours to get
    moving sum of volume. Then use the most recent 1miniute interval to
    use as the current volume. Use percentage change to determine if threshold
    has been execeeded.
    """
    try:
        moving_24hr_sum_url = get_candles_url(symbol=symbol, time_range='1hr')
        current_url = get_candles_url(symbol=symbol, time_range='1m')

        response = send_request(url=moving_24hr_sum_url)
        response_json = response.json()
        total_24hr_volume = get_total_volume_past_24_hours(response=response_json)

        response = send_request(url=current_url)
        response_json = response.json()
        current_volume = get_current_volume_1m_interval(response=response_json)

        percent_change = calculate_percentage_change(final=current_volume,
                                                     initial=total_24hr_volume)
        message = f"""Percentage change {percent_change} between current volume
                            {current_volume} and past 24hour total volume
                            {total_24hr_volume} threshold of {threshold}."""

        if percent_change > threshold:
            send_alert(alert_type="voldev", message=message)
        else:
            send_info(alert_type="voldev", message=message)
    except Exception as ex:
        log.exception("Failed to get volume deviation")


def validate_symbol(symbol):
    """
    Call the Gemini API for validating the symbol. Locally caches the symboles
    on disk. Updates the local cache every hour.
    """
    #TODO


def send_alert(alert_type, message):
    """
    Send alert for the alert that ran.
    """
    log.info("Sending alert.")
    if alert_type and message:
        log.error("ALERT TRIGGERED: %s, Message: %s", alert_type, message)
    else:
        log.exception("Invalid parameters alert_type, messsage")
        raise ValueError


def send_info(alert_type, message):
    """
    Send info for the alert that ran.
    """
    log.info("Sending info.")
    if alert_type and message:
        log.info("OK: %s, Message: %s", alert_type, message)
    else:
        log.exception("Invalid parameters alert_type, messsage")
        raise ValueError


@click.command()
@click.option('--currency',
              type=str,
              required=False)
@click.option('--alert_type',
              type=str,
              required=True)
@click.option('--deviation',
              type=float,
              required=True)
@click.option('--symbol',
              type=str,
              required=True)
@click.option('--debug',
              type=bool,
              required=False)
def main(currency, alert_type, deviation, symbol, debug):
    setup_logging(debug)
    log.debug("Currency: %s, type: %s, deviation: %s", currency, alert_type, deviation)
    deviation = deviation * 100
    if alert_type == "pricedev":
        get_price_deviation(symbol=symbol, stdev=1.0)
    elif alert_type == "pricechange":
        get_price_change(symbol=symbol, threshold=deviation)
    elif alert_type == "voldev":
        get_volume_deviation(symbol=symbol, threshold=deviation)
    elif alert_type == "all":
        get_price_deviation(symbol=symbol, stdev=1.0)
        get_price_change(symbol=symbol, threshold=deviation)
        get_volume_deviation(symbol=symbol, threshold=deviation)
    else:
        log.exception("""Invalid alert type value, must be pricedev,
                      pricechange, voldev, or all.""")


if __name__ == '__main__':
    main()
