import timeit
import sys

# Local imports
from analysis import (
    auto_correlation,
    correlation,
    heteroskedasticity,
    seasonality,
    stationarity,
    stochasticity,
    trend,
    volatility,
)
from experiment import train_test


def analysis():
    """
    Generates all analysis data and plots.
    """

    # Stationarity
    stationarity.stationarity_tests()

    # Autocorrelation
    auto_correlation.auto_cor_tests()

    # Trend
    trend.trend_tests()

    # Seasonality
    seasonality.seasonal_strength_test()

    # Heteroskedasticity
    heteroskedasticity.uncon_het_tests()
    heteroskedasticity.con_het_test()

    # Correlation
    correlation.correlation_tests()

    # Volatility
    volatility.volatility_tests()

    # Stochasticity
    stochasticity.calc_hurst()


def models():
    # forecast.all_forecasts("ARIMA")
    pass


if __name__ == "__main__":
    train_test.plot_periods()
